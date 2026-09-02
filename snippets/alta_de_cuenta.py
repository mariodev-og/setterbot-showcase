# Español primero · English below
# Origen: app/onboarding.py del sistema en producción (archivo completo).
# Ilustra: el alta de una cuenta nueva genera su system_prompt y lo persiste,
# sin tocar código ni desplegar. Es lo que hace que multi-tenant signifique
# algo: la cuenta tres se dio de alta igual que la uno.
#
# --- English ---
# Source: app/onboarding.py from the production system (full file).
# Shows: onboarding a new account generates its system_prompt and persists it,
# without touching code or deploying. That's what makes multi-tenant mean
# something: account three was onboarded the same way as account one.

"""
onboarding.py — Alta de clientes: generador de system_prompt + persistencia en DB.

El generador arma un borrador de system_prompt desde un template base, rellenando
nicho, tono, nombre del vendedor y las preguntas de calificación. El admin lo edita
antes de guardar (flujo híbrido). NO maneja credenciales.
"""
from typing import Optional


def generar_system_prompt(
    name: str,
    nombre_comercial: str,
    nicho: str,
    tono: str,
    preguntas: list[str],
) -> str:
    """Devuelve un borrador de system_prompt. Placeholders activos que el runtime
    rellena ({lead_summary}, {booking_url}, {vsl_url}) se dejan SIN escapar (van con una
    sola llave) porque agent.py los resuelve con .format()."""
    preguntas_fmt = "\n".join(f"  - {p}" for p in preguntas if p.strip())
    if not preguntas_fmt:
        preguntas_fmt = "  - (sin preguntas de calificación definidas)"
    return f"""Sos {name}, del equipo de {nombre_comercial}.
Atendés por Instagram a personas interesadas en {nicho}.

TONO: {tono}. Hablás natural, cercano, sin sonar robot ni vendedor agresivo.

OBJETIVO: calificar al lead y, si corresponde, mandarle el link de agenda.

PREGUNTAS DE CALIFICACIÓN (hacelas de a una, natural, no como interrogatorio):
{preguntas_fmt}

REGLAS:
- Una pregunta por mensaje. Esperá la respuesta antes de la siguiente.
- No menciones precios. No prometas resultados garantizados.
- Cuando el lead esté calificado y muestre interés, ofrecé el link: {{booking_url}}
- Si pregunta por el video/recurso, mandá: {{vsl_url}}

CONTEXTO DEL LEAD:
{{lead_summary}}
"""


async def guardar_cliente_onboarding(cfg: dict) -> dict:
    """
    cfg: {client_id, account_id, nombre_comercial, email, nicho, tono, name, system_prompt}
    Inserta clients + client_personalities + seed account_config. Recarga PERSONALITIES en memoria.
    Devuelve {ok, account_id, client_id}.
    """
    from .database import control_pool, control_available as db_ok
    if not db_ok():
        return {"ok": False, "error": "DB no disponible"}
    async with control_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO clients (client_id, nombre_comercial, email_contacto, estado, account_id) "
                "VALUES ($1, $2, $3, 'activo', $4) ON CONFLICT (client_id) DO NOTHING",
                cfg["client_id"], cfg["nombre_comercial"], cfg.get("email", ""), cfg["account_id"],
            )
            await conn.execute(
                "INSERT INTO client_personalities (account_id, client_id, nombre_comercial, nicho, tono, name, system_prompt) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7) "
                "ON CONFLICT (account_id) DO UPDATE SET system_prompt = $7, nicho = $4, tono = $5, name = $6, updated_at = NOW()",
                cfg["account_id"], cfg["client_id"], cfg["nombre_comercial"],
                cfg.get("nicho", ""), cfg.get("tono", ""), cfg.get("name", ""), cfg["system_prompt"],
            )
            for clave in ("booking_url", "vsl_url"):
                await conn.execute(
                    "INSERT INTO account_config (client_id, clave, valor) VALUES ($1, $2, '') "
                    "ON CONFLICT (client_id, clave) DO NOTHING",
                    cfg["client_id"], clave,
                )
    # Recarga en memoria (sin reinicio)
    await cargar_personalidades_db()
    from . import state
    await state.warm_clients_cache()
    return {"ok": True, "account_id": cfg["account_id"], "client_id": cfg["client_id"]}


async def cargar_personalidades_db() -> int:
    """Mergea client_personalities (DB) a PERSONALITIES en memoria. Devuelve cantidad cargada.
    Toma como base la personalidad de DiegoFerrari para heredar placeholders/estructura runtime,
    y le pisa system_prompt + name. Así el nuevo cliente usa el mismo pipeline (CORE_RULES, format)."""
    from .database import control_pool, control_available as db_ok
    from . import personalities as P
    if not db_ok():
        return 0
    async with control_pool().acquire() as conn:
        rows = await conn.fetch("SELECT account_id, name, system_prompt FROM client_personalities")
    base = P.PERSONALITIES.get("DiegoFerrari", {})
    n = 0
    _saltadas = []
    for r in rows:
        aid = r["account_id"]
        # Las personalidades que viven en personalities.py NO se pisan con la DB.
        # La fila de Diego se seedeó una vez con ON CONFLICT DO NOTHING y quedó
        # congelada; pisando el prompt en cada arranque, ningún cambio al código
        # llegaba a producción. Ver PERSONALIDADES_EN_CODIGO.
        if aid in P.PERSONALIDADES_EN_CODIGO:
            _saltadas.append(aid)
            continue
        if aid in P.PERSONALITIES:
            P.PERSONALITIES[aid]["system_prompt"] = r["system_prompt"]
            if r["name"]:
                P.PERSONALITIES[aid]["name"] = r["name"]
        else:
            nueva = dict(base)
            nueva["name"] = r["name"] or "Asistente"
            nueva["system_prompt"] = r["system_prompt"]
            nueva["booking_url"] = ""
            nueva["vsl_url"] = ""
            P.PERSONALITIES[aid] = nueva
        n += 1
    # Se loguean SIEMPRE las dos cosas: cuántas vinieron de la DB y cuáles se
    # ignoraron por vivir en código. Sin esta línea, que el prompt de producción no
    # fuera el del repo era invisible en los logs.
    if n:
        print(f"[Onboarding] {n} personalidad(es) cargada(s) desde DB")
    if _saltadas:
        print(f"[Onboarding] personalidad desde CÓDIGO (fila de DB ignorada): {', '.join(_saltadas)}")
    return n
