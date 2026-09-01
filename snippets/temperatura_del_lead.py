# Origen: app/temperature.py del sistema en producción (archivo completo).
# Ilustra: la temperatura del lead la evalúa el LLM sobre el historial de la
# conversación, pero con un vocabulario cerrado (4 palabras) y validación del
# output: el resultado inválido cae a un fallback en vez de romper el flujo.
"""
Evaluación de temperatura del lead.
Claude analiza el historial y decide si el lead es frío, tibio o caliente.

TEMPERATURAS:
  caliente → pasa al closer (verde)
  tibio    → en proceso, tiene potencial (amarillo)
  frio     → sin intención real (gris)

COLORES (fill hex sin #):
  caliente: C6EFCE  (verde claro)
  tibio:    FFEB9C  (amarillo claro)
  frio:     D9D9D9  (gris claro)
  manual:   no tocar — el bot respeta cualquier color puesto a mano
"""

import os
from .llm import call_llm

TEMPERATURE_COLORS = {
    "caliente":      "C6EFCE",   # verde claro
    "tibio":         "FFEB9C",   # amarillo claro
    "frio":          "D9D9D9",   # gris claro
    "desinteresado": "F4CCCC",   # rojo claro — sin potencial real
}

TEMPERATURE_LABELS = {
    "caliente":      "🟢 Caliente — pasa al closer",
    "tibio":         "🟡 Tibio — en proceso",
    "frio":          "⚪ Frío — se enfrió",
    "desinteresado": "🔴 Desinteresado — sin potencial",
}

# Colores que el bot pone automáticamente — cualquier otro se considera manual
BOT_COLORS = set(TEMPERATURE_COLORS.values())


async def evaluar_temperatura(historial: list, lead_summary: str, client_id: str | None = None) -> str:
    """
    Le pide a Claude que evalúe la temperatura del lead
    basándose en el historial de la conversación.
    Devuelve: "caliente" | "tibio" | "frio"
    """
    if not historial:
        return "frio"

    historial_texto = "\n".join([
        f"{'Prospecto' if m['role'] == 'user' else 'Setter'}: {m['content']}"
        for m in historial[-20:]  # últimos 20 mensajes
    ])

    prompt = f"""Analizá esta conversación de ventas y evaluá la temperatura del lead.

DATOS DEL LEAD:
{lead_summary}

CONVERSACIÓN:
{historial_texto}

CRITERIOS:
- CALIENTE: mostró urgencia, pidió precio o agenda, habló de fechas concretas, reveló pain point fuerte con disposición a actuar
- TIBIO: respondió bien, dio información, hay interés pero sin urgencia, no rechazó pero tampoco avanzó activamente
- FRÍO: estuvo activo pero se enfrió — monosílabos, evasivo, dijo que no es el momento, depende de terceros
- DESINTERESADO: nunca mostró interés real — respuestas vacías o automáticas, no reveló ningún pain point, conversación completamente unidireccional, claramente no es el target

Respondé ÚNICAMENTE con una de estas cuatro palabras exactas: caliente | tibio | frio | desinteresado"""

    resultado, _ = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        client_id=client_id,
    )
    resultado = resultado.lower().strip()

    if resultado not in TEMPERATURE_COLORS:
        print(f"[Temperatura] Output inválido '{resultado}' → fallback 'tibio'")
        return "tibio"

    # Auditoría: log decisión + sample de los últimos 5 mensajes del lead
    _ultimos_lead = [
        m.get("content", "")[:120]
        for m in historial[-10:] if m.get("role") == "user"
    ][-5:]
    _sample = " | ".join(_ultimos_lead)
    print(f"[Temperatura] decisión='{resultado}' | últimos_lead='{_sample}'")

    return resultado


def color_es_manual(hex_color: str) -> bool:
    """
    Devuelve True si el color fue puesto manualmente por el usuario.
    El bot solo reconoce sus propios 3 colores — cualquier otro es manual.
    """
    if not hex_color:
        return False
    # Normalizar (openpyxl a veces incluye FF de alpha al inicio)
    color_limpio = hex_color.upper().lstrip("FF") if len(hex_color) == 8 else hex_color.upper()
    return color_limpio not in {c.upper() for c in BOT_COLORS}