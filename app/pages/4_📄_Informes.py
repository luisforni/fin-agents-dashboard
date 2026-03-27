import streamlit as st

from utils.api import APIClient

st.set_page_config(page_title="Informes – FinAgents", page_icon="📄", layout="wide")

if not st.session_state.get("token"):
    st.warning("Inicia sesión primero.")
    st.stop()

client = APIClient(st.session_state.token)

st.title("📄 Informes")

with st.sidebar:
    st.markdown("### FinAgents")


accounts = client.list_accounts()
accounts = accounts if isinstance(accounts, list) else []

with st.expander("+ Generar nuevo informe", expanded=not bool(client.list_reports())):
    with st.form("new_report"):
        col1, col2 = st.columns(2)
        with col1:
            report_type = st.selectbox(
                "Tipo de informe",
                ["monthly_summary", "risk_analysis", "executive_brief", "custom"],
                format_func=lambda x: {
                    "monthly_summary": "Resumen mensual",
                    "risk_analysis": "Análisis de riesgo",
                    "executive_brief": "Informe ejecutivo",
                    "custom": "Personalizado",
                }.get(x, x),
            )
        with col2:
            if accounts:
                account_options = {"(todas las cuentas)": None} | {
                    f"{a.get('name', 'Sin nombre')} — {str(a.get('id', ''))[:8]}": a.get("id")
                    for a in accounts
                }
                selected_acc = st.selectbox("Cuenta", list(account_options.keys()))
                selected_account_id = account_options[selected_acc]
            else:
                st.info("No hay cuentas disponibles.")
                selected_account_id = None

        report_title = st.text_input("Título (opcional)", placeholder="Informe Q1 2026")

        if st.form_submit_button("Generar informe", type="primary", use_container_width=True):
            with st.spinner("Generando informe..."):
                result = client.create_report(
                    report_type,
                    account_id=str(selected_account_id) if selected_account_id else None,
                    title=report_title or None,
                )
            if result:
                st.success(f"Informe generado: `{str(result.get('id', ''))[:8]}...`")
                st.rerun()
            else:
                st.error("Error al generar el informe.")

st.divider()


reports = client.list_reports()
reports = reports if isinstance(reports, list) else []

if not reports:
    st.info("No hay informes. Genera uno con el formulario de arriba.")
    st.stop()

st.subheader(f"Informes generados ({len(reports)})")

type_labels = {
    "monthly_summary": "📅 Resumen mensual",
    "risk_analysis": "⚠️ Análisis de riesgo",
    "executive_brief": "📋 Informe ejecutivo",
    "custom": "📝 Personalizado",
}

for report in sorted(reports, key=lambda r: r.get("created_at", ""), reverse=True):
    report_id = report.get("id", "")
    report_type = report.get("report_type", "custom")
    title = report.get("title") or type_labels.get(report_type, report_type)
    created = report.get("created_at", "")[:10]

    with st.expander(f"{type_labels.get(report_type, '📝')} **{title}** — {created}"):
        col_meta, col_action = st.columns([3, 1])
        with col_meta:
            st.caption(f"ID: `{str(report_id)[:8]}...`  |  Tipo: `{report_type}`  |  Fecha: {created}")
            if report.get("account_id"):
                st.caption(f"Cuenta: `{str(report.get('account_id', ''))[:8]}...`")

        with col_action:
            if st.button("Ver completo", key=f"view_{report_id}"):
                st.session_state[f"show_report_{report_id}"] = True

        if st.session_state.get(f"show_report_{report_id}"):
            with st.spinner("Cargando informe..."):
                full = client.get_report(str(report_id))
            if full:
                content = full.get("content") or full.get("body") or full.get("markdown") or ""
                metadata = full.get("metadata", {})
                if content:
                    st.markdown("---")
                    st.markdown(content)
                if metadata:
                    with st.expander("Metadatos"):
                        st.json(metadata)
            else:
                st.error("No se pudo cargar el informe.")
