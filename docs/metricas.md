**🇦🇷 Español · 🇬🇧 [English](#-english)**

# Métricas de operación

Números reales de la base de datos de producción, medidos el 2026-08-28.

**Todo lo que sigue son agregados.** Ninguna consulta devolvió datos de una
persona: ni usuarios de Instagram, ni nombres, ni contenido de conversaciones.
Son conteos, sumas y promedios sobre la tabla de leads. La base se consultó en
sesión de solo lectura.

## Volumen

| | |
|---|---:|
| Conversaciones atendidas | **2.449** |
| Mensajes procesados | **32.021** |
| Mensajes por conversación (promedio) | 13,1 |
| Conversación más larga | 64 mensajes |
| Período de operación | 22/05/2026 – 24/08/2026 |
| Días corridos | 94 |

Actividad mes a mes, sin cortes:

| Mes | Conversaciones | Agendas |
|---|---:|---:|
| 2026-05 | 921 | 27 |
| 2026-06 | 522 | 19 |
| 2026-07 | 663 | 11 |
| 2026-08 | 343 | 10 |

## Multi-tenancy

**3 cuentas** dadas de alta, cada una con sus propias preguntas, filtros y
ajustes persistidos en la base. **2** llegaron a recibir tráfico real:

| Cuenta | Conversaciones | Agendas |
|---|---:|---:|
| 1 | 2.325 | 62 |
| 2 | 124 | 5 |

Las cuentas van sin nombre a propósito: son clientes reales.

## Transcripción de voz

**292 conversaciones (11,9%)** incluyeron al menos una nota de voz que el sistema
transcribió y procesó como texto.

Es el dato que sostiene la decisión de resolver el audio antes del motor de
reglas: uno de cada ocho prospectos respondió hablando, no escribiendo.

## Scoring

**547 leads** alcanzaron score 6 o más sobre 10. Distribución completa:

| Score | Leads |
|---:|---:|
| 8 | 176 |
| 7 | 193 |
| 6 | 178 |
| 5 | 48 |
| 4 | 135 |
| 3 | 45 |
| 2 | 73 |
| 1 | 467 |
| 0 | 1.134 |

La concentración en 0 y 1 es esperable: la mayoría de los mensajes entrantes a
una cuenta de Instagram con audiencia no son prospectos. Filtrar ese ruido era
justamente el trabajo del bot.

## Lo que no está acá, y por qué

Tres métricas existen en la base pero no se publican, porque los números no
sostienen lo que el código sí hace:

- **Embudo de calificación.** El flag que marca el inicio de la calificación se
  agregó tarde y no cubre los primeros meses, así que da menos entradas que
  agendas — un imposible. El dato está roto, no el sistema.
- **Verificación de agenda.** La función se sumó en agosto y alcanzó a correr
  sobre 2 casos. La decisión de diseño se explica en el README; el volumen no la
  respalda todavía y decirlo es más honesto que omitirlo.
- **Facturación.** Es información comercial del cliente y mía. No corresponde.

También se descartó publicar la tasa de conversión global (67 agendas sobre 2.449
conversaciones). Sin contexto parece baja, y no lo es: la mayoría de esas
conversaciones nunca fueron prospectos. Los números absolutos cuentan mejor lo
que pasó.

---

<a name="english"></a>
# 🇬🇧 English — Operation metrics

Real numbers from the production database, measured on 2026-08-28.

**Everything below is aggregate.** No query returned a person's data: no
Instagram handles, no names, no conversation content. They're counts, sums and
averages over the leads table. The database was queried in a read-only session.

## Volume

| | |
|---|---:|
| Conversations handled | **2,449** |
| Messages processed | **32,021** |
| Messages per conversation (avg) | 13.1 |
| Longest conversation | 64 messages |
| Operation period | 2026-05-22 – 2026-08-24 |
| Straight days | 94 |

Month by month, without gaps:

| Month | Conversations | Bookings |
|---|---:|---:|
| 2026-05 | 921 | 27 |
| 2026-06 | 522 | 19 |
| 2026-07 | 663 | 11 |
| 2026-08 | 343 | 10 |

## Multi-tenancy

**3 accounts** onboarded, each with its own questions, filters and settings
persisted in the database. **2** received real traffic:

| Account | Conversations | Bookings |
|---|---:|---:|
| 1 | 2,325 | 62 |
| 2 | 124 | 5 |

Accounts go unnamed on purpose: they're real clients.

## Voice transcription

**292 conversations (11.9%)** included at least one voice note the system
transcribed and processed as text. It's the number that backs the decision to
resolve audio before the rule engine: one in eight prospects replied by speaking.

## Scoring

**547 leads** reached a score of 6 or more out of 10. Full distribution: 8→176,
7→193, 6→178, 5→48, 4→135, 3→45, 2→73, 1→467, 0→1,134. The concentration at 0
and 1 is expected: most inbound messages to an Instagram account with an audience
aren't prospects. Filtering that noise was exactly the bot's job.

## What's not here, and why

Three metrics exist in the database but aren't published, because the numbers
don't back what the code does: the qualification funnel (a flag added late gives
fewer entries than bookings — the data is broken, not the system), booking
verification (the function shipped in August and ran on 2 cases), and billing
(the client's and my commercial information). The global conversion rate (67
bookings over 2,449 conversations) was also dropped: without context it looks
low, and it isn't — most of those conversations were never prospects.
