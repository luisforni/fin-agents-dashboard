import streamlit as st

from utils.api import APIClient

st.set_page_config(page_title="Análisis IA – FinAgents", page_icon="🤖", layout="wide")

if not st.session_state.get("token"):
    st.warning("Inicia sesión primero.")
    st.stop()

client = APIClient(st.session_state.token)

st.title("🤖 Agente IA — LangGraph")
st.caption("Pipeline: DataCollector → RiskAnalyst → ExecutiveWriter")

with st.sidebar:
    st.markdown("### FinAgents")
    st.divider()
    st.info(
        "El agente recopila transacciones, evalúa el riesgo y genera "
        "un informe ejecutivo usando LLM (Ollama/OpenAI)."
    )


if "agent_session_id" not in st.session_state:
    st.session_state.agent_session_id = None
if "agent_messages" not in st.session_state:
    st.session_state.agent_messages = []

accounts = client.list_accounts()
accounts = accounts if isinstance(accounts, list) else []

col_session, col_account = st.columns(2)

with col_session:
    if st.session_state.agent_session_id:
        st.success(f"Sesión activa: `{str(st.session_state.agent_session_id)[:8]}...`")
        if st.button("Nueva sesión"):
            st.session_state.agent_session_id = None
            st.session_state.agent_messages = []
            st.rerun()
    else:
        if st.button("Iniciar sesión de análisis", type="primary"):
            session = client.create_session("Dashboard analysis")
            if session:
                st.session_state.agent_session_id = session.get("id")
                st.rerun()
            else:
                st.error("No se pudo crear la sesión.")

with col_account:
    if accounts:
        account_options = {
            f"{a.get('name', 'Sin nombre')} — {str(a.get('id', ''))[:8]}": a
            for a in accounts
        }
        selected_label = st.selectbox("Cuenta de referencia", ["(ninguna)"] + list(account_options.keys()))
        context_account = account_options.get(selected_label)
    else:
        st.info("Crea una cuenta primero.")
        context_account = None

st.divider()


for msg in st.session_state.agent_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if not st.session_state.agent_messages:
    st.markdown("**Consultas sugeridas:**")
    presets = [
        "Analiza el riesgo de esta cuenta y dame un resumen ejecutivo",
        "¿Hay patrones de transacciones sospechosos en el último mes?",
        "Genera un informe de riesgo completo con recomendaciones",
        "¿Cuál es el nivel de riesgo actual y por qué?",
    ]
    cols = st.columns(2)
    for i, preset in enumerate(presets):
        if cols[i % 2].button(preset, key=f"preset_{i}", use_container_width=True):
            if not st.session_state.agent_session_id:
                session = client.create_session("Dashboard analysis")
                if session:
                    st.session_state.agent_session_id = session.get("id")
            st.session_state._pending_message = preset
            st.rerun()

if hasattr(st.session_state, "_pending_message") and st.session_state._pending_message:
    pending = st.session_state._pending_message
    st.session_state._pending_message = None
    user_input = pending
else:
    user_input = st.chat_input(
        "Escribe tu consulta al agente...",
        disabled=not st.session_state.agent_session_id,
    )

if user_input:
    if not st.session_state.agent_session_id:
        st.error("Inicia una sesión primero.")
        st.stop()

    message = user_input
    if context_account:
        account_id = context_account.get("id")
        message = f"{user_input}\n\n[Cuenta de referencia: {account_id}]"

    st.session_state.agent_messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("El agente está procesando... (DataCollector → RiskAnalyst → ExecutiveWriter)"):
            result = client.run_agent(str(st.session_state.agent_session_id), message)

        if result:
            response = result.get("response") or result.get("output") or result.get("final_response") or str(result)
            st.markdown(response)
            st.session_state.agent_messages.append({"role": "assistant", "content": response})

            if result.get("metadata") or result.get("steps"):
                with st.expander("Detalles del pipeline"):
                    if result.get("steps"):
                        for step in result["steps"]:
                            st.markdown(f"**{step.get('node', '')}**: {step.get('summary', '')}")
                    else:
                        st.json(result.get("metadata", {}))
        else:
            err_msg = "Error al ejecutar el agente. Comprueba que el LLM esté configurado (OPENAI_API_KEY o Ollama)."
            st.error(err_msg)
            st.session_state.agent_messages.append({"role": "assistant", "content": err_msg})
