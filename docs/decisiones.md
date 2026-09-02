**🇦🇷 Español · 🇬🇧 [English](#-english)**

# Decisiones de diseño — SetterBot

Cada decisión lleva sus cuatro partes: qué se hizo, contra qué, por qué, y qué
costó. La cuarta es la que importa.

## Verificación de agenda como paso aparte

- **Qué se hizo:** no se confía en el webhook de Cal.com. Cuando el bot no
  puede verificar la reserva contra la API y tampoco con el nombre que dio el
  lead, el booking queda en estado `agendado_no_verificado` y un humano decide
  desde el panel: `confirmar_verificacion()` (reserva real, continúa el flujo
  post-agenda) o `marcar_falso_positivo()` (el lead mintió o se confundió y
  vuelve a `link_enviado`). Ver `snippets/verificacion_de_agenda.py`.
- **Alternativa descartada:** dar el lead por agendado apenas llega el webhook.
- **Por qué:** el webhook puede no llegar o llegar tarde, y un "agendado" falso
  contaminaba la cola del closer. El chequeo posterior convierte el agendado en
  un hecho verificado, no en una suposición.
- **Qué costó:** una llamada más a la API y latencia en el cierre del flujo.
  Además, la verificación es humana: sin alguien en el panel, el lead queda en
  el medio.

## La personalidad se construye desde conversaciones reales del cliente

- **Qué se hizo:** el system prompt de cada cuenta se arma a partir de las
  conversaciones reales del cliente, imitando su tono, su vocabulario y su
  manera de cerrar. El prompt es propiedad del cliente y no se publica.
- **Alternativa descartada:** un prompt genérico de "asistente de ventas".
- **Por qué:** el prospecto tiene que sentir que habla con el dueño, no con una
  IA. Un prompt genérico responde bien y vende mal.
- **Qué costó:** no es portable entre clientes: hay que rehacerlo en cada
  onboarding. Y por eso mismo el repositorio público no puede mostrar el prompt
  real — sería filtrar conversaciones del cliente.

## Multi-tenancy por configuración, no por fork por cliente

- **Qué se hizo:** los tres clientes corren en un solo servidor. El `account_id`
  selecciona personalidad, token de Instagram, pestaña de Google Sheets y reglas;
  todo eso se edita desde el panel `/admin`.
- **Alternativa descartada:** un fork y un deploy por cliente.
- **Por qué:** los tres clientes son independientes entre sí — nichos, cuentas
  y datos separados. Justamente por eso el aislamiento tenía que ser real. Aun
  así, un deploy por cliente triplicaba servidores, costos y el esfuerzo de cada
  actualización para una sola persona, y cada alta nueva habría exigido tocar
  código. Con configuración, sumar una cuenta es cargar datos.
- **Qué costó:** el panel creció mucho y la configuración quedó dispersa en
  varios módulos. La validación de que una cuenta no vea los leads de otra
  (fuga cross-tenant) pasó a ser una preocupación de primer orden — de ahí el
  test de verificación que se publica en `tests/`.

## Interfaz servida desde Python, sin motor de plantillas

- **Qué se hizo:** el panel `/admin` se sirve directamente desde Python, sin
  motor de plantillas ni frontend aparte.
- **Alternativa descartada:** separar la interfaz con un motor de plantillas o
  un framework de frontend.
- **Por qué:** aceleraba el arranque: un solo lenguaje, un solo proceso, cero
  build, cero despliegue adicional.
- **Qué costó:** y es el costo real de este proyecto: `admin.py` llegó a 8367
  líneas y `agent.py` a 5814. Es el ejemplo de una decisión que acelera al
  principio y se cobra después — y es la razón principal por la que estos dos
  archivos no se publican en esta vitrina.

## Transcripción de voz dentro del mismo flujo de texto

- **Qué se hizo:** el audio se descarga y se transcribe a texto antes de entrar
  al motor de reglas. El resto del sistema nunca sabe que el mensaje entró como
  audio. Ver `snippets/transcripcion_de_voz.py`.
- **Alternativa descartada:** un flujo separado de audio, con su propio pipeline
  de descarga, transcripción y almacenamiento.
- **Por qué:** filtros, temperatura y scoring procesan una sola cosa: texto.
  Resolver la voz en el borde mantiene al resto del sistema simple.
- **Qué costó:** depende de un proveedor externo (Groq Whisper) y suma latencia
  al primer mensaje. Si el proveedor cae, la voz queda sin responder (el bot
  degrada a texto silencioso).

---

<a name="english"></a>
# 🇬🇧 English — Design decisions

Each decision has four parts: what was done, against what, why, and what it cost.
The fourth is the one that matters.

## Booking verification as a separate step

- **What:** the Cal.com webhook is not trusted. When the bot can't verify the
  booking against the API nor with the name the lead gave, the booking stays
  `booked_unverified` and a human decides from the panel: confirm (real booking,
  continue the post-booking flow) or mark false positive (the lead lied or got
  confused, back to `link_sent`). See `snippets/verificacion_de_agenda.py`.
- **Rejected alternative:** mark the lead booked as soon as the webhook arrives.
- **Why:** the webhook may not arrive or arrive late, and a false "booked"
  polluted the closer's queue. The later check turns "booked" into a verified
  fact, not an assumption.
- **Cost:** one more API call and latency at flow close. The verification is
  human: with no one at the panel, the lead is stuck in the middle.

## The persona is built from the client's real conversations

- **What:** each account's system prompt is assembled from the client's real
  conversations, mirroring their tone, vocabulary and closing style. The prompt
  is the client's property and is not published.
- **Rejected alternative:** a generic "sales assistant" prompt.
- **Why:** the prospect has to feel they're talking to the owner, not an AI. A
  generic prompt answers well and sells poorly.
- **Cost:** not portable between clients — rebuilt at each onboarding. And for
  that same reason the public repo can't show the real prompt: it would leak the
  client's conversations.

## Multi-tenancy by configuration, not a fork per client

- **What:** the three clients run on a single server. `account_id` selects
  persona, Instagram token, Google Sheets tab and rules; all edited from `/admin`.
- **Rejected alternative:** a fork and a deploy per client.
- **Why:** the three clients are independent — separate niches, accounts and
  data. That's exactly why isolation had to be real. Still, a deploy per client
  tripled servers, cost and update effort for a single person, and every new
  onboarding would have meant touching code. With configuration, adding an
  account is loading data.
- **Cost:** the panel grew a lot and configuration ended up spread across
  modules. Validating that one account can't see another's leads (cross-tenant
  leak) became a first-order concern — hence the verification test published in
  `tests/`.

## Interface served from Python, no template engine

- **What:** the `/admin` panel is served directly from Python, no template
  engine or separate frontend.
- **Rejected alternative:** split the interface with a template engine or a
  frontend framework.
- **Why:** it sped up the start: one language, one process, zero build, no extra
  deployment.
- **Cost:** and it's this project's real cost: `admin.py` reached 8367 lines and
  `agent.py` 5814. The case of a decision that accelerates early and charges you
  later — and the main reason those two files aren't published here.

## Voice transcription inside the same text flow

- **What:** audio is downloaded and transcribed to text before entering the rule
  engine. The rest of the system never knows it came in as audio. See
  `snippets/transcripcion_de_voz.py`.
- **Rejected alternative:** a separate audio flow with its own download,
  transcription and storage pipeline.
- **Why:** filters, temperature and scoring process one thing: text. Resolving
  voice at the edge keeps the rest of the system simple.
- **Cost:** depends on an external provider (Groq Whisper) and adds latency to
  the first message. If the provider is down, voice goes unanswered.
