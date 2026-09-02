# Español primero · English below
# Origen: app/scoring.py del sistema en producción (archivo completo).
# Ilustra: el score de calificación usa reglas fijas, sin IA ni tokens extra:
# se recalcula tras cada mensaje y el esquema de puntos cambia según el nicho
# del lead (deportivo vs. no deportivo) de forma determinística.
#
# --- English ---
# Source: app/scoring.py from the production system (full file).
# Shows: the qualification score uses fixed rules, no AI and no extra tokens: it's
# recomputed after each message and the point scheme changes with the lead's niche
# (sports vs. non-sports) deterministically.
"""
Cálculo del score de calificación del lead (1-10).

Reglas fijas — sin IA, sin tokens extra.
Se recalcula después de cada mensaje del lead.

Hay un esquema de puntos por nicho (ver `_es_nicho_deportivo`):
  - Deportivo (CLIENTES_NICHO_DEPORTIVO): deporte_club +2 y categoria +1.
  - No deportivo (Martín, Estancia La Rosada): esos campos no existen en su flujo;
    los 3 puntos se redistribuyen en pain_point (+5) y nombre (+2).
Ambos esquemas clamps a 1-10 y su techo es 10.

Escala:
  8-10 → 🟢 Calificado — listo para el link
  5-7  → 🟡 En proceso — sigue la conversación
  1-4  → 🔴 No calificado — falta info clave
"""


def _es_nicho_deportivo(lead) -> bool:
    """True si al lead le aplican los campos de calificación deportiva.

    Fail-open hacia el camino histórico (deportivo): si el import falla, se puntúa
    como siempre. Acá el riesgo de equivocarse es cosmético —un número en el panel—,
    al revés que en los filtros de descarte, donde un fallo pierde un lead.
    """
    try:
        from .main import CLIENTES_NICHO_DEPORTIVO
        return getattr(lead, "client_id", "diego_ferrari") in CLIENTES_NICHO_DEPORTIVO
    except Exception:
        return True


def calcular_score(lead) -> int:
    """
    Devuelve un entero entre 1 y 10.
    Nunca devuelve 0 — el mínimo es 1 para distinguir "calculado" de "sin datos".

    El lead trae `client_id` (así lo pasan los call sites de agent.py); el esquema
    de puntos lo decide `_es_nicho_deportivo`. Sin `client_id` se usa el histórico.
    """
    deportivo = _es_nicho_deportivo(lead)

    score = 0

    # ── Datos de calificación (hasta 9 puntos) ───────────────────────────────
    if getattr(lead, "pain_point", None):
        score += 3 if deportivo else 5   # el más importante — sin pain point no hay venta

    if deportivo and getattr(lead, "deporte_club", None):
        score += 2   # confirma que es atleta real

    if deportivo and getattr(lead, "categoria", None):
        score += 1   # nivel competitivo

    if getattr(lead, "meta_ingreso", None):
        score += 1   # tiene objetivo concreto

    if getattr(lead, "edad", None):
        score += 1   # dato demográfico básico

    if getattr(lead, "nombre", None):
        score += 1 if deportivo else 2   # mínimo de engagement

    # ── Temperatura (hasta 2 puntos extra) ───────────────────────────────────
    temp = getattr(lead, "temperatura_label", None) or ""
    if temp == "caliente":
        score += 2
    elif temp == "tibio":
        score += 1

    # ── Clamp al rango 1-10 ──────────────────────────────────────────────────
    return max(1, min(10, score))


def score_label(score: int) -> str:
    """Devuelve emoji + texto para mostrar en panel/logs."""
    if score >= 8:
        return f"🟢 {score}"
    elif score >= 5:
        return f"🟡 {score}"
    else:
        return f"🔴 {score}"