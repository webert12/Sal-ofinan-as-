import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import json

# Configuração da página
st.set_page_config(page_title="Gestão Financeira - Salão", layout="wide", page_icon="✂️")

USUARIOS_FILE = "usuarios.json"

# --- CONFIGURAÇÃO DO ADMINISTRADOR MESTRE (VOCÊ) ---
# Altere aqui o seu usuário e senha de criador do sistema:
ADMIN_MESTRE_USER = "admin"
ADMIN_MESTRE_PASS = "master2026"

# --- FUNÇÕES DE GERENCIAMENTO DE USUÁRIOS (SALÕES) ---
def carregar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r") as f:
            return json.load(f)
    # Lista inicial caso o arquivo não exista
    usuarios_padrao = {
        "salao_central": "admin123",
        "barbearia_vanguard": "corte2026"
    }
    with open(USUARIOS_FILE, "w") as f:
        json.dump(usuarios_padrao, f, indent=4)
    return usuarios_padrao

def salvar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w") as f:
        json.dump(usuarios, f, indent=4)

# --- FUNÇÕES DE PERSISTÊNCIA DE DADOS ISOLADOS POR USUÁRIO ---
def obter_nomes_arquivos():
    usuario = st.session_state.usuario_logado
    return f"servicos_{usuario}.json", f"fluxo_caixa_{usuario}.csv"

def carregar_servicos():
    servicos_file, _ = obter_nomes_arquivos()
    if os.path.exists(servicos_file):
        with open(servicos_file, "r") as f:
            return json.load(f)
    return {
        "Corte de Cabelo": 25.00,
        "Barba": 25.00,
        "Combo Cabelo e Barba": 50.00
    }

def salvar_servicos(servicos):
    servicos_file, _ = obter_nomes_arquivos()
    with open(servicos_file, "w") as f:
        json.dump(servicos, f, indent=4)

def carregar_fluxo():
    _, fluxo_file = obter_nomes_arquivos()
    if os.path.exists(fluxo_file):
        try:
            df = pd.read_csv(fluxo_file)
            df['Data'] = pd.to_datetime(df['Data'])
            return df
        except Exception:
            return pd.DataFrame(columns=["Data", "Tipo", "Descrição", "Valor"])
    return pd.DataFrame(columns=["Data", "Tipo", "Descrição", "Valor"])

def salvar_fluxo(df):
    _, fluxo_file = obter_nomes_arquivos()
    df.to_csv(fluxo_file, index=False)

# --- CONTROLE DE SESSÃO E LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = None
if 'eh_admin' not in st.session_state:
    st.session_state.eh_admin = False

usuarios_cadastrados = carregar_usuarios()

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.title("✂️ Sistema de Gestão - Login")
    st.markdown("---")
    
    with st.form("form_login"):
        st.subheader("Acesse seu Painel")
        usuario_input = st.text_input("Usuário do Salão ou ADM:").strip().lower()
        senha_input = st.text_input("Senha:", type="password")
        botao_entrar = st.form_submit_button("Entrar no Sistema")
        
        if botao_entrar:
            # Verifica primeiro se é o Administrador do Sistema
            if usuario_input == ADMIN_MESTRE_USER and senha_input == ADMIN_MESTRE_PASS:
                st.session_state.autenticado = True
                st.session_state.usuario_logado = "Administrador"
                st.session_state.eh_admin = True
                st.success("Acesso master concedido!")
                st.rerun()
            
            # Se não for o ADM, verifica se é um salão cliente cadastrado
            elif usuario_input in usuarios_cadastrados and usuarios_cadastrados[usuario_input] == senha_input:
                st.session_state.autenticado = True
                st.session_state.usuario_logado = usuario_input
                st.session_state.eh_admin = False
                
                # Inicializa as variáveis específicas deste salão
                st.session_state.servicos = carregar_servicos()
                st.session_state.fluxo_caixa = carregar_fluxo()
                
                st.success(f"Carregando painel de {usuario_input}...")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. Verifique suas credenciais.")
    st.stop()

# =====================================================================
# --- INTERFACE 1: PAINEL DO ADMINISTRADOR MESTRE (GERENCIAR CLIENTES) ---
# =====================================================================
if st.session_state.eh_admin:
    st.title("👑 Central do Administrador - Gestão de Clientes")
    st.markdown("Aqui você cadastra novos salões e gerencia os acessos do seu sistema.")
    st.markdown("---")
    
    col_cad, col_lista = st.columns([1, 1])
    
    with col_cad:
        st.subheader("➕ Registrar Novo Salão Cliente")
        with st.form("form_cadastro_cliente"):
            # Evitar espaços e caracteres especiais no nome do usuário para não quebrar nomes de arquivos
            novo_usuario = st.text_input("Identificador/Usuário do Salão:", help="Ex: salao_do_bairro (Use apenas letras, números e _ )").strip().lower()
            nova_senha = st.text_input("Senha de Acesso:", type="password").strip()
            
            btn_cadastrar = st.form_submit_button("Criar Conta do Salão", type="primary")
            
            if btn_cadastrar:
                if not novo_usuario or not nova_senha:
                    st.error("Preencha todos os campos para cadastrar.")
                elif novo_usuario in usuarios_cadastrados or novo_usuario == ADMIN_MESTRE_USER:
                    st.error("Este nome de usuário já está sendo utilizado.")
                else:
                    usuarios_cadastrados[novo_usuario] = nova_senha
                    salvar_usuarios(usuarios_cadastrados)
                    st.success(f"Sucesso! O salão '{novo_usuario}' já pode acessar o sistema.")
                    st.rerun()
                    
    with col_lista:
        st.subheader("👥 Salões Ativos no Sistema")
        
        # Converte o dicionário em DataFrame para exibição limpa
        df_usuarios = pd.DataFrame(list(usuarios_cadastrados.items()), columns=["Usuário / Salão", "Senha de Acesso"])
        st.dataframe(df_usuarios, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🗑️ Remover Acesso de um Salão")
        salao_remover = st.selectbox("Selecione o salão que deseja deletar:", ["Selecione..."] + list(usuarios_cadastrados.keys()))
        
        if st.button("Excluir Conta Permanentemente", type="primary"):
            if salao_remover != "Selecione...":
                del usuarios_cadastrados[salao_remover]
                salvar_usuarios(usuarios_cadastrados)
                st.warning(f"O acesso do salão '{salao_remover}' foi deletado.")
                st.rerun()
            else:
                st.error("Selecione um salão válido para remover.")

    # Botão de Logout fixo na barra lateral para o Admin
    with st.sidebar:
        st.header("Painel Master")
        st.info("Você está logado como Administrador Geral.")
        if st.button("🚪 Sair do Modo ADM", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.usuario_logado = None
            st.session_state.eh_admin = False
            st.rerun()
    st.stop()


# =====================================================================
# --- INTERFACE 2: PAINEL EXCLUSIVO DO CLIENTE (SALÃO INDIVIDUAL) ----
# =====================================================================

# Título do App customizado com o nome do salão atual
nome_salao_formatado = st.session_state.usuario_logado.replace("_", " ").title()
st.title(f"✂️ {nome_salao_formatado} - Gestão Financeira")
st.markdown(f"*Painel exclusivo e isolado de dados*")
st.markdown("---")

# --- SIDEBAR: GERENCIAR SERVIÇOS (CRIAÇÃO E EDIÇÃO) ---
with st.sidebar:
    st.header("⚙️ Configurações de Serviços")
    st.markdown("Selecione um serviço para alterar ou escolha criar um novo.")
    
    opcoes_gerenciamento = ["➕ Cadastrar Novo Serviço"] + list(st.session_state.servicos.keys())
    servico_selecionado_gerenciar = st.selectbox("Escolha uma ação:", opcoes_gerenciamento, key="sb_gerenciar_servicos")
    
    if servico_selecionado_gerenciar == "➕ Cadastrar Novo Serviço":
        nome_padrao = ""
        preco_padrao = 0.0
        botao_label = "Cadastrar Serviço"
    else:
        nome_padrao = servico_selecionado_gerenciar
        preco_padrao = float(st.session_state.servicos[servico_selecionado_gerenciar])
        botao_label = "Salvar Alterações"
        
    novo_servico = st.text_input("Nome do Serviço:", value=nome_padrao, key=f"input_nome_{servico_selecionado_gerenciar}")
    novo_preco = st.number_input("Preço (R$):", min_value=0.0, value=preco_padrao, step=5.0, key=f"input_preco_{servico_selecionado_gerenciar}")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button(botao_label, type="primary", key=f"btn_salvar_{servico_selecionado_gerenciar}"):
            if novo_servico:
                if servico_selecionado_gerenciar != "➕ Cadastrar Novo Serviço" and servico_selecionado_gerenciar != novo_servico:
                    if servico_selecionado_gerenciar in st.session_state.servicos:
                        del st.session_state.servicos[servico_selecionado_gerenciar]
                
                st.session_state.servicos[novo_servico] = novo_preco
                salvar_servicos(st.session_state.servicos)
                st.success("Serviço atualizado!")
                st.rerun()
            else:
                st.error("O nome do serviço não pode ser vazio.")
                
    with col_btn2:
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
        
    # Botão de Logout para permitir trocar de salão com segurança
    st.markdown("---")
    if st.button("🚪 Sair do Painel", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_logado = None
        st.session_state.eh_admin = False
        st.rerun()

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
    
    ent_dia = df_diario[df_diario['Tipo'] == 'Entrada']['Valor'].sum()
    sai_dia = df_diario[df_diario['Tipo'] == 'Saída']['Valor'].sum()
    lucro_dia = ent_dia + sai_dia
    
    ent_sem = df_semanal[df_semanal['Tipo'] == 'Entrada']['Valor'].sum()
    sai_sem = df_semanal[df_semanal['Tipo'] == 'Saída']['Valor'].sum()
    lucro_sem = ent_sem + sai_sem
    
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
            df_exibicao = df_exibicao.sort_index(ascending=False)
            
            df_visualizacao = df_exibicao.copy()
            df_visualizacao['Data'] = df_visualizacao['Data'].dt.strftime('%d/%m/%Y')
            df_visualizacao = df_visualizacao.drop(columns=['Mês/Ano'])
            
            # FUNÇÃO DE ESTILIZAÇÃO DAS LINHAS
            def colorir_linhas(row):
                if row['Tipo'] == 'Entrada':
                    return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
                elif row['Tipo'] == 'Saída':
                    return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)
                return [''] * len(row)
            
            # FORMATO CORRIGIDO DE VALOR MONETÁRIO
            tabela_estilizada = df_visualizacao.style.apply(colorir_linhas, axis=1).format(
                subset=["Valor"], 
                formatter=lambda x: f"R$ {x:.2f}".replace('.', ',')
            )
            
            st.dataframe(tabela_estilizada, use_container_width=True)
        else:
            st.info("Nenhum registro encontrado para este mês.")
    else:
        st.info("Nenhuma movimentação registrada até o momento.")
