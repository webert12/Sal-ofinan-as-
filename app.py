import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Importação necessária para o fuso horário
import os
import json

# --- CONFIGURAÇÃO DE FUSO HORÁRIO ---
TZ = ZoneInfo("America/Sao_Paulo")

# Configuração da página
st.set_page_config(page_title="Gestão Financeira - Salão", layout="wide", page_icon="✂️")

# --- CARREGAMENTO DE FONTES E CSS PERSONALIZADO ---
# Carregar FontAwesome para os ícones
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">', unsafe_allow_html=True)

# CSS personalizado para emular o design da imagem
st.markdown("""
<style>
    /* Estilos globais para tema escuro */
    body {
        background-color: #121212;
        color: white;
    }
    .stApp {
        background-color: #121212;
    }
    
    /* Simulação de cabeçalho */
    .sim-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #333;
        margin-bottom: 20px;
    }
    .sim-header-title {
        color: #d4af37; /* Dourado */
        font-weight: bold;
        font-size: 1.2rem;
    }
    .sim-header-icons {
        color: white;
        font-size: 1.2rem;
    }
    
    /* Container principal de Ações Rápidas */
    .fast-actions-container {
        background-color: #1a1d21; /* Fundo escuro dos cartões */
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Título "Ações rápidas" e linha dourada */
    .fast-actions-header {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .fast-actions-title {
        color: white;
        font-weight: bold;
        font-size: 1rem;
        margin-right: 10px;
    }
    .fast-actions-line {
        flex-grow: 1;
        height: 2px;
        background-color: #d4af37; /* Linha dourada */
    }
    
    /* Estilo de cada item de ação rápida */
    .fast-action-item {
        background-color: #22252a; /* Fundo de cada item */
        border-radius: 8px;
        padding: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
        cursor: pointer;
        transition: background-color 0.3s;
        border: 1px solid #333;
    }
    
    /* Efeito de hover nos cartões */
    .fast-action-item:hover {
        background-color: #333; /* Fundo mais claro ao passar o mouse */
    }
    
    /* Ícone dourado à esquerda */
    .fast-action-icon {
        color: #d4af37; /* Ícone dourado */
        font-size: 1.2rem;
        margin-right: 15px;
    }
    
    /* Texto branco */
    .fast-action-text {
        color: white;
        font-weight: 500;
        font-size: 0.9rem;
        flex-grow: 1; /* Para centralizar o texto */
        text-align: left; /* Alinhado à esquerda como na imagem */
    }
    
    /* Chevron dourado à direita */
    .fast-action-chevron {
        color: #d4af37; /* Seta dourada */
        font-size: 1rem;
    }
    
    /* Resetar estilos de link padrão nos cartões */
    .fast-action-item-link {
        text-decoration: none;
        color: inherit;
        display: block; /* Para o link ocupar todo o cartão */
    }

    /* Ocultar os expansores padrão do Streamlit para um visual mais limpo */
    .st-expander {
        border: none !important;
        box-shadow: none !important;
    }
    .st-expander-label {
        display: none !important;
    }
    
</style>
""", unsafe_allow_html=True)

# Funções auxiliares para renderizar os cartões de ação rápida
def renderizar_acao_rapida(icon_class, text, query_param):
    """Renderiza um cartão de ação rápida clicável com HTML e CSS personalizado."""
    # Cria o link de query parameter para recarregar a página e acionar a ação
    query_link = f"{st.query_params['base_url']}?action={query_param}" if 'base_url' in st.query_params else f"/?action={query_param}"
    return f"""
    <a href="{query_link}" class="fast-action-item-link" target="_self">
        <div class="fast-action-item">
            <i class="{icon_class} fast-action-icon"></i>
            <span class="fast-action-text">{text}</span>
            <i class="fa fa-chevron-right fast-action-chevron"></i>
        </div>
    </a>
    """

# --- INICIALIZAÇÃO E PROCESSAMENTO DE PARÂMETROS DE QUERY ---
# Inicializar parâmetros de query para detectar cliques
if 'action' not in st.query_params:
    st.query_params['action'] = 'none'

# Definir o formulário ativo com base no parâmetro de query
if 'formulario_ativo' not in st.session_state:
    st.session_state.formulario_ativo = 'none'

if st.query_params['action'] != 'none':
    st.session_state.formulario_ativo = st.query_params['action']
    # Resetar o parâmetro de query para evitar loops e recarregamentos
    st.query_params['action'] = 'none'

# Obter a URL base da aplicação
if 'base_url' not in st.session_state:
    # Em produção, st.query_params['base_url'] é preenchido pelo Streamlit
    # Localmente, definimos um fallback para "/"
    st.session_state.base_url = "/"
if 'base_url' not in st.query_params:
    st.query_params['base_url'] = st.session_state.base_url

# Definir a URL de query base para os links
url_base_query = f"{st.query_params['base_url']}?action="

# --- CONFIGURAÇÃO DE FUSO HORÁRIO E ARQUIVOS (MANTIDO) ---
TZ = ZoneInfo("America/Sao_Paulo")
USUARIOS_FILE = "usuarios.json"
ADMIN_MESTRE_USER = "admin"
ADMIN_MESTRE_PASS = "master2026"

# --- FUNÇÕES DE GERENCIAMENTO DE USUÁRIOS E DADOS (MANTIDO) ---
def carregar_usuarios():
    vencimento_padrao = (datetime.now(TZ) + timedelta(days=30)).strftime("%Y-%m-%d")
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r") as f:
            dados = json.load(f)
        usuarios_atualizados = {}
        modificado = False
        for k, v in dados.items():
            if isinstance(v, str):
                usuarios_atualizados[k] = {
                    "senha": v,
                    "tipo": "Cliente",
                    "vencimento": vencimento_padrao,
                    "status": "Ativo"
                }
                modificado = True
            else:
                usuarios_atualizados[k] = v
        if modificado:
            salvar_usuarios(usuarios_atualizados)
        return usuarios_atualizados
    usuarios_padrao = {
        "salao_central": {
            "senha": "admin123",
            "tipo": "Cliente",
            "vencimento": vencimento_padrao,
            "status": "Ativo"
        },
        "barbearia_vanguard": {
            "senha": "corte2026",
            "tipo": "Teste",
            "vencimento": (datetime.now(TZ) + timedelta(days=7)).strftime("%Y-%m-%d"),
            "status": "Ativo"
        }
    }
    with open(USUARIOS_FILE, "w") as f:
        json.dump(usuarios_padrao, f, indent=4)
    return usuarios_padrao

def salvar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w") as f:
        json.dump(usuarios, f, indent=4)

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

# --- CONTROLE DE SESSÃO E LOGIN (MANTIDO) ---
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
            if usuario_input == ADMIN_MESTRE_USER and senha_input == ADMIN_MESTRE_PASS:
                st.session_state.autenticado = True
                st.session_state.usuario_logado = "Administrador"
                st.session_state.eh_admin = True
                st.success("Acesso master concedido!")
                st.rerun()
            elif usuario_input in usuarios_cadastrados and usuarios_cadastrados[usuario_input]["senha"] == senha_input:
                dados_user = usuarios_cadastrados[usuario_input]
                data_vencimento = datetime.strptime(dados_user["vencimento"], "%Y-%m-%d").date()
                hoje = datetime.now(TZ).date()
                if hoje > data_vencimento or dados_user.get("status") == "Suspenso":
                    st.error(f"❌ ACESSO BLOQUEADO! O período de {dados_user['tipo']} venceu em {data_vencimento.strftime('%d/%m/%Y')}. Entre em contato com o suporte para renovação.")
                    st.stop()
                st.session_state.autenticado = True
                st.session_state.usuario_logado = usuario_input
                st.session_state.eh_admin = False
                st.session_state.servicos = carregar_servicos()
                st.session_state.fluxo_caixa = carregar_fluxo()
                st.success(f"Carregando painel de {usuario_input}...")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. Verifique suas credenciais.")
    st.stop()

# =====================================================================
# --- INTERFACE 1: PAINEL DO ADMINISTRADOR MESTRE (MANTIDO) ---
# =====================================================================
if st.session_state.eh_admin:
    st.title("👑 Central do Administrador - Gestão de Clientes & Licenças")
    st.markdown("---")
    col_cad, col_lista = st.columns([1, 1.2])
    with col_cad:
        st.subheader("➕ Registrar ou Renovar Salão")
        with st.form("form_cadastro_cliente"):
            novo_usuario = st.text_input("Identificador/Usuário do Salão:", help="Ex: salao_do_bairro").strip().lower()
            nova_senha = st.text_input("Senha de Acesso:", type="password").strip()
            tipo_conta = st.selectbox("Tipo de Conta:", ["Teste", "Cliente"])
            dias_validade = st.number_input("Dias de Acesso/Validade:", min_value=1, max_value=365, value=7 if tipo_conta == "Teste" else 30)
            btn_cadastrar = st.form_submit_button("Salvar / Atualizar Conta", type="primary")
            if btn_cadastrar:
                if not novo_usuario or not nova_senha: st.error("Preencha o usuário e senha para salvar.")
                elif novo_usuario == ADMIN_MESTRE_USER: st.error("Nome reservado do sistema.")
                else:
                    vencimento_calculado = (datetime.now(TZ) + timedelta(days=dias_validade)).strftime("%Y-%m-%d")
                    usuarios_cadastrados[novo_usuario] = {"senha": nova_senha, "tipo": tipo_conta, "vencimento": vencimento_calculado, "status": "Ativo"}
                    salvar_usuarios(usuarios_cadastrados); st.success(f"Sucesso! Salão '{novo_usuario}' configurado."); st.rerun()
    with col_lista:
        st.subheader("👥 Salões Cadastrados")
        lista_formatada = []
        for user, info in usuarios_cadastrados.items():
            dt_venc = datetime.strptime(info['vencimento'], "%Y-%m-%d").date()
            lista_formatada.append({"Salão / Usuário": user, "Tipo": info["tipo"], "Vencimento": dt_venc.strftime("%d/%m/%Y"), "Situação": "Ativo" if datetime.now(TZ).date() <= dt_venc else "🔴 Expirado"})
        df_usuarios = pd.DataFrame(lista_formatada); st.dataframe(df_usuarios, use_container_width=True, hide_index=True)
    with st.sidebar:
        st.header("Painel Master")
        if st.button("🚪 Sair do Modo ADM", use_container_width=True): st.session_state.autenticado = False; st.session_state.usuario_logado = None; st.session_state.eh_admin = False; st.rerun()
    st.stop()


# =====================================================================
# --- INTERFACE 2: PAINEL EXCLUSIVO DO CLIENTE (MODIFICADO) ---
# =====================================================================
# Preparação dos dados para Dashboard e Histórico (movido para antes das abas)
df_fluxo_caixa = st.session_state.fluxo_caixa.copy()
if not df_fluxo_caixa.empty:
    df_fluxo_caixa['Data'] = pd.to_datetime(df_fluxo_caixa['Data'])
    hoje = pd.Timestamp(datetime.now(TZ).date())
    df_limpo = df_fluxo_caixa.dropna(subset=['Data'])
    df_diario = df_limpo[df_limpo['Data'].dt.date == hoje.date()]
    df_semanal = df_limpo[df_limpo['Data'] >= (hoje - timedelta(days=7))]
    df_mensal = df_limpo[df_limpo['Data'].dt.month == hoje.month]
    
    ent_dia, sai_dia = df_diario[df_diario['Tipo'] == 'Entrada']['Valor'].sum(), df_diario[df_diario['Tipo'] == 'Saída']['Valor'].sum()
    ent_sem, sai_sem = df_semanal[df_semanal['Tipo'] == 'Entrada']['Valor'].sum(), df_semanal[df_semanal['Tipo'] == 'Saída']['Valor'].sum()
    ent_mes, sai_mes = df_mensal[df_mensal['Tipo'] == 'Entrada']['Valor'].sum(), df_mensal[df_mensal['Tipo'] == 'Saída']['Valor'].sum()
    lucro_dia, lucro_sem, lucro_mes = ent_dia + sai_dia, ent_sem + sai_sem, ent_mes + sai_mes
else:
    ent_dia = sai_dia = lucro_dia = ent_sem = sai_sem = lucro_sem = ent_mes = sai_mes = lucro_mes = 0

# --- ABAS DA TELA PRINCIPAL (MODIFICADO: Aba "Lançamentos" integrada em "Início") ---
tab0, tab1, tab2 = st.tabs(["🚀 Início / Ações Rápidas", "📊 Dashboard", "📜 Histórico"])

# --- TAB 0: INÍCIO E AÇÕES RÁPIDAS (NOVO LAYOUT) ---
with tab0:
    # Simulação de cabeçalho
    st.markdown("""
    <div class="sim-header">
        <span class="sim-header-title">Fio&Caixa</span>
        <span class="sim-header-icons">
            <i class="fa fa-bell"></i>
            <i class="fa fa-user-circle"></i>
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Título "Ações rápidas" e linha dourada
    st.markdown("""
    <div class="fast-actions-header">
        <span class="fast-actions-title">Ações rápidas</span>
        <div class="fast-actions-line"></div>
    </div>
    """, unsafe_allow_html=True)

    # Container de Ações Rápidas
    st.markdown('<div class="fast-actions-container">', unsafe_allow_html=True)
    
    # Ícones que melhor se parecem com os da imagem
    icon_atendimento = "fa fa-scissors" # Tesoura para atendimento
    icon_venda = "fa fa-shopping-cart" # Carrinho para venda
    icon_receber = "fa fa-piggy-bank" # Cofrinho para receber (não tem o +)
    icon_pagar = "fa fa-hand-holding-usd" # Mão com dinheiro para pagar
    icon_relatorios = "fa fa-chart-bar" # Gráfico de barras para relatórios

    # Renderizar os cartões de ação rápida com parâmetros de query
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    with col_a:
        # Usamos st.query_params para criar links clicáveis que recarregam a página com o parâmetro 'action'
        # Em produção, st.query_params['base_url'] é preenchido automaticamente
        query_link = f"/?action=new_atendimento"
        st.markdown(renderizar_acao_rapida(icon_atendimento, "Novo atendimento", "new_atendimento"), unsafe_allow_html=True)
    with col_b:
        st.markdown(renderizar_acao_rapida(icon_venda, "Nova venda", "new_venda"), unsafe_allow_html=True)
    with col_c:
        st.markdown(renderizar_acao_rapida(icon_receber, "Contas a receber", "new_receber"), unsafe_allow_html=True)
    with col_d:
        st.markdown(renderizar_acao_rapida(icon_pagar, "Contas a pagar", "new_pagar"), unsafe_allow_html=True)
    with col_e:
        st.markdown(renderizar_acao_rapida(icon_relatorios, "Relatórios", "view_relatorios"), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # --- LÓGICA DE EXIBIÇÃO DE FORMULÁRIOS (Mover dos expansores) ---
    formulario_ativo = st.session_state.formulario_ativo

    if formulario_ativo == 'new_atendimento':
        st.subheader("📥 REGISTRAR ENTRADA (Atendimento Concluído e Pago)")
        if list(st.session_state.servicos.keys()):
            servico_selecionado = st.selectbox("Selecione o Serviço realizado:", list(st.session_state.servicos.keys()), key="selectbox_servico_atendimento_fast")
            preco_final = st.number_input("Valor Cobrado (R$):", value=float(st.session_state.servicos[servico_selecionado]), step=1.0)
            data_entrada = st.date_input("Data do Atendimento:", datetime.now(TZ).date())
            if st.button("Confirmar e Lançar Entrada", type="primary"):
                nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_entrada), "Tipo": "Entrada", "Descrição": f"Atendimento: {servico_selecionado}", "Valor": preco_final}])
                st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa); st.success("Entrada financeira registrada!")
                # Resetar o estado após o lançamento
                st.session_state.formulario_ativo = 'none'; st.rerun()
        else: st.info("Cadastre pelo menos um serviço na barra lateral.")
        if st.button("Cancelar", key="cancel_atendimento"): st.session_state.formulario_ativo = 'none'; st.rerun()

    elif formulario_ativo == 'new_venda':
        st.subheader("📤 REGISTRAR SAÍDA (Pagamento de Contas e Custos)")
        descricao_saida = st.text_input("Descrição da Despesa (Ex: Luz, Aluguel, Produtos):")
        valor_saida = st.number_input("Valor da Despesa (R$):", min_value=0.0, step=5.0)
        data_saida = st.date_input("Data do Pagamento:", datetime.now(TZ).date())
        if st.button("Confirmar e Lançar Saída", type="primary"):
            if descricao_saida and valor_saida > 0:
                nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_saida), "Tipo": "Saída", "Descrição": descricao_saida, "Valor": -valor_saida}])
                st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa); st.success("Despesa lançada com sucesso!")
                st.session_state.formulario_ativo = 'none'; st.rerun()
            else: st.error("Preencha a descrição e o valor da despesa.")
        if st.button("Cancelar", key="cancel_venda"): st.session_state.formulario_ativo = 'none'; st.rerun()

    elif formulario_ativo == 'new_receber':
        st.subheader("⏳ REGISTRAR PENDÊNCIA (Corte / Serviço Fiado)")
        if list(st.session_state.servicos.keys()):
            nome_devedor = st.text_input("Nome do Cliente (Quem ficou devendo?):").strip()
            servico_pendente = st.selectbox("Selecione o Serviço feito:", list(st.session_state.servicos.keys()))
            preco_final_p = st.number_input("Valor Pendente (R$):", value=float(st.session_state.servicos[servico_pendente]), step=1.0)
            data_pendencia = st.date_input("Data da Realização:", datetime.now(TZ).date())
            if st.button("Salvar Registro de Fiado", type="primary"):
                if nome_devedor:
                    nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_pendencia), "Tipo": "Pendência", "Descrição": f"Fiado de: {nome_devedor} ({servico_pendente})", "Valor": preco_final_p}])
                    st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa); st.success(f"Pendência de {nome_devedor} anotada.")
                    st.session_state.formulario_ativo = 'none'; st.rerun()
                else: st.error("Por favor, preencha o nome do cliente.")
        else: st.info("Cadastre pelo menos um serviço na barra lateral.")
        if st.button("Cancelar", key="cancel_receber"): st.session_state.formulario_ativo = 'none'; st.rerun()

    elif formulario_ativo == 'new_pagar':
        st.subheader("✅ CONFIRMAR RECEBIMENTO DE FIADO (Dar Baixa)")
        df_pendencias = df_fluxo_caixa[df_fluxo_caixa['Tipo'] == 'Pendência']
        if not df_pendencias.empty:
            opcoes_pendentes = {f"{row['Descrição']} - R$ {abs(row['Valor']):.2f}": idx for idx, row in df_pendencias.iterrows()}
            pendencia_selecionada = st.selectbox("Selecione o cliente que está pagando agora:", list(opcoes_pendentes.keys()))
            if st.button("Baixar Débito e Registrar Entrada de Caixa", type="primary"):
                idx_alterar = opcoes_pendentes[pendencia_selecionada]
                st.session_state.fluxo_caixa.at[idx_alterar, 'Tipo'] = 'Entrada'
                st.session_state.fluxo_caixa.at[idx_alterar, 'Data'] = pd.to_datetime(datetime.now(TZ).date())
                st.session_state.fluxo_caixa.at[idx_alterar, 'Descrição'] = st.session_state.fluxo_caixa.at[idx_alterar, 'Descrição'].replace("Fiado de:", "Recebido Fiado:") + " [PAGO HOJE]"
                salvar_fluxo(st.session_state.fluxo_caixa); st.success("O valor foi migrado para as Entradas de hoje."); st.session_state.formulario_ativo = 'none'; st.rerun()
        else: st.info("Não existem contas fiadas em aberto no momento.")
        if st.button("Cancelar", key="cancel_pagar"): st.session_state.formulario_ativo = 'none'; st.rerun()
        
    elif formulario_ativo == 'view_relatorios':
        st.subheader("📊 Visualização de Relatórios")
        # Você pode adicionar relatórios mais detalhados aqui no futuro.
        # Por enquanto, mostramos apenas o resumo financeiro.
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Fechamento do Dia (Líquido)", value=f"R$ {lucro_dia:.2f}")
        with col2:
            st.metric(label="Mês Atual (Líquido)", value=f"R$ {lucro_mes:.2f}")
        if st.button("Fechar Relatórios", key="cancel_relatorios"): st.session_state.formulario_ativo = 'none'; st.rerun()

    else:
        st.info("Clique em uma ação rápida acima para iniciar.")

# --- SIDEBAR: GERENCIAR SERVIÇOS (MANTIDO) ---
with st.sidebar:
    st.header("⚙️ Configurações de Serviços")
    # ... (lógica de gerenciamento de serviços idêntica ao original) ...
    nome_salao_formatado = st.session_state.usuario_logado.replace("_", " ").title()
    st.title(f"✂️ {nome_salao_formatado}")
    dados_proprios = usuarios_cadastrados[st.session_state.usuario_logado]
    st.markdown(f"*Licença: **{dados_proprios['tipo']}** (Até {datetime.strptime(dados_proprios['vencimento'], '%Y-%m-%d').strftime('%d/%m/%Y')})*")
    st.markdown("---")
    opcoes_gerenciamento = ["➕ Cadastrar Novo Serviço"] + list(st.session_state.servicos.keys())
    servico_selecionado_gerenciar = st.selectbox("Escolha uma ação:", opcoes_gerenciamento)
    if servico_selecionado_gerenciar == "➕ Cadastrar Novo Serviço":
        nome_padrao = ""; preco_padrao = 0.0; botao_label = "Cadastrar Serviço"
    else:
        nome_padrao = servico_selecionado_gerenciar; preco_padrao = float(st.session_state.servicos[servico_selecionado_gerenciar]); botao_label = "Salvar Alterações"
    novo_servico = st.text_input("Nome do Serviço:", value=nome_padrao)
    novo_preco = st.number_input("Preço (R$):", min_value=0.0, value=preco_padrao, step=5.0)
    if st.button(botao_label, type="primary"):
        if novo_servico:
            if servico_selecionado_gerenciar != "➕ Cadastrar Novo Serviço": del st.session_state.servicos[servico_selecionado_gerenciar]
            st.session_state.servicos[novo_servico] = novo_preco; salvar_servicos(st.session_state.servicos); st.success("Serviço atualizado!"); st.rerun()
        else: st.error("Nome vazio.")
    if servico_selecionado_gerenciar != "➕ Cadastrar Novo Serviço" and st.button("🗑️ Excluir"):
        del st.session_state.servicos[servico_selecionado_gerenciar]; salvar_servicos(st.session_state.servicos); st.warning("Excluído!"); st.rerun()
    st.markdown("### Valores Atuais")
    for serv, preco in st.session_state.servicos.items(): st.text(f"• {serv}: R$ {preco:.2f}")
    if st.button("🚪 Sair do Painel", use_container_width=True): st.session_state.autenticado = False; st.session_state.usuario_logado = None; st.session_state.eh_admin = False; st.rerun()

# --- TAB 1: DASHBOARD (MANTIDO E AJUSTADO) ---
with tab1:
    st.subheader("📊 Resumo Financeiro Real-Time")
    m1, m2, m3 = st.columns(3)
    with m1: st.metric(label="Fechamento do Dia (Líquido)", value=f"R$ {lucro_dia:.2f}")
    with m2: st.metric(label="Últimos 7 Dias (Líquido)", value=f"R$ {lucro_sem:.2f}")
    with m3: st.metric(label="Mês Atual (Líquido)", value=f"R$ {lucro_mes:.2f}")
    st.markdown("---")
    st.subheader("📈 Resumo de Entradas vs Saídas (Mês Atual)")
    dados_grafico = pd.DataFrame({"Categoria": ["Entradas", "Saídas"], "Total (R$)": [ent_mes, abs(sai_mes)]})
    st.bar_chart(data=dados_grafico, x="Categoria", y="Total (R$)", color="#29b6f6")

# --- TAB 2: HISTÓRICO DE CAIXA (MANTIDO) ---
with tab2:
    st.subheader("📜 Histórico Completo de Transações")
    # ... (lógica do histórico idêntica ao original) ...
    if not df_fluxo_caixa.empty:
        df_filtro = df_fluxo_caixa.dropna(subset=['Data']).copy(); df_filtro['Mês/Ano'] = df_filtro['Data'].dt.strftime('%m/%Y')
        meses_disponiveis = sorted(df_filtro['Mês/Ano'].unique(), reverse=True)
        mes_escolhido = st.selectbox("📅 Selecione o mês:", ["Ver Tudo"] + meses_disponiveis)
        df_exibicao = df_filtro[df_filtro['Mês/Ano'] == mes_escolhido] if mes_escolhido != "Ver Tudo" else df_filtro
        if not df_exibicao.empty:
            df_visualizacao = df_exibicao.sort_index(ascending=False).copy()
            df_visualizacao['Data'] = df_visualizacao['Data'].dt.strftime('%d/%m/%Y'); df_visualizacao = df_visualizacao.drop(columns=['Mês/Ano'])
            def colorir(row):
                if row['Tipo'] == 'Entrada': return ['background-color: #d4edda; color: #155724'] * 4
                elif row['Tipo'] == 'Saída': return ['background-color: #f8d7da; color: #721c24'] * 4
                elif row['Tipo'] == 'Pendência': return ['background-color: #fff3cd; color: #856404'] * 4
                return [''] * 4
            st.dataframe(df_visualizacao.style.apply(colorir, axis=1).format({"Valor": "R$ {:.2f}"}), use_container_width=True)
    else: st.info("Nenhuma movimentação.")
