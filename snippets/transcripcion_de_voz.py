# Español primero · English below
# Origen: app/transcriber.py del sistema en producción (archivo completo).
# Ilustra: la transcripción de notas de voz ocurre ANTES del motor de reglas,
# así el resto del sistema nunca sabe que el mensaje entró como audio.
#
# --- English ---
# Source: app/transcriber.py from the production system (full file).
# Shows: voice-note transcription happens BEFORE the rule engine, so the rest of
# the system never knows the message came in as audio.
"""
Transcripción de audio vía Groq Whisper.

Flujo:
  1. Descarga el audio desde la URL de Meta (CDN firmado, no requiere token)
  2. Lo envía a Groq Whisper (whisper-large-v3-turbo, español)
  3. Devuelve el texto transcripto o None si falla

Formatos soportados por Instagram: ogg, m4a, mp4, webm
Formatos soportados por Groq: mp3, mp4, mpeg, m4a, wav, webm, ogg, flac

CONFIGURACIÓN:
  GROQ_API_KEY → en .env y en Render como variable de entorno
"""
import os
import httpx

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL     = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL   = "whisper-large-v3-turbo"

# Tamaño máximo de audio a procesar (25 MB — límite de Groq)
MAX_AUDIO_BYTES = 25 * 1024 * 1024


def is_available() -> bool:
    """True si GROQ_API_KEY está configurada."""
    return bool(GROQ_API_KEY)


async def transcribir_desde_url(audio_url: str, account_id: str = "DiegoFerrari") -> str | None:
    """
    Descarga el audio desde la URL de Meta y lo transcribe con Groq Whisper.

    Devuelve el texto transcripto, o None si:
      - GROQ_API_KEY no está configurada
      - La descarga falla
      - Groq devuelve error
      - La transcripción queda vacía (ruido, silencio)
    """
    if not GROQ_API_KEY:
        print("[Audio] GROQ_API_KEY no configurada — transcripción desactivada")
        return None

    audio_bytes = await _descargar_audio(audio_url)
    if not audio_bytes:
        return None

    return await _transcribir(audio_bytes)


async def _descargar_audio(url: str) -> bytes | None:
    """
    Descarga el audio desde la URL firmada de Meta.
    Las URLs de media de Instagram son CDN firmadas — no necesitan token.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code == 200:
                content = r.content
                if len(content) > MAX_AUDIO_BYTES:
                    print(f"[Audio] Archivo muy grande ({len(content)//1024}KB) — ignorado")
                    return None
                print(f"[Audio] Descargado: {len(content)//1024}KB")
                return content
            print(f"[Audio] Error descargando audio: HTTP {r.status_code}")
    except Exception as e:
        print(f"[Audio] Error de red al descargar: {e}")
    return None


async def _transcribir(audio_bytes: bytes) -> str | None:
    """
    Envía el audio a Groq Whisper y devuelve el texto.
    Usa response_format=text para respuesta directa sin parsear JSON.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files={"file": ("audio.ogg", audio_bytes, "audio/ogg")},
                data={
                    "model":           GROQ_MODEL,
                    "language":        "es",
                    "response_format": "text",
                },
            )

            if r.status_code == 200:
                texto = r.text.strip()
                # Descartar transcripciones vacías o solo ruido
                if len(texto) < 3:
                    print(f"[Audio] Transcripción vacía o muy corta: '{texto}'")
                    return None
                print(f"[Audio] Transcripto: {texto[:120]}{'...' if len(texto)>120 else ''}")
                return texto

            print(f"[Audio] Groq error {r.status_code}: {r.text[:300]}")

    except Exception as e:
        print(f"[Audio] Error llamando a Groq: {e}")

    return None