**🇦🇷 Español · 🇬🇧 [English](#-english)**

# Mapa de módulos

El sistema en producción tiene **35 módulos** en `app/`. Esta tabla los lista
todos con su tamaño real y marca cuáles están publicados en este repositorio.

Sirve para dos cosas: mostrar la forma y la escala del sistema completo, y dejar
explícito que lo publicado es una selección deliberada y no todo lo que hay.

| Módulo | Líneas | Qué hace | En este repo |
|---|---:|---|---|
| `agent.py` | 5814 | Orquestador de la conversación | privado |
| `admin.py` | 8367 | Panel de administración (76 endpoints) | privado |
| `personalities.py` | 2431 | Personalidad por cuenta, construida con conversaciones del cliente | privado |
| `telegram_bot.py` | 2326 | Control interactivo por Telegram con teclados inline | privado |
| `main.py` | 1921 | Entrada FastAPI y webhooks | privado |
| `rules.py` | 1855 | Motor de reglas proactivas y follow-ups automáticos | privado |
| `database.py` | 1461 | Persistencia PostgreSQL, fuente de verdad del estado del lead | privado |
| `saas_owner_crm.py` | 1022 | CRM interno del dueño del SaaS | privado |
| `notifications.py` | 788 | Aviso al equipo humano cuando se agenda una llamada | privado |
| `meta_insights.py` | 773 | Métricas de Meta | privado |
| `sheets.py` | 767 | Integración con Google Sheets | privado |
| `closer_sheet.py` | 589 | Sincronización del registro de llamadas del closer | privado |
| `client_sheets.py` | 530 | Escritor del Sheet que ve el cliente | privado |
| `monitoring.py` | 481 | Monitoreo del sistema en tiempo real | privado |
| `state.py` | 480 | Estado de cada lead en memoria | privado |
| `sender.py` | 411 | Envío de mensajes (Instagram y WhatsApp) | privado |
| `questions.py` | 365 | Preguntas de calificación con variaciones naturales | privado |
| `preflight.py` | 351 | Autodiagnóstico de configuración por cliente | privado |
| `filters.py` | 347 | Filtros y palabras gatillo que silencian al bot | privado |
| `calcom_api.py` | 338 | Cliente de la API de Cal.com | privado |
| **`llm.py`** | 310 | Abstracción de proveedor LLM, resuelta por cliente | **fragmento publicado** |
| `casos_exito.py` | 280 | Videos de caso según el dolor detectado en el lead | privado |
| **`agenda_verificacion.py`** | 264 | Verificación manual de que la reserva ocurrió | **fragmento publicado** |
| `status_vivo.py` | 252 | Estado del sistema en vivo | privado |
| `config_store.py` | 171 | Configuración operativa por cliente, cacheada | privado |
| `fx.py` | 155 | Cotización USD/ARS | privado |
| **`change_detector.py`** | 141 | Detector de cambios en el Sheet del cliente | **publicado** |
| **`onboarding.py`** | 122 | Alta de cliente: genera el system prompt y lo persiste | **publicado** |
| `logbuffer.py` | 113 | Buffer circular de los últimos logs, en memoria | privado |
| `mailer.py` | 111 | Punto único de salida de mails | privado |
| **`transcriber.py`** | 105 | Transcripción de audio con Whisper (Groq) | **publicado** |
| **`core_rules.py`** | 104 | Reglas universales que toda cuenta del SaaS cumple | **publicado** |
| **`temperature.py`** | 99 | Evaluación de temperatura del lead | **publicado** |
| **`scoring.py`** | 83 | Cálculo del score de calificación (1-10) | **publicado** |
| `http_client.py` | 43 | Cliente httpx compartido | privado |

**Publicados:** 8 de 35 módulos — 6 completos y 2 en fragmento.

## Por qué esta selección

Los módulos publicados son los que **se leen de un vistazo y muestran una
decisión**. Los que quedan afuera lo hacen por dos motivos distintos, y conviene
no mezclarlos:

- **Por tamaño.** `agent.py` (5814 líneas) y `admin.py` (8367) son los dos
  archivos más grandes del sistema. Ninguno aporta a quien evalúa en cinco
  minutos, y los dos muestran deuda técnica sin el contexto de por qué se llegó
  ahí. Ese contexto está en las decisiones del README.
- **Por contenido de cliente.** `personalities.py` está construido con
  transcripciones reales de conversaciones del cliente. No es publicable ni
  renombrando: el material es de él, no mío.

El resto son privados simplemente porque el sistema completo no se publica.

## Nota sobre el conteo de multi-tenancy

El CV menciona que la multi-tenancy está repartida en 26 de los 35 módulos. Ese
número no es la cantidad total, sino cuántos **leen `client_id` o `account_id`**
como parámetro o como filtro: resuelven configuración por cliente, aíslan datos
por cuenta o enrutan según la cuenta. Los 9 restantes son utilidades que no
saben de qué cuenta viene lo que procesan.

---

<a name="english"></a>
# 🇬🇧 English — Module map

The production system has **35 modules** in `app/`. The Spanish table above lists
all of them with real line counts and marks which are published here.

**Published:** 8 of 35 modules — 6 in full, 2 as fragments.

## Why this selection

Published modules are the ones that **read at a glance and show a decision**. The
rest are out for two distinct reasons:

- **By size.** `agent.py` (5814 lines) and `admin.py` (8367) are the two largest
  files. Neither helps a five-minute evaluation, and both show technical debt
  without the context of how it got there. That context is in the README
  decisions.
- **By client content.** `personalities.py` is built from transcripts of the
  client's real conversations. Not publishable even renamed: the material is
  theirs, not mine.

The rest are private simply because the full system isn't published.

## Note on the multi-tenancy count

The CV mentions multi-tenancy spread across 26 of the 35 modules. That number
isn't the total, but how many **read `client_id` or `account_id`** as a parameter
or filter: resolve per-client config, isolate data per account, or route by
account. The remaining 9 are utilities that don't know which account they're
processing.
