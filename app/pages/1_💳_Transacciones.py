import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api import APIClient

st.set_page_config(page_title="Transacciones – FinAgents", page_icon="💳", layout="wide")

if not st.session_state.get("token"):
    st.warning("Inicia sesión primero.")
    st.stop()

client = APIClient(st.session_state.token)

st.title("💳 Transacciones")


accounts = client.list_accounts()
accounts = accounts if isinstance(accounts, list) else []

with st.sidebar:
    st.markdown("### FinAgents")
    st.divider()
    st.subheader("Nueva cuenta")
    with st.form("new_account"):
        acc_name = st.text_input("Nombre")
        acc_currency = st.selectbox("Moneda", ["EUR", "USD", "GBP"])
        if st.form_submit_button("Crear cuenta", use_container_width=True, type="primary"):
            result = client.create_account(acc_name, acc_currency)
            if result:
                st.success("Cuenta creada.")
                st.rerun()
            else:
                st.error("Error al crear la cuenta.")


if not accounts:
    st.info("No hay cuentas. Crea una en el panel lateral.")
    st.stop()

account_options = {f"{a.get('name', 'Sin nombre')} ({a.get('currency', '')}) — {a.get('id', '')[:8]}": a for a in accounts}
selected_label = st.selectbox("Cuenta", list(account_options.keys()))
selected_account = account_options[selected_label]
account_id = selected_account.get("id")

col_bal, col_cur, col_id = st.columns(3)
col_bal.metric("Saldo", f"{selected_account.get('balance', 0):,.2f} {selected_account.get('currency', '')}")
col_cur.metric("Moneda", selected_account.get("currency", ""))
col_id.metric("ID", str(account_id)[:8] + "...")

st.divider()


with st.expander("+ Nueva transacción", expanded=False):
    with st.form("new_tx"):
        col1, col2 = st.columns(2)
        with col1:
            tx_amount = st.number_input("Importe", min_value=0.01, value=100.0, step=10.0)
            tx_type = st.selectbox("Tipo", ["credit", "debit"])
        with col2:
            tx_desc = st.text_input("Descripción")
            tx_cat = st.selectbox("Categoría", ["income", "transfer", "payment", "withdrawal", "food", "utilities", "other"])

        if st.form_submit_button("Registrar transacción", use_container_width=True, type="primary"):
            result = client.create_transaction(account_id, tx_amount, tx_type, tx_desc, tx_cat)
            if result:
                st.success(f"Transacción registrada: {result.get('id', '')[:8]}")
                st.rerun()
            else:
                st.error("Error al registrar la transacción.")


transactions = client.list_transactions(account_id)
transactions = transactions if isinstance(transactions, list) else []

if not transactions:
    st.info("No hay transacciones en esta cuenta.")
    st.stop()

df = pd.DataFrame([{
    "Fecha": t.get("created_at", "")[:10],
    "Descripción": t.get("description", ""),
    "Categoría": t.get("category", ""),
    "Tipo": t.get("type", ""),
    "Importe": t.get("amount", 0),
} for t in transactions])

df["Importe €"] = df.apply(
    lambda r: r["Importe"] if r["Tipo"] == "credit" else -r["Importe"], axis=1
)

col_table, col_chart = st.columns([1.4, 1])

with col_table:
    st.subheader("Historial")
    st.dataframe(
        df[["Fecha", "Descripción", "Categoría", "Tipo", "Importe"]],
        use_container_width=True,
        hide_index=True,
    )

with col_chart:
    st.subheader("Por categoría")
    cat_df = df.groupby("Categoría")["Importe"].sum().reset_index()
    fig = px.pie(cat_df, names="Categoría", values="Importe", hole=0.4)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", font_color="#F1F5F9")
    st.plotly_chart(fig, use_container_width=True)


summary = client.monthly_summary(account_id)
if summary and isinstance(summary, dict):
    st.subheader("Resumen mensual")
    if isinstance(summary, list):
        s_df = pd.DataFrame(summary)
        st.dataframe(s_df, use_container_width=True, hide_index=True)
    else:
        cols = st.columns(len(summary))
        for col, (k, v) in zip(cols, summary.items()):
            col.metric(k.replace("_", " ").title(), v)
