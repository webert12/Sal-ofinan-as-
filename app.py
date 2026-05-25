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
        try:
            df = pd.read_csv(FLUXO_FILE)
            df['Data'] = pd.to_datetime(df['Data'])
            return df
        except Exception:
            return pd.DataFrame(columns=["Data", "Tipo", "Descrição", "Valor"])
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

# --- SIDEBAR: GERENCIAR SERVIÇOS (CRIAÇÃO E EDIÇÃO) ---
with st.sidebar:
    st.header("⚙️ Configurações de Serviços")
    st.markdown("Selecione um serviço para alterar ou escolha criar um novo.")
    
    # Menu para escolher se vai criar ou editar um existente
    opcoes_gerenciamento = ["➕ Cadastrar Novo Serviço"] + list(st.session_state.servicos.keys())
    servico_selecionado_gerenciar = st.selectbox("Escolha uma ação:", opcoes_gerenciamento, key="sb_gerenciar_servicos")
    
    # Define os valores iniciais dos campos baseado na escolha do usuário
    if servico_selecionado_gerenciar == "➕ Cadastrar Novo Serviço":
        nome_padrao = ""
        preco_padrao = 0.0
        botao_label = "Cadastrar Serviço"
    else:
        nome_padrao = servico_selecionado_gerenciar
        preco_padrao = float(st.session_state.servicos[servico_selecionado_gerenciar])
        botao_label = "Salvar Alterações"
        
    # Uso de chaves dinâmicas para atualizar os campos instantaneamente ao mudar o selectbox
    novo_servico = st.text_input("Nome do Serviço:", value=nome_padrao, key=f"input_nome_{servico_selecionado_gerenciar}")
    novo_preco = st.number_input("Preço (R$):", min_value=0.0, value=preco_padrao, step=5.0, key=f"input_preco_{servico_selecionado_gerenciar}")
    
    # Botões de Ação lado a lado
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button(botao_label, type="primary", key=f"btn_salvar_{servico_selecionado_gerenciar}"):
            if novo_servico:
                # Se o usuário alterou o nome de um serviço existente, remove o nome antigo para não duplicar
                if servico_selecionado_gerenciar != "➕ Cadastrar Novo Serviço" and servico_selecionado_gerenciar != novo_servico:
                    if servico_selecionado_gerenciar in st.session_state.servicos:
                        del st.session_state.servicos[servico_selecionado_gerenciar]
                
                # Salva os novos dados
                st.session_state.servicos[novo_servico] = novo_preco
                salvar_servicos(st.session_state.servicos)
                st.success("Serviço atualizado com sucesso!")
                st.rerun()
            else:
                st.error("O nome do serviço não pode ser vazio.")
                
    with col_btn2:
        # Só exibe o botão excluir se for um serviço já existente
        if servico_selecionado_gerenciar != "➕ Cadastrar Novo Serviço":
            if st.button("🗑️ Excluir", key=f"btn_deletar_{servico_selecionado_gerenciar}"):
                if servico_selecionado_gerenciar in st.session_state.servicos:
                    del st.session_state.servicos[servico_selecionado_gerenciar]
                salvar_servicos(st.session_state.servicos)
                st.warning("Serviço excluído!")
                st.rerun()

    st.markdown("---")
    st.markdown("### Lista de Valores Atuais")
    for serv, preco in st.session_state.servicos.items():
        st.text(f"• {serv}: R$ {preco:.2f}")

# --- ABAS DA TELA PRINCIPAL ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💰 Lançar Movimentação", "📜 Histórico de Caixa"])

# --- TAB 2: LANÇAR MOVIMENTAÇÃO ---
with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Entrada (Atendimento ao Cliente)")
        if list(st.session_state.servicos.keys()):
            servico_selecionado = st.selectbox("Selecione o Serviço realizado:", list(st.session_state.servicos.keys()), key="selectbox_servico_atendimento")
            preco_sugerido = st.session_state.servicos[servico_selecionado]
            
            preco_final = st.number_input("Valor Cobrado (R$):", value=preco_sugerido, step=1.0, key=f"entrada_val_{servico_selecionado}")
            data_entrada = st.date_input("Data do Atendimento:", datetime.now().date(), key="entrada_data")
            
            if st.button("Registrar Entrada"):
                nova_linha = pd.DataFrame([{
                    "Data": pd.to_datetime(data_entrada),
                    "Tipo": "Entrada",
                    "Descrição": f"Atendimento: {servico_selecionado}",
                    "Valor": preco_final
                }])
                st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True)
                salvar_fluxo(st.session_state.fluxo_caixa) 
                st.success("Entrada registrada com sucesso!")
                st.rerun()
        else:
            st.info("Cadastre pelo menos um serviço na barra lateral para registrar entradas.")

    with col2:
        st.subheader("📤 Saída (Pagamento de Despesas)")
        descricao_saida = st.text_input("Descrição da Despesa (Ex: Luz, Aluguel, Água):")
        valor_saida = st.number_input("Valor da Despesa (R$):", min_value=0.0, step=5.0, key="saida_val")
        data_saida = st.date_input("Data do Pagamento:", datetime.now().date(), key="saida_data")
        
        if st.button("Registrar Saída", type="primary"):
            if descricao_saida and valor_saida > 0:
                nova_linha = pd.DataFrame([{
                    "Data": pd.to_datetime(data_saida),
                    "Tipo": "Saída",
                    "Descrição": descricao_saida,
                    "Valor": -valor_saida  
                }])
                st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True)
                salvar_fluxo(st.session_state.fluxo_caixa) 
                st.success("Despesa registrada com sucesso!")
                st.rerun()
            else:
                st.error("Preencha a descrição e o valor da despesa.")

# --- LÓGICA DE CÁLCULO DOS GANHOS (D/W/M) ---
df = st.session_state.fluxo_caixa.copy()
if not df.empty:
    df['Data'] = pd.to_datetime(df['Data'])
    hoje = pd.Timestamp(datetime.now().date())
    
    df_limpo = df.dropna(subset=['Data'])
    df_diario = df_limpo[df_limpo['Data'].dt.date == hoje.date()]
    df_semanal = df_limpo[df_limpo['Data'] >= (hoje - timedelta(days=7))]
    df_mensal = df_limpo[df_limpo['Data'].dt.month == hoje.month]
    
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
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="Fechamento do Dia (Líquido)", value=f"R$ {lucro_dia:.2f}", delta=f"+ R$ {ent_dia:.2f} Entradas")
    with m2:
        st.metric(label="Últimos 7 Dias (Líquido)", value=f"R$ {lucro_sem:.2f}", delta=f"+ R$ {ent_sem:.2f} Entradas")
    with m3:
        st.metric(label="Mês Atual (Líquido)", value=f"R$ {lucro_mes:.2f}", delta=f"+ R$ {ent_mes:.2f} Entradas")
        
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
        df_filtro = df.dropna(subset=['Data']).copy()
        df_filtro['Mês/Ano'] = df_filtro['Data'].dt.strftime('%m/%Y')
        
        meses_puros = df_filtro['Mês/Ano'].dropna().unique()
        meses_disponiveis = sorted([str(m) for m in meses_puros if str(m).strip() and str(m) != 'nan'], reverse=True)
        
        opcoes_filtro = ["Ver Tudo"] + meses_disponiveis
        mes_escolhido = st.selectbox("📅 Selecione o mês que deseja consultar:", opcoes_filtro, key="selectbox_filtro_mes_historico")
        
        if mes_escolhido != "Ver Tudo":
            df_exibicao = df_filtro[df_filtro['Mês/Ano'] == mes_escolhido].copy()
        else:
            df_exibicao = df_filtro.copy()
            
        if not df_exibicao.empty:
            # Ordena os lançamentos mais recentes primeiro
            df_exibicao = df_exibicao.sort_index(ascending=False)
            
            # Formata a data de visualização
            df_visualizacao = df_exibicao.copy()
            df_visualizacao['Data'] = df_visualizacao['Data'].dt.strftime('%d/%m/%Y')
            df_visualizacao = df_visualizacao.drop(columns=['Mês/Ano'])
            
            # FUNÇÃO DE ESTILIZAÇÃO: Define cores de fundo para as linhas (verde para entrada, vermelho para saída)
            def colorir_linhas(row):
                if row['Tipo'] == 'Entrada':
                    return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
                elif row['Tipo'] == 'Saída':
                    return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)
                return [''] * len(row)
            
            # Renderiza a tabela aplicando o estilo CSS dinâmico
            st.dataframe(df_visualizacao.style.apply(colorir_linhas, axis=1), use_container_width=True)
        else:
            st.info("Nenhum registro encontrado para este mês.")
    else:
        st.info("Nenhuma movimentação registrada até o momento.")
