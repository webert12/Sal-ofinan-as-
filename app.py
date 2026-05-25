import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import json

# Configuração da página
st.set_page_config(page_title="Gestão Financeira - Salão", layout="wide", page_icon="✂️")

# --- FUNÇÕES DE PERSISTÊNCIA DE DADOS (ARQUIVOS LOCAIS) ---
SERVICOS_FILE = "servicos.json"
FLUXO_FILE = "fluxo_caixa.csv"

def carregar_servicos():
    if os.path.exists(SERVICOS_FILE):
        with open(SERVICOS_FILE, "r") as f:
            return json.load(f)
    # Valores padrão caso o arquivo não exista
    return {
        "Corte de Cabelo": 25.00,
        "Barba": 25.00,
        "Combo Cabelo e Barba": 50.00
    }

def salvar_servicos(servicos):
    with open(SERVICOS_FILE, "w") as f:
        json.dump(servicos, f)

def carregar_fluxo():
    if os.path.exists(FLUXO_FILE):
        df = pd.read_csv(FLUXO_FILE)
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    return pd.DataFrame(columns=["Data", "Tipo", "Descrição", "Valor"])

def salvar_fluxo(df):
    df.to_csv(FLUXO_FILE, index=False)

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
if 'servicos' not in st.session_state:
    st.session_state.servicos = carregar_servicos()

if 'fluxo_caixa' not in st.session_state:
    st.session_state.fluxo_caixa = carregar_fluxo()

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
        # CORREÇÃO: Agora salva de verdade no dicionário e grava no arquivo json
        st.session_state.servicos[novo_servico] = novo_preco
        salvar_servicos(st.session_state.servicos)
        st.sidebar.success(f"Serviço '{novo_servico}' atualizado para R$ {novo_preco:.2f}!")
        st.rerun() # Atualiza a tela para aplicar nos menus de seleção
    else:
        st.sidebar.error("Digite o nome do serviço.")

# Listar serviços atuais na sidebar para consulta
st.sidebar.markdown("### Serviços Cadastrados")
for serv, preco in st.session_state.servicos.items():
    st.sidebar.text(f"• {serv}: R$ {preco:.2f}")

# --- ABAS DA TELA PRINCIPAL ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💰 Lançar Movimentação", "📜 Histórico de Caixa"])

# --- TAB 2: LANÇAR MOVIMENTAÇÃO ---
with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Entrada (Atendimento ao Cliente)")
        servico_selecionado = st.selectbox("Selecione o Serviço realizado:", list(st.session_state.servicos.keys()))
        preco_sugerido = st.session_state.servicos[servico_selecionado]
        
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
            salvar_fluxo(st.session_state.fluxo_caixa) # Salva no arquivo CSV permanente
            st.success("Entrada registrada com sucesso!")
            st.rerun()

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
                    "Valor": -valor_saida  
                }])
                st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True)
                salvar_fluxo(st.session_state.fluxo_caixa) # Salva no arquivo CSV permanente
                st.success("Despesa registrada com sucesso!")
                st.rerun()
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
        # FUNÇÃO ADICIONADA: Criação do filtro por Mês/Ano
        df_filtro = df.copy()
        df_filtro['Mês/Ano'] = df_filtro['Data'].dt.strftime('%m/%Y')
        
        # Agrupa os meses únicos existentes no banco para colocar no menu de escolha
        meses_disponiveis = sorted(df_filtro['Mês/Ano'].unique(), reverse=True)
        opcoes_filtro = ["Ver Tudo"] + meses_disponiveis
        
        mes_escolhido = st.selectbox("📅 Selecione o mês que deseja consultar:", opciones_filtro)
        
        # Filtra a tabela conforme a escolha do usuário
        if mes_escolhido != "Ver Tudo":
            df_exibicao = df_filtro[df_filtro['Mês/Ano'] == mes_escolhido].copy()
        else:
            df_exibicao = df_filtro.copy()
            
        if not df_exibicao.empty:
            # Formata a data para leitura humana antes de exibir
            df_exibicao['Data'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
            # Remove a coluna auxiliar do filtro para limpar o visual
            df_exibicao = df_exibicao.drop(columns=['Mês/Ano'])
            
            st.dataframe(df_exibicao.sort_index(ascending=False), use_container_width=True)
        else:
            st.info("Nenhum registro encontrado para este mês.")
    else:
        st.info("Nenhuma movimentação registrada até o momento.")
