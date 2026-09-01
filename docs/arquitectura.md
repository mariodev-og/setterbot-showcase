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