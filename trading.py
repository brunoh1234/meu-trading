import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="JAKOBA CLOUD", layout="wide", page_icon="🚀")

# --- CONEXÃO GOOGLE SHEETS ---
# A conexão será configurada no painel do Streamlit Cloud depois
conn = st.connection("gsheets", type=GSheetsConnection)


def carregar_dados():
    try:
        # Tenta ler os dados da planilha
        return conn.read(ttl=0)
    except Exception:
        # Se a planilha estiver vazia ou der erro, cria o DataFrame do zero
        return pd.DataFrame(columns=['Data', 'Ativo', 'Timeframe', 'Resultado', 'Lucro', 'Banca'])


st.title("📈 JAKOBA - Gestão Profissional na Nuvem")

# --- SIDEBAR: CONFIGURAÇÃO DE GESTÃO ---
with st.sidebar:
    st.header("⚙️ Configuração da Sessão")
    banca_input = st.number_input("Banca Inicial do Dia (€)", value=100.0, step=10.0)

    # Cálculos de Gestão (1% entrada, 10% Stop Loss)
    entrada_fixa = banca_input * 0.01
    meta_v = banca_input + (entrada_fixa * 3)
    stop_loss_v = banca_input - (banca_input * 0.1)

    st.divider()
    st.info(f"🎯 Entrada: {entrada_fixa:.2f} €")
    st.success(f"✅ Meta: {meta_v:.2f} €")
    st.error(f"🛑 Stop Loss: {stop_loss_v:.2f} €")

    st.divider()
    st.warning("Os dados são salvos automaticamente na sua Google Sheet.")

# --- CARREGAR HISTÓRICO ---
df = carregar_dados()

# Garantir que a coluna Banca é numérica
if not df.empty:
    df['Banca'] = pd.to_numeric(df['Banca'])
    df['Lucro'] = pd.to_numeric(df['Lucro'])
    banca_atual = df['Banca'].iloc[-1]
else:
    banca_atual = banca_input

# --- DASHBOARD DE MÉTRICAS ---
col1, col2, col3, col4 = st.columns(4)
lucro_total = banca_atual - banca_input
col1.metric("Banca Atual", f"{banca_atual:.2f} €", f"{lucro_total:.2f} €")
col2.metric("Meta", f"{meta_v:.2f} €")
col3.metric("Stop Loss", f"{stop_loss_v:.2f} €")
progresso = min(max((banca_atual - banca_input) / (meta_v - banca_input), 0.0), 1.0) if meta_v != banca_input else 0
col4.write(f"Progresso: {progresso * 100:.1f}%")
col4.progress(progresso)

# --- TRAVAS DE SEGURANÇA ---
if banca_atual >= meta_v:
    st.balloons()
    st.success("🏆 META ATINGIDA! PARE DE OPERAR.")
elif banca_atual <= stop_loss_v:
    st.error("🚨 STOP LOSS ATINGIDO! RESPEITE O SEU CAPITAL.")

# --- FORMULÁRIO DE ENTRADA ---
st.divider()
with st.expander("📝 Registar Nova Operação", expanded=True):
    f1, f2, f3, f4, f5 = st.columns(5)
    ativo = f1.text_input("Ativo", "EUR/USD OTC")
    tf = f2.selectbox("Timeframe", ["M1", "M5", "M15", "H1"])
    payout = f3.number_input("Payout (ex: 0.87)", value=0.87)
    res = f4.selectbox("Resultado", ["WIN", "LOSS", "EMPATE", "WIN GALE 1", "WIN GALE 2", "EMPATE GALE"])

    if st.button("🚀 Gravar Operação na Nuvem"):
        lucro = 0
        # Lógica de cálculo de lucro/perda
        if res == "WIN":
            lucro = entrada_fixa * payout
        elif res == "WIN GALE 1":
            lucro = (entrada_fixa * 2 * payout) - entrada_fixa
        elif res == "WIN GALE 2":
            lucro = (entrada_fixa * 4 * payout) - (entrada_fixa * 3)
        elif res == "LOSS":
            lucro = -(entrada_fixa * 7)  # Perda total 1 + 2 + 4
        elif res == "EMPATE":
            lucro = 0
        elif res == "EMPATE GALE":
            lucro = -entrada_fixa  # Empatou o Gale, mas perdeu a 1ª

        nova_banca = banca_atual + lucro

        # Criar nova linha
        novo_registro = pd.DataFrame([{
            'Data': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'Ativo': ativo,
            'Timeframe': tf,
            'Resultado': res,
            'Lucro': round(lucro, 2),
            'Banca': round(nova_banca, 2)
        }])

        # Atualizar Google Sheets
        df_atualizado = pd.concat([df, novo_registro], ignore_index=True)
        conn.update(data=df_atualizado)
        st.toast("✅ Registado com sucesso!")
        st.rerun()

# --- GRÁFICOS E TABELAS ---
st.divider()
tab1, tab2 = st.tabs(["📊 Evolução e Gráficos", "📋 Diário de Trades"])

with tab1:
    if not df.empty:
        st.subheader("Curva de Capital")
        st.line_chart(df.set_index('Data')['Banca'])

        st.subheader("Lucro por Dia")
        df['Apenas_Dia'] = pd.to_datetime(df['Data']).dt.date
        evolucao_dia = df.groupby('Apenas_Dia')['Lucro'].sum().reset_index()
        st.bar_chart(data=evolucao_dia, x='Apenas_Dia', y='Lucro')
    else:
        st.info("Aguardando operações para gerar gráficos.")

with tab2:
    if not df.empty:
        st.dataframe(df.sort_index(ascending=False), width="stretch")
    else:
        st.write("O histórico está vazio.")