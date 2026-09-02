# Español primero · English below
# Origen: app/change_detector.py del sistema en producción (archivo completo).
# Ilustra: el cliente edita su Google Sheet a mano y el sistema tiene que
# enterarse. En vez de confiar en un webhook, se detecta el cambio contra el
# último estado conocido — la misma desconfianza que en la verificación de
# agenda, aplicada a otra integración.
#
# --- English ---
# Source: app/change_detector.py from the production system (full file).
# Shows: the client edits their Google Sheet by hand and the system has to notice.
# Instead of trusting a webhook, the change is detected against the last known
# state — the same distrust as in the booking verification, applied to another
# integration.

"""
Detector de cambios en el sheet del cliente.

OBJETIVO:
  Cada hora, comparar los leads en memoria con las filas presentes en el
  sheet del cliente. Si el cliente eliminó un lead de SU sheet, el bot:
    1. Cambia el status a "desinteresado" (deja de hacer follow-ups)
    2. Pinta la fila de ese lead en ROJO dentro del sheet del bot
    3. NO re-inserta al lead en el sheet del cliente (evita resucitarlo)

El admin (única persona con acceso al sheet del bot) revisa las filas
rojas y decide manualmente si las borra o las restaura.

PROTECCIONES:
  - Solo procesa leads con más de 30 minutos de antigüedad (evita falsos
    positivos por race condition con la escritura fire-and-forget).
  - Solo procesa leads con status != "desinteresado" / "frio".
  - Si el sheet del cliente no está accesible, no hace nada (silencioso).
"""
import os
import time
from datetime import datetime


# Buffer mínimo desde el primer contacto para considerar a un lead
# "ya sincronizado" con el sheet del cliente (evita marcar como borrado
# leads que recién se crearon y todavía no fueron escritos).
_FRESH_LEAD_MIN_SECONDS = 30 * 60   # 30 min


def _parse_fecha_primer_contacto(fecha_str: str | None) -> float | None:
    """Devuelve el timestamp (epoch) del primer contacto, o None si no se puede parsear."""
    if not fecha_str:
        return None
    try:
        dt = datetime.strptime(fecha_str, "%d/%m/%Y %H:%M")
        return dt.timestamp()
    except Exception:
        return None


async def _get_client_sheet_keys() -> set[str] | None:
    """
    Lee la columna B del sheet del cliente y devuelve un set con todas las
    claves de lead presentes. Devuelve None si el sheet no está configurado
    o no se pudo leer (en cuyo caso NO se ejecuta la detección, por seguridad).
    """
    from .client_sheets import CLIENT_SPREADSHEET_ID, _CLIENT_TAB
    from .sheets import _get_service

    if not CLIENT_SPREADSHEET_ID:
        return None

    service = _get_service()
    if not service:
        return None

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=CLIENT_SPREADSHEET_ID,
            range=f"'{_CLIENT_TAB}'!B:B",
        ).execute()
        values = result.get("values", [])
        # Devolver set de strings non-vacíos (saltea header rows vacíos)
        return {str(row[0]).strip() for row in values if row and str(row[0]).strip()}
    except Exception as e:
        print(f"[ChangeDetector] No se pudo leer client sheet col B: {e}")
        return None


async def check_client_deletions() -> None:
    """
    Job principal. Detecta leads borrados del sheet del cliente y los marca
    como 'desinteresado' + pinta su fila roja en el sheet del bot.

    Se invoca desde el scheduler de rules.py cada hora.
    """
    from .state import _leads
    from .client_sheets import _get_lead_key
    from .sheets import mark_row_red
    from .database import upsert_lead, is_available as db_available

    client_keys = await _get_client_sheet_keys()
    if client_keys is None:
        # Sheet no configurado o no accesible — saltar silenciosamente
        return

    ahora = time.time()
    marcados = 0
    saltados = 0

    for lead in list(_leads.values()):
        # 1) Skip leads ya inactivos
        if lead.status in ("desinteresado", "frio"):
            continue

        # 2) Skip leads demasiado nuevos (puede que aún no se haya escrito en client sheet)
        primer_ts = _parse_fecha_primer_contacto(lead.fecha_primer_contacto)
        if primer_ts is None:
            # Sin fecha de primer contacto → usar created_at como proxy
            # Si tampoco existe, usar last_seen como último fallback
            primer_ts = getattr(lead, "last_seen", ahora)
        if (ahora - primer_ts) < _FRESH_LEAD_MIN_SECONDS:
            saltados += 1
            continue

        # 3) Calcular la client_key esperada para este lead
        client_key = _get_lead_key(lead)
        if not client_key:
            continue

        # 4) ¿Existe en el client sheet?
        if client_key in client_keys:
            continue   # OK, el cliente lo sigue teniendo

        # 5) NO está → el cliente lo borró. Marcar como desinteresado + fila roja.
        try:
            lead.status = "desinteresado"
            ts = datetime.now().strftime("%d/%m/%Y %H:%M")
            lead.historial_setter.append({
                "accion":    "borrado por cliente",
                "setter":    "client-sheet",
                "timestamp": ts,
                "datos":     {"client_key": client_key},
            })

            ok = await mark_row_red(lead.account_id, lead.user_id)
            if ok:
                marcados += 1

            # Persistir en DB para que sobreviva al reinicio
            if db_available():
                await upsert_lead(lead)
        except Exception as e:
            print(f"[ChangeDetector] Error procesando {lead.user_id}: {e}")

    if marcados or saltados:
        print(
            f"[ChangeDetector] {marcados} lead(s) marcados como borrados | "
            f"{saltados} salteados por ser muy recientes"
        )
