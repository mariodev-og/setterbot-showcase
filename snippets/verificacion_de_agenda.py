# Español primero · English below
# Origen: app/agenda_verificacion.py del sistema en producción (fragmento).
# Ilustra: no se confía en el webhook de Cal.com — hay una verificación posterior
# de que la reserva realmente ocurrió, hecha por un humano, antes de cerrar el
# flujo. El lead queda 'agendado_no_verificado' hasta que alguien la confirma.
# Se recortó: marcar_falso_positivo() y la sección de comprobantes de seña
# (listar_comprobantes_pendientes, confirmar_comprobante). Los módulos .state,
# .sender, .sheets, .database y .agent se referencian por lazy import y no se
# incluyen: quedan como estaban, el snippet es para leer, no para correr.
#
# --- English ---
# Source: app/agenda_verificacion.py from the production system (fragment).
# Shows: the Cal.com webhook is not trusted — there is a later human verification
# that the booking actually happened, before closing the flow. The lead stays
# 'booked_unverified' until someone confirms it.
# Trimmed: marcar_falso_positivo() and the deposit-receipt section. The .state,
# .sender, .sheets, .database and .agent modules are referenced by lazy import and
# not included: the snippet is to read, not to run.
"""
Lógica de verificación manual de agendas.

Cuando el bot no puede verificar contra la API de Cal.com (sin match) y tampoco
con el nombre que dio el lead, el booking queda en estado 'agendado_no_verificado'
y el equipo decide manualmente vía panel /admin (sección Verificaciones pendientes):
  - confirmar_verificacion() → reserva real, continúa flujo post-agenda
  - marcar_falso_positivo()  → el lead mintió/se confundió, vuelve a link_enviado
"""
import time
from typing import Optional


def listar_pendientes(client_id: str | None = None) -> list[dict]:
    """
    Leads pendientes de verificación de agenda. Para la UI del admin.

    `client_id` NO es opcional en la práctica: sin él devuelve los pendientes de
    TODOS los clientes, y esa era la fuga — el panel de Martín y el de Estancia
    La Rosada mostraban un lead de Diego (07/08). Cada cuenta ve lo suyo y nada
    más. Se deja con default None solo para usos internos que ya agregan el
    account_id (como el aviso de Telegram, que lo dice en el texto).
    """
    from .state import _leads
    out = []
    for lead in _leads.values():
        if lead.status != "agendado_no_verificado":
            continue
        if (lead.agenda_verif_estado or "") != "no_verificado_pendiente":
            continue
        if client_id and getattr(lead, "client_id", "") != client_id:
            continue
        out.append({
            "user_id":      lead.user_id,
            "account_id":   lead.account_id,
            "nombre":       (lead.nombre or "") + (" " + lead.apellido if lead.apellido else ""),
            "ig_perfil":    lead.ig_perfil or "",
            "nombre_dado":  lead.agenda_verif_nombre_dado or "",
            "ts":           lead.agenda_verif_ts or 0,
            "hora_legible": _hora_relativa(lead.agenda_verif_ts),
            "ultimo_msg_lead": _ultimo_msg_lead(lead),
        })
    # Más recientes primero
    out.sort(key=lambda x: x["ts"], reverse=True)
    return out


def _hora_relativa(ts: Optional[float]) -> str:
    if not ts:
        return ""
    delta_seg = int(time.time() - ts)
    if delta_seg < 60:
        return f"hace {delta_seg}s"
    if delta_seg < 3600:
        return f"hace {delta_seg // 60} min"
    if delta_seg < 86400:
        return f"hace {delta_seg // 3600} h"
    return f"hace {delta_seg // 86400} d"


def _ultimo_msg_lead(lead) -> str:
    """Último mensaje del usuario en el historial."""
    for entry in reversed(lead.history or []):
        if entry.get("role") == "user":
            txt = entry.get("content", "") or ""
            return txt[:150]
    return ""


async def confirmar_verificacion(unique_id: str) -> tuple[bool, str]:
    """
    Marca el lead como agendado VERIFICADO manualmente por el equipo.
    Bot manda mensaje de continuación post-agenda.
    Devuelve (ok, mensaje).
    """
    from .state import _leads
    from .sender import send_message

    lead = _leads.get(unique_id)
    if not lead:
        return False, f"lead {unique_id} no existe en memoria"
    if lead.status != "agendado_no_verificado":
        return False, f"lead status='{lead.status}' (esperaba 'agendado_no_verificado')"

    lead.status               = "agendado"
    lead.estado_llamada       = "pendiente"
    lead.agenda_verif_estado  = None
    if not getattr(lead, "agendado_ts", None):
        lead.agendado_ts = time.time()

    # Mensaje al lead — confirmación + arrancar engagement post-agenda
    msg = "ahi confirmamos tu reserva | pudiste ver el video post-agenda??"
    try:
        partes = [p.strip() for p in msg.split(" | ")]
        for i, p in enumerate(partes):
            await send_message(lead.user_id, p, lead.platform, lead.account_id)
            if i < len(partes) - 1:
                import asyncio
                await asyncio.sleep(1.2)
        lead.history.append({"role": "assistant", "content": msg})
        lead.ultimo_msg_bot_ts = time.time()
        lead.pregunta_1_enviada = True
    except Exception as e:
        print(f"[AgendaVerif] error enviando msg de confirmación: {e}")

    # Persistir
    try:
        from .sheets import save_lead
        await save_lead(lead)
    except Exception as e:
        print(f"[AgendaVerif] error guardando en sheets: {e}")
    try:
        from .database import upsert_lead, is_available as db_ok
        if db_ok():
            await upsert_lead(lead)
    except Exception as e:
        print(f"[AgendaVerif] error guardando en DB: {e}")

    # Flujo PADRES: audio post-agenda del hijo (additivo, 1×/lead). El helper filtra
    # audiencia_ad != "padres" y el guard audio_postagenda_hijo evita duplicados.
    try:
        import asyncio
        from .agent import enviar_postagenda_hijo
        asyncio.create_task(enviar_postagenda_hijo(lead))
    except Exception as e:
        print(f"[AgendaVerif] error agendando postAgendaHijo: {e}")

    print(f"[AgendaVerif] ✅ {unique_id} confirmado manualmente → agendado")
    return True, "Reserva verificada — bot continuó flujo post-agenda"