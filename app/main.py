import streamlit as st

from utils.api import APIClient

st.set_page_config(
    page_title="FinAgents",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

for key, default in [("token", None), ("user_id", None), ("user_email", None)]:
    if key not in st.session_state:
        st.session_state[key] = default


def login_page() -> None:
    st.markdown("## 📊 FinAgents")
    st.markdown("*Plataforma Multiagente de Análisis Financiero*")
    st.divider()

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        tab_login, tab_register = st.tabs(["Iniciar sesión", "Registrarse"])

        with tab_login:
            with st.form("login"):
                email = st.text_input("Email")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

            if submitted:
                if not email or not password:
                    st.error("Completa todos los campos.")
                else:
                    result = APIClient().login(email, password)
                    if result and "access_token" in result:
                        st.session_state.token = result["access_token"]
                        st.session_state.user_email = email
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")

        with tab_register:
            with st.form("register"):
                r_name = st.text_input("Nombre completo")
                r_email = st.text_input("Email", key="r_email")
                r_pass = st.text_input("Contraseña", type="password", key="r_pass")
                r_submitted = st.form_submit_button("Crear cuenta", use_container_width=True)

            if r_submitted:
                if not r_name or not r_email or not r_pass:
                    st.error("Completa todos los campos.")
                else:
                    result = APIClient().register(r_email, r_pass, r_name)
                    if result:
                        st.success("Cuenta creada. Ahora inicia sesión.")
                    else:
                        st.error("Error al registrar. El email ya podría existir.")


def home_page() -> None:
    client = APIClient(st.session_state.token)

    st.title("📊 FinAgents Dashboard")
    st.caption(f"Sesión: {st.session_state.user_email}")

    accounts = client.list_accounts()
    alerts = client.list_alerts()
    reports = client.list_reports()
    transactions = client.list_transactions()

    n_accounts = len(accounts) if isinstance(accounts, list) else 0
    n_alerts = len([a for a in alerts if isinstance(alerts, list) and a.get("status") != "resolved"])
    n_reports = len(reports) if isinstance(reports, list) else 0
    n_tx = len(transactions) if isinstance(transactions, list) else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cuentas", n_accounts)
    col2.metric("Alertas activas", n_alerts)
    col3.metric("Informes", n_reports)
    col4.metric("Transacciones", n_tx)

    st.divider()

    if isinstance(accounts, list) and accounts:
        st.subheader("Cuentas")
        import pandas as pd
        df = pd.DataFrame([{
            "ID": a.get("id", ""),
            "Nombre": a.get("name", ""),
            "Moneda": a.get("currency", ""),
            "Saldo": a.get("balance", 0),
        } for a in accounts])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay cuentas. Ve a Transacciones para crear una.")

    if isinstance(alerts, list) and alerts:
        open_alerts = [a for a in alerts if a.get("status") != "resolved"]
        if open_alerts:
            st.subheader("Alertas de riesgo recientes")
            for alert in open_alerts[:5]:
                level = alert.get("level", "medium")
                icon = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(level, "⚪")
                st.warning(f"{icon} **{alert.get('alert_type', '')}** — {alert.get('description', '')}")


if st.session_state.token is None:
    login_page()
else:
    with st.sidebar:
        st.markdown("### FinAgents")
        st.caption(st.session_state.user_email or "")
        st.divider()
        if st.button("Cerrar sesión", use_container_width=True):
            for key in ["token", "user_id", "user_email"]:
                st.session_state[key] = None
            st.rerun()

    home_page()
