import plotly.graph_objects as go
import streamlit as st

from utils.api import APIClient

st.set_page_config(page_title="Riesgo – FinAgents", page_icon="⚠️", layout="wide")

if not st.session_state.get("token"):
    st.warning("Inicia sesión primero.")
    st.stop()

client = APIClient(st.session_state.token)

st.title("⚠️ Motor de Riesgo")

with st.sidebar:
    st.markdown("### FinAgents")


accounts = client.list_accounts()
accounts = accounts if isinstance(accounts, list) else []

if accounts:
    account_options = {
        f"{a.get('name', 'Sin nombre')} — {str(a.get('id', ''))[:8]}": a
        for a in accounts
    }
    selected_label = st.selectbox("Cuenta a analizar", list(account_options.keys()))
    selected_account = account_options[selected_label]
    account_id = selected_account.get("id")

    if st.button("Evaluar riesgo ahora", type="primary"):
        with st.spinner("Calculando score de riesgo..."):
            result = client.evaluate_risk(account_id, "account")
        if result:
            st.session_state["last_score"] = result
            st.rerun()
        else:
            st.error("Error al evaluar el riesgo.")
else:
    st.info("Crea una cuenta en Transacciones primero.")
    account_id = None

st.divider()


score_data = st.session_state.get("last_score")
if score_data:
    score = score_data.get("score", 0)
    level = score_data.get("level", "low")

    color_map = {"low": "#22C55E", "medium": "#EAB308", "high": "#F97316", "critical": "#EF4444"}
    label_map = {"low": "Bajo", "medium": "Medio", "high": "Alto", "critical": "Crítico"}
    color = color_map.get(level, "#94A3B8")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Score de riesgo")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(score * 100, 1),
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": label_map.get(level, level), "font": {"color": color}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#F1F5F9"},
                "bar": {"color": color},
                "bgcolor": "#1E293B",
                "steps": [
                    {"range": [0, 30], "color": "#14532D"},
                    {"range": [30, 60], "color": "#713F12"},
                    {"range": [60, 80], "color": "#7C2D12"},
                    {"range": [80, 100], "color": "#450A0A"},
                ],
                "threshold": {"line": {"color": "white", "width": 4}, "thickness": 0.75, "value": round(score * 100, 1)},
            },
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#F1F5F9",
            height=280,
            margin=dict(t=30, b=10, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Desglose por estrategia")
        breakdown = score_data.get("breakdown", {})
        if breakdown:
            for strategy, details in breakdown.items():
                s_score = details.get("score", 0) if isinstance(details, dict) else details
                s_pct = round(float(s_score) * 100, 1)
                bar_color = color_map.get("low" if s_pct < 30 else "medium" if s_pct < 60 else "high" if s_pct < 80 else "critical", "#94A3B8")
                st.markdown(f"**{strategy.replace('_', ' ').title()}**")
                st.progress(s_pct / 100, text=f"{s_pct}%")
        else:
            st.json(score_data)

    alerts_in_score = score_data.get("alerts", [])
    if alerts_in_score:
        st.subheader("Alertas generadas")
        for alert in alerts_in_score:
            level_a = alert.get("level", "medium")
            icon = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(level_a, "⚪")
            st.warning(f"{icon} **{alert.get('alert_type', '')}** — {alert.get('description', '')}")

st.divider()


st.subheader("Todas las alertas")
alerts = client.list_alerts()
alerts = alerts if isinstance(alerts, list) else []

if not alerts:
    st.info("No hay alertas registradas.")
else:
    open_alerts = [a for a in alerts if a.get("status") != "resolved"]
    resolved_alerts = [a for a in alerts if a.get("status") == "resolved"]

    tab_open, tab_resolved = st.tabs([f"Abiertas ({len(open_alerts)})", f"Resueltas ({len(resolved_alerts)})"])

    with tab_open:
        if not open_alerts:
            st.success("No hay alertas abiertas.")
        for alert in open_alerts:
            level_a = alert.get("level", "medium")
            icon = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(level_a, "⚪")
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"{icon} **{alert.get('alert_type', '')}** — {alert.get('description', '')}")
                st.caption(f"Entidad: {str(alert.get('entity_id', ''))[:8]}  |  {alert.get('created_at', '')[:10]}")
            with col_b:
                if st.button("Resolver", key=f"resolve_{alert.get('id')}"):
                    client.resolve_alert(str(alert.get("id")))
                    st.rerun()
            st.divider()

    with tab_resolved:
        if not resolved_alerts:
            st.info("No hay alertas resueltas.")
        for alert in resolved_alerts:
            st.markdown(f"✅ ~~{alert.get('alert_type', '')}~~ — {alert.get('description', '')}")
            st.caption(f"{alert.get('created_at', '')[:10]}")
