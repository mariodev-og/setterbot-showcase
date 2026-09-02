**🇦🇷 Español · 🇬🇧 [English](#-english)**

# Arquitectura — SetterBot

## Vista general

```
                         ┌─────────────────────────────────────────────┐
   Instagram DM          │              Un solo servidor               │
 ───────────────────────►│                                             │
   (Meta Graph API,      │   FastAPI (webhook)                         │
    webhook POST)        │      │  routing por page_id → account_id    │
                         │      ▼                                      │
                         │   filtros de gatillos                       │
                         │      │  (pausan el bot + alerta al humano)  │
                         │      ▼                                      │
                         │   motor de reglas ──► Claude API            │
                         │      │  personalidad por cuenta             │
                         │      ├─► transcripción de voz (Groq Whisper)│
                         │      ├─► temperatura del lead (cada 4+ msg) │
                         │      └─► scoring (reglas fijas, sin IA)     │
                         │      ▼                                      │
                         │   Google Sheets (vista del cliente)         │
                         │   Cal.com (link de agenda)                  │
                         │      ▼                                      │
                         │   verificación de agenda (chequeo posterior)│
                         └─────────────────────────────────────────────┘
```

## Flujo de datos

1. **Entrada.** Un lead manda un DM a la cuenta de Instagram del cliente. Meta
   Graph API entrega el mensaje como webhook `POST` al servidor.

2. **Routing multi-cuenta.** El webhook trae un `page_id`; un mapa en `main.py`
   lo convierte en `account_id`. Así un solo servidor atiende tres cuentas de
   cliente y cada una sabe qué personalidad, qué reglas y qué pestaña de
   Google Sheets le tocan.

3. **Filtros de gatillos.** Corren antes que el LLM. Si el mensaje dispara una
   pausa (consulta a terceros, falta de intención, competencia), el bot no
   responde y se genera una alerta para el setter humano. El lead queda
   `pausado`.

4. **Motor de reglas + LLM.** Si no hay gatillo, Claude responde siguiendo la
   personalidad de esa cuenta, construida a partir de conversaciones reales del
   cliente. El sistema extrae datos del mensaje (facturación, pain point, etc.).

5. **Audio.** Si el mensaje entró como nota de voz, se transcribe con Groq
   Whisper *antes* de pasar al motor de reglas. El resto del sistema solo ve
   texto.

6. **Temperatura y scoring.** Cada cuatro o más mensajes, Claude clasifica al
   lead como caliente/tibio/frío/desinteresado con un vocabulario cerrado. El
   score (1-10) se recalcula con reglas fijas tras cada mensaje.

7. **Persistencia.** Cada paso se guarda en Google Sheets, la vista que el
   cliente ve y edita en tiempo real. Es la base de datos visible, no un
   detalle cosmético.

8. **Agenda.** Cuando el lead quiere agendar, se le pasa el link de Cal.com. La
   reserva **no** se da por confirmada por el webhook: queda en
   `agendado_no_verificado` y un humano la confirma. Solo ahí el bot continúa el
   flujo post-agenda.

## Qué sale del sistema

- Respuestas al lead por Instagram.
- Fila actualizada por lead en Google Sheets, con color según temperatura.
- Aviso al closer cuando el bot agenda.
- Tabla de agendados en el panel `/admin` para seguimiento de llamadas.

## Punto de tensión principal

La configuración vive dispersa: personalidad, preguntas y reglas se editan
desde el panel pero se aplican en módulos distintos. Es el costo directo de la
decisión de multi-tenancy por configuración (ver `decisiones.md`).

---

<a name="english"></a>
# 🇬🇧 English — Architecture

## Data flow

1. **Input.** A lead DMs the client's Instagram account. Meta Graph API delivers
   the message as a `POST` webhook to the server.
2. **Multi-account routing.** The webhook carries a `page_id`; a map in `main.py`
   turns it into `account_id`. A single server serves three client accounts and
   each knows which persona, rules and Google Sheets tab are its own.
3. **Trigger filters.** They run before the LLM. If the message trips a pause
   (third-party query, no intent, competitor), the bot doesn't reply and an
   alert is raised for the human setter. The lead stays `paused`.
4. **Rule engine + LLM.** With no trigger, Claude replies following that
   account's persona, built from the client's real conversations. The system
   extracts data from the message (budget, pain point, etc.).
5. **Audio.** If the message came in as a voice note, it's transcribed with Groq
   Whisper *before* the rule engine. The rest of the system only sees text.
6. **Temperature and scoring.** Every four-plus messages, Claude classifies the
   lead as hot/warm/cold/uninterested with a closed vocabulary. The score (1-10)
   is recomputed with fixed rules after each message.
7. **Persistence.** Each step is saved to Google Sheets, the view the client
   sees and edits in real time. It's the visible database, not a cosmetic detail.
8. **Booking.** When the lead wants to book, the Cal.com link is sent. The
   booking is **not** taken as confirmed by the webhook: it stays
   `booked_unverified` and a human confirms it. Only then does the bot continue
   the post-booking flow.

## What comes out of the system

- Replies to the lead on Instagram.
- An updated row per lead in Google Sheets, colored by temperature.
- A notice to the closer when the bot books.
- A booked-leads table in the `/admin` panel for call follow-up.

## Main tension point

Configuration lives spread out: persona, questions and rules are edited from the
panel but applied in different modules. It's the direct cost of the
multi-tenancy-by-configuration decision (see `decisiones.md`).
