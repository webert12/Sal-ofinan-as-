import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(page_title="Gestão Financeira - Salão", layout="wide", page_icon="✂️")

# --- INICIALIZAÇÃO DO BANCO DE DADOS EM MEMÓRIA ---
# (Usando st.session_state para manter os dados enquanto a aba estiver aberta)
if 'servicos' not in st.session_state:
    st.session_state.servicos = {
        "Corte de Cabelo": 25.00,
        "Barba": 25.00,
        "Combo Cabelo e Barba": 50.00
    }

if 'fluxo_caixa' not in st.session_state:
    # Dados iniciais para exemplo
    st.session_state.fluxo_caixa = pd.DataFrame(columns=["Data", "Tipo", "Descrição", "Valor"])

# Título do App
st.title("✂️ Barber & Hair - Gestão Financeira")
st.markdown("---")

# --- SIDEBAR: GERENCIAR SERVIÇOS ---
st.sidebar.header("⚙️ Configurações de Serviços")
st.sidebar.markdown("Altere os valores ou adicione novos serviços.")

# Editar/Adicionar Serviço
novo_servico = st.sidebar.text_input("Nome do Serviço:")
novo_preco = st.sidebar.number_input("Preço (R$):", min_value=0.0, step=5.0)

if st.sidebar.button("Salvar/Atualizar Serviço"):
    if novo_servico:
        st.sidebar.success(f"Serviço '{novo_servico}' atualizado para R$ {novo_preco:.2f}!")
    else:
        st.sidebar.error("Digite o nome do serviço.")

# Listar serviços atuais na sidebar para consulta
st.sidebar.markdown("### Serviços Cadastrados")
for serv, preco in st.session_state.servicos.items():
    st.sidebar.text(f"• {serv}: R$ {preco:.2f}")

# --- ABAS DA TELA PRINCIPAL ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💰 Lançar Movimentação", "📜 Histórico de Caixa"])

# --- TAB 2: LANÇAR MOVIMENTAÇÃO (Feito primeiro para lógica de dados) ---
with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Entrada (Atendimento ao Cliente)")
        servico_selecionado = st.selectbox("Selecione o Serviço realizado:", list(st.session_state.servicos.keys()))
        # Busca o preço atual do serviço selecionado
        preco_sugerido = st.session_state.servicos[servico_selecionado]
        
        # Permite alterar o preço na hora se houver algum desconto/acréscimo
        preco_final = st.number_input("Valor Cobrado (R$):", value=preco_sugerido, step=1.0, key="entrada_val")
        data_entrada = st.date_input("Data do Atendimento:", datetime.now(), key="entrada_data")
        
        if st.button("Registrar Entrada"):
            nova_linha = pd.DataFrame([{
                "Data": pd.to_datetime(data_entrada),
                "Tipo": "Entrada",
                "Descrição": f"Atendimento: {servico_selecionado}",
                "Valor": preco_final
            }])
            st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True)
            st.success("Entrada registrada com sucesso!")

    with col2:
        st.subheader("📤 Saída (Pagamento de Despesas)")
        descricao_saida = st.text_input("Descrição da Despesa (Ex: Luz, Aluguel, Água):")
        valor_saida = st.number_input("Valor da Despesa (R$):", min_value=0.0, step=5.0, key="saida_val")
        data_saida = st.date_input("Data do Pagamento:", datetime.now(), key="saida_data")
        
        if st.button("Registrar Saída", type="primary"):
            if descricao_saida and valor_saida > 0:
                nova_linha = pd.DataFrame([{
                    "Data": pd.to_datetime(data_saida),
                    "Tipo": "Saída",
                    "Descrição": descricao_saida,
                    "Valor": -valor_saida  # Salva como negativo para facilitar as somas
                }])
                st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True)
                st.success("Despesa registrada com sucesso!")
            else:
                st.error("Preencha a descrição e o valor da despesa.")

# --- LÓGICA DE CÁLCULO DOS GANHOS (D/W/M) ---
df = st.session_state.fluxo_caixa.copy()
if not df.empty:
    df['Data'] = pd.to_datetime(df['Data'])
    hoje = pd.Timestamp(datetime.now().date())
    
    # Filtros temporais
    df_diario = df[df['Data'].dt.date == hoje.date()]
    df_semanal = df[df['Data'] >= (hoje - timedelta(days=7))]
    df_mensal = df[df['Data'].dt.month == hoje.month]
    
    # Cálculos Diários
    ent_dia = df_diario[df_diario['Tipo'] == 'Entrada']['Valor'].sum()
    sai_dia = df_diario[df_diario['Tipo'] == 'Saída']['Valor'].sum()
    lucro_dia = ent_dia + sai_dia
    
    # Cálculos Semanais
    ent_sem = df_semanal[df_semanal['Tipo'] == 'Entrada']['Valor'].sum()
    sai_sem = df_semanal[df_semanal['Tipo'] == 'Saída']['Valor'].sum()
    lucro_sem = ent_sem + sai_sem
    
    # Cálculos Mensais
    ent_mes = df_mensal[df_mensal['Tipo'] == 'Entrada']['Valor'].sum()
    sai_mes = df_mensal[df_mensal['Tipo'] == 'Saída']['Valor'].sum()
    lucro_mes = ent_mes + sai_mes
else:
    ent_dia = sai_dia = lucro_dia = 0
    ent_sem = sai_sem = lucro_sem = 0
    ent_mes = sai_mes = lucro_mes = 0

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader("📊 Resumo Financeiro Real-Time")
    
    # Métricas em colunas
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.metric(label="Fechamento do Dia (Líquido)", value=f"R$ {lucro_dia:.2f}", delta=f"Entradas: R$ {ent_dia:.2f}")
    with m2:
        st.metric(label="Últimos 7 Dias (Líquido)", value=f"R$ {lucro_sem:.2f}", delta=f"Entradas: R$ {ent_sem:.2f}")
    with m3:
        st.metric(label="Mês Atual (Líquido)", value=f"R$ {lucro_mes:.2f}", delta=f"Entradas: R$ {ent_mes:.2f}")
        
    st.markdown("---")
    st.subheader("📈 Resumo de Entradas vs Saídas (Mês Atual)")
    
    dados_grafico = pd.DataFrame({
        "Categoria": ["Entradas", "Saídas"],
        "Total (R$)": [ent_mes, abs(sai_mes)]
    })
    st.bar_chart(data=dados_grafico, x="Categoria", y="Total (R$)", color="#29b6f6")

# --- TAB 3: HISTÓRICO DE CAIXA ---
with tab3:
    st.subheader("📜 Histórico Completo de Transações")
    if not df.empty:
        # Formatar a data para exibição mais amigável
        df_exibicao = df.copy()
        df_exibicao['Data'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_exibicao.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("Nenhuma movimentação registrada até o momento.")
