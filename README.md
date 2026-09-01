# SetterBot

> Agente de ventas automatizado que califica leads en Instagram y agenda llamadas para un closer humano.

**Este repositorio es una vitrina técnica, no el sistema.** El sistema en
producción es privado. Acá están la arquitectura, las decisiones de diseño, las
pruebas y algunos fragmentos de código elegidos para mostrar cómo está resuelto.

---

## El problema

Un coach con marca personal recibía decenas de mensajes por Instagram por día y
no podía responderlos todos, filtrar quién tenía intención real de comprar y
agendar la llamada de venta con su closer. Las herramientas de automatización
existentes (ManyChat, n8n) cobran por mensaje o resuelven con flujos visuales
que no dan el control fino que necesita la calificación de un lead.

El bot tenía que hacer el trabajo de un setter humano: saludar, calificar con
preguntas, detectar si el prospecto era el perfil correcto, medir temperatura
y recién pasar a agenda a los calientes. Y tenía que correr en las cuentas
reales del cliente, en producción, sin romper una conversación.

En el camino se probó el modelo multi-tenant: tres cuentas de cliente corriendo
en un solo servidor, cada una con su personalidad, sus preguntas y sus reglas,
editables desde un panel.

## Arquitectura

```
DM en Instagram
      │   Meta Graph API — webhook POST
      ▼
 FastAPI ────► routing por page_id ──► account_id
      │
      ▼
filtros de gatillos   (si detectan, el bot se calla y alerta al humano)
      │
      ▼
motor de reglas ──► Claude (personalidad por cuenta)
      │
      ├── transcripción de voz (se resuelve ANTES del motor de reglas)
      ├── temperatura del lead (cada 4+ mensajes)
      └── scoring (reglas fijas, sin IA)
      │
      ▼
 Google Sheets (vista del cliente)   Cal.com (link de agenda)
      │
      ▼
verificación de agenda (chequeo posterior, no se confía en el webhook)
```

**Flujo de datos:** el lead manda un DM y el webhook de Meta lo entrega a
FastAPI, que detecta la cuenta por `page_id` y asigna `account_id`. Antes de
llamar al LLM corren los filtros de gatillos: si detectan una pausa (consulta a
terceros, falta de intención, competencia) el bot se calla y genera una alerta
para el humano. Si no hay gatillo, Claude responde con la personalidad de esa
cuenta. Cada cuatro o más mensajes se evalúa la temperatura y se recalcula el
score. Todo se persiste en Google Sheets, que es la vista que el cliente ve y
edita. Cuando el lead quiere agendar, el bot le pasa el link de Cal.com y la
reserva se verifica con un chequeo posterior — nunca se da por agendado por el
solo hecho de recibir el webhook.

Detalle completo en [`docs/arquitectura.md`](docs/arquitectura.md).

## Stack

| Capa | Tecnología | Por qué esta y no otra |
|---|---|---|
| Backend | Python 3.10+ / FastAPI | Control total del flujo, sin suscripciones por mensaje |
| Base de datos visible | Google Sheets | El cliente ve y edita sus leads en tiempo real, sin herramientas técnicas |
| Interfaz | Panel `/admin` servido desde Python | Todo en un lenguaje y un proceso (ver decisión 4) |
| IA | OpenAI o Anthropic segun la cuenta · Groq Whisper (voz) | El proveedor se resuelve por cliente desde el prefijo de su API key, asi una cuenta puede correr en un modelo mas barato sin afectar a las demas |
| Integraciones | Meta Graph API · Cal.com | Instagram directo y agendamiento por link |
| Despliegue | Railway | URL fija sin ngrok, costo fijo bajo |

## Decisiones de diseño

Las decisiones que definieron el proyecto. **Cada una lleva las cuatro partes**:
qué se eligió, contra qué, por qué, y qué costó. La cuarta es la que importa —
una decisión sin costo declarado no es una decisión, es una preferencia.

### Verificación de agenda como paso aparte

- **Qué se hizo:** no se confía en el webhook de Cal.com. Hay un chequeo
  posterior de que la reserva existe: el lead queda en `agendado_no_verificado`
  hasta que un humano la confirma y recién ahí el bot continúa el flujo.
- **Alternativa descartada:** dar el lead por agendado apenas llega el webhook.
- **Por qué:** el webhook puede no llegar o llegar tarde, y un "agendado" falso
  contaminaba la cola del closer.
- **Qué costó:** una llamada más a la API y latencia en el cierre del flujo.

### La personalidad se construye desde conversaciones reales del cliente

- **Qué se hizo:** el prompt de cada cuenta se arma a partir de las
  conversaciones reales del cliente, para que el bot imite su estilo de cierre.
  Por eso el prompt es propiedad del cliente y no se publica.
- **Alternativa descartada:** un prompt genérico de "asistente de ventas".
- **Por qué:** el prospecto tiene que sentir que habla con el dueño, no con una
  IA genérica.
- **Qué costó:** no es portable entre clientes: hay que rehacerlo en cada
  onboarding.

### Multi-tenancy por configuración, no por fork por cliente

- **Qué se hizo:** reglas, preguntas y personalidad se editan desde el panel;
  los tres clientes corren en un solo servidor.
- **Alternativa descartada:** un fork y un deploy por cliente.
- **Por qué:** los tres clientes son independientes entre sí y no comparten
  nada, pero un deploy por cliente triplicaba servidores, costos y el esfuerzo
  de cada actualización para una sola persona. Con configuración, dar de alta
  una cuenta nueva es cargar datos, no tocar código ni desplegar.
- **Qué costó:** el panel creció mucho y la configuración quedó dispersa en
  varios módulos.

### Interfaz servida desde Python, sin motor de plantillas

- **Qué se hizo:** el panel `/admin` se sirve directamente desde Python.
- **Alternativa descartada:** un motor de plantillas separado o un frontend
  aparte.
- **Por qué:** aceleraba el arranque: un solo lenguaje, un solo proceso, cero
  build.
- **Qué costó:** y es un costo real — `admin.py` llegó a 8367 líneas. Es el
  ejemplo de una decisión que acelera al principio y se cobra después.

### Transcripción de voz dentro del mismo flujo de texto

- **Qué se hizo:** el audio se convierte en texto antes de entrar al motor de
  reglas; así el resto del sistema nunca sabe que el mensaje entró como audio.
- **Alternativa descartada:** un flujo separado de audio con su propio pipeline.
- **Por qué:** filtros, temperatura y scoring procesan una sola cosa: texto. La
  voz se resuelve en el borde, en `transcriber.py`.
- **Qué costó:** depende de un proveedor externo (Groq Whisper) y suma latencia
  al primer mensaje.

Detalle completo en [`docs/decisiones.md`](docs/decisiones.md).

## Decisiones sobre este repositorio

Por qué este repo se ve así y no como el proyecto entero:

- **Es una vitrina, no un espejo.** El sistema en producción tiene material de
  clientes: nombres reales, conversaciones reales, audio y datos de negocio.
  Publicarlo entero no era una opción, ni siquiera renombrando: la personalidad
  del bot está construida con transcripciones de conversaciones reales del
  cliente, que son propiedad de él.
- **Se publica lo que se lee, no lo que pesa.** Los archivos más grandes del
  sistema — `admin.py` (8367 líneas) y `agent.py` (5814) — no aportan a quien
  evalúa y muestran deuda técnica sin contexto. En su lugar van fragmentos
  elegidos: cada uno ilustra una decisión y se lee de un vistazo.
- **El único test va completo, y con honestidad.** `tests/test_no_fuga_cross_tenant.py`
  son 22 líneas con `print`s: es un script de verificación manual de que no hay
  fuga de datos entre cuentas, no una suite de pytest. Se presenta como lo que
  es. No hay otra suite en el proyecto.
- **Los nombres de clientes están reemplazados** por ficticios consistentes. No
  hay `[REDACTADO]` ni `XXXX`: un nombre inventado se lee como un ejemplo, un
  tachón se lee como un problema.

## Qué hay en este repositorio

| Carpeta | Qué contiene |
|---|---|
| [`docs/arquitectura.md`](docs/arquitectura.md) | Diagrama y flujo de datos |
| [`docs/decisiones.md`](docs/decisiones.md) | Cada decisión con su porqué y su costo |
| [`docs/mapa_modulos.md`](docs/mapa_modulos.md) | Los 35 módulos del sistema real, con cuáles se publican y cuáles no |
| [`docs/metricas.md`](docs/metricas.md) | Números de operación medidos sobre la base de producción |
| `docs/img/` | Capturas del panel |
| `snippets/` | 8 fragmentos comentados, uno por decisión |
| `tests/` | El script de verificación de fuga cross-tenant |

Los fragmentos de `snippets/` no forman un programa ejecutable: están elegidos
para leerse, no para correrse.

## Escala del proyecto

**2.449 conversaciones y 32.021 mensajes procesados** en 94 días corridos de
operación (22/05/2026 – 24/08/2026). **3 cuentas** dadas de alta con su propia
configuración, **2** con tráfico real. **292 conversaciones (11,9%)** llegaron con
notas de voz que el sistema transcribió.

Del lado del código: 481 commits, 198 archivos, 35 módulos, un panel propio de 76
endpoints y multi-tenancy repartida en 20 de esos módulos.

Detalle y método de medición en [`docs/metricas.md`](docs/metricas.md); el reparto
entre publicado y privado, en [`docs/mapa_modulos.md`](docs/mapa_modulos.md).

## Estado

Entregado. En producción durante ese período; sin clientes activos hoy.

---

## Código completo

El repositorio de producción es privado porque contiene material de clientes.
Puedo dar acceso de lectura durante un proceso de selección: escribime a
**mario1804.dev@gmail.com**.

## Licencia

Todos los derechos reservados. Ver [`LICENSE`](LICENSE).