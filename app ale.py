import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

# -----------------------------
# Configuración de página
# -----------------------------
st.set_page_config(page_title="Neuro-Rest | Chat Asistente", page_icon="🧠", layout="centered")

# -----------------------------
# Estilos (fondo negro + burbujas con colores)
# -----------------------------
CUSTOM_CSS = """
<style>
:root{
  --bg:#0b0f14;
  --panel:#0f172a;
  --text:#e6e6e6;
  --muted:#94a3b8;
  --bot-bg:#0f172a;
  --bot-br:#1f2a44;
  --user-bg:#1e293b;
  --user-br:#334155;
  --accent:#67e8f9;
  --accent2:#fbcfe8;
}
.stApp{background:var(--bg);}
div.block-container{padding-top:1.4rem;color:var(--text);}
.hero{
  background:var(--panel);
  border:1px solid var(--bot-br);
  border-radius:18px;
  padding:16px 18px;
  margin-bottom:12px;
}
.hero h3{margin:0 0 6px 0;}
.hero p{margin:0 0 6px 0;color:var(--muted);}
.badges{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.25rem}
.badge{
  border:1px solid var(--user-br);
  color:var(--text);
  border-radius:999px;
  padding:4px 10px;
  font-size:.80rem;
}

.chat-wrap{margin-top:.5rem;}
.bubble{
  padding:12px 14px;
  border-radius:16px;
  margin:8px 0;
  max-width:85%;
  line-height:1.55;
  word-wrap:break-word;
  border:1px solid transparent;
}
.bubble .name{
  font-weight:700;
  font-size:.82rem;
  letter-spacing:.02em;
  margin-bottom:4px;
}

.bubble.bot{
  background:var(--bot-bg);
  border-color:var(--bot-br);
}
.bubble.bot .name{color:var(--accent);}

.bubble.user{
  background:var(--user-bg);
  border-color:var(--user-br);
  margin-left:auto;
}
.bubble.user .name{color:var(--accent2);}

/* Enlaces visibles sobre fondo oscuro */
a { color:#7dd3fc; text-decoration:none; }
a:hover { text-decoration:underline; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------
# Cargar API key de forma segura
# -----------------------------
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
if not API_KEY:
    st.error("Falta GROQ_API_KEY. Agrégala en un archivo .env (local) o en Settings → Secrets (Streamlit Cloud).")
    st.stop()

os.environ["GROQ_API_KEY"] = API_KEY
client = Groq()

# -----------------------------
# Estado de sesión
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # [{"role": "user"|"assistant", "content": "..."}]

# -----------------------------
# Prompts (enfoque Neuro-Rest)
# -----------------------------
SYSTEM_PROMPT = (
    "Eres Neuro-Bot, asistente de Neuro-Rest. Explicas con claridad y empatía a familiares y "
    "cuidadores de adultos mayores. No das consejo médico; ofrece hablar con un humano si lo piden. "
    "Responde en 5–8 líneas máx., usa bullets cuando ayuden y ofrece 1 CTA útil (demo, preventa, WhatsApp)."
)

WELCOME = (
    "**¡Hola! Soy Neuro-Bot.**\n\n"
    "**¿Qué es Neuro-Rest?** Es un *dispositivo + app* que ayuda a **reducir riesgos nocturnos** en adultos mayores: "
    "detecta agitación/sueño y activa **luz cálida + sonido relajante**, enviando **alertas** al cuidador.\n\n"
    "**¿En qué puedo ayudarte?**\n"
    "• Cómo funciona  • Precio / preventa  • Agendar demo  • Soporte básico  • Garantía\n"
    "_Información general: no sustituye consejo médico._"
)

# Mostrar cabecera descriptiva (siempre)
st.markdown(
    f"""
<div class="hero">
  <h3>🧠 Neuro-Rest | Asistente Virtual</h3>
  <p>Dispositivo + app para <b>reducir riesgos nocturnos</b> en adultos mayores con monitoreo y estímulos relajantes.</p>
  <div class="badges">
    <span class="badge">Demo</span>
    <span class="badge">Preventa</span>
    <span class="badge">Soporte</span>
    <span class="badge">Garantía</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Si el chat está vacío, mostramos un mensaje de bienvenida (burbuja del bot)
def render_message(role: str, content: str):
    who = "Neuro-Bot" if role == "assistant" else "Tú"
    cls = "bot" if role == "assistant" else "user"
    st.markdown(
        f"""
<div class="bubble {cls}">
  <div class="name">{who}</div>
  <div>{content}</div>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

if not st.session_state.chat_history:
    render_message("assistant", WELCOME)

# Renderizar historial
for msg in st.session_state.chat_history:
    render_message(msg["role"], msg["content"])

# -----------------------------
# Entrada del usuario
# -----------------------------
user_input = st.chat_input("Escribe tu consulta…")

if user_input:
    # Agregar y renderizar mensaje del usuario
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    render_message("user", user_input)

    # Construir mensajes para el modelo (contexto breve)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Añadimos la descripción WELCOME como contexto del bot
    messages.append({"role": "system", "content": "Contexto del producto:\n" + WELCOME})
    # Historial (últimos 8 turnos para mantenerlo ligero)
    messages.extend(st.session_state.chat_history[-8:])

    # Llamar al modelo
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.5,
        )
        respuesta_texto = response.choices[0].message.content
    except Exception as e:
        respuesta_texto = f"Lo siento, ocurrió un error al llamar a la API: `{e}`"

    # Mostrar respuesta del asistente y guardar
    st.session_state.chat_history.append({"role": "assistant", "content": respuesta_texto})
    render_message("assistant", respuesta_texto)

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Pie (Nota)
# -----------------------------
st.caption("💡 Tips: Si vienes de una feria o anuncio, pide una **demo**. Para contacto rápido usa WhatsApp (handoff humano).")
