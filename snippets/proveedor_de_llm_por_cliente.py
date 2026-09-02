# Español primero · English below
# Origen: app/llm.py del sistema en producción (fragmento: docstring del
# módulo y resolver_llm_config; se recortaron call_llm, call_llm_tool y los
# constructores de cliente HTTP).
# Ilustra: cada cuenta puede correr con un proveedor distinto — el proveedor
# se deduce del prefijo de la API key del cliente (sk-ant- → Anthropic, el
# resto → OpenAI). Permitió mover una cuenta a un modelo más barato sin
# tocar el código ni afectar a las demás.
#
# --- English ---
# Source: app/llm.py from the production system (fragment: module docstring and
# resolver_llm_config; call_llm, call_llm_tool and the HTTP client builders were
# trimmed).
# Shows: each account can run on a different provider — it's inferred from the
# prefix of the client's API key (sk-ant- -> Anthropic, otherwise -> OpenAI). It
# let one account move to a cheaper model without touching code or affecting the rest.

"""
Abstracción de proveedor LLM.

Controlado por env var GLOBAL (default por defecto si no hay override por cliente):
  LLM_PROVIDER      = "openai" (default) | "anthropic"
  OPENAI_API_KEY    / OPENAI_MODEL     (default: gpt-4o-mini)
  ANTHROPIC_API_KEY / ANTHROPIC_MODEL  (default: claude-sonnet-4-5)

PER-CLIENT (multi-tenancy SaaS) — CONVENCIÓN NUEVA (preferida):
Una sola API key por cliente. El provider se DETECTA por el prefijo de la key
(sk-ant- → anthropic, resto → openai). El modelo sale del env GLOBAL del provider.
  API_KEY_<CLIENT_ID_UPPER>  = <key del cliente>   (ej. API_KEY_MARTIN_OCAMPO)
  ANTHROPIC_MODEL            = <modelo si la key es anthropic>  (ej. claude-haiku-4-5-20251001)
  OPENAI_MODEL               = <modelo si la key es openai>     (ej. gpt-5.4-mini)

Ejemplos:
  API_KEY_DIEGO_FERRARI=sk-proj-...       → openai   → usa OPENAI_MODEL
  API_KEY_MARTIN_OCAMPO=sk-ant-...     → anthropic → usa ANTHROPIC_MODEL (haiku)

FALLBACK (convención vieja, sigue funcionando si no hay API_KEY_<C>):
  LLM_PROVIDER_<C> + OPENAI_API_KEY_<C>/ANTHROPIC_API_KEY_<C> + *_MODEL_<C>.
Sin nada per-cliente → provider global (LLM_PROVIDER).
"""
import os

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# ── Clientes lazy GLOBALES — para el provider default ───────────────────────
_oai_client = None
_ant_client = None

# ── Clientes lazy POR CLIENT_ID — cache de instancias OpenAI/Anthropic ──────
_oai_clients_per_client: dict[str, object] = {}
_ant_clients_per_client: dict[str, object] = {}


def _oai():
    global _oai_client
    if _oai_client is None:
        from openai import AsyncOpenAI
        _oai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _oai_client


def _ant():
    global _ant_client
    if _ant_client is None:
        from anthropic import AsyncAnthropic
        _ant_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _ant_client


def resolver_llm_config(client_id: str | None) -> dict:
    """
    Devuelve la configuración LLM para un client_id específico.
    Si client_id es None o no tiene overrides, usa los defaults globales.

    Returns: {provider, model, api_key}
    """
    if not client_id:
        return {
            "provider": LLM_PROVIDER,
            "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5") if LLM_PROVIDER == "anthropic" else os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "api_key": os.getenv("ANTHROPIC_API_KEY") if LLM_PROVIDER == "anthropic" else os.getenv("OPENAI_API_KEY"),
        }
    up = client_id.upper()
    # ── Convención nueva (preferida): API_KEY_<CLIENT_ID> ──
    # Una sola key por cliente; el provider se DETECTA por el prefijo de la key
    # (sk-ant- → anthropic, resto → openai). El modelo sale del env GLOBAL del
    # provider detectado (ANTHROPIC_MODEL / OPENAI_MODEL).
    api_key = os.getenv(f"API_KEY_{up}", "")
    if api_key:
        if api_key.startswith("sk-ant-"):
            return {
                "provider": "anthropic",
                "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
                "api_key": api_key,
            }
        return {
            "provider": "openai",
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "api_key": api_key,
        }
    # ── Fallback: convención vieja LLM_PROVIDER_<C> + OPENAI/ANTHROPIC_API_KEY_<C> ──
    # AISLAMIENTO DE BILLING: la API key es SOLO per-cliente. NUNCA se cae a la key
    # global (ANTHROPIC_API_KEY / OPENAI_API_KEY) — eso facturaría el tráfico de un
    # cliente a la cuenta del dueño de la global. Sin key propia → api_key="" → el
    # cliente NO responde (lo frena cliente_listo_para_responder). El modelo sí puede
    # tomar el default global (no afecta a quién se factura, solo qué modelo se usa).
    provider = os.getenv(f"LLM_PROVIDER_{up}", LLM_PROVIDER)
    if provider == "anthropic":
        return {
            "provider": "anthropic",
            "model": os.getenv(f"ANTHROPIC_MODEL_{up}", os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")),
            "api_key": os.getenv(f"ANTHROPIC_API_KEY_{up}", ""),
        }
    return {
        "provider": "openai",
        "model": os.getenv(f"OPENAI_MODEL_{up}", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
        "api_key": os.getenv(f"OPENAI_API_KEY_{up}", ""),
    }
