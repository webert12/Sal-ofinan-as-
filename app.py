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
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">', unsafe_allow_html=True)

# CSS personalizado corrigido para garantir o clique perfeito
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
        background-color: #1a1d21;
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
        background-color: #d4af37;
    }
    
    /* Estilo de cada item de ação rápida */
    .fast-action-item {
        background-color: #22252a;
        border-radius: 8px;
        padding: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: background-color 0.3s;
        border: 1px solid #333;
        pointer-events: none; /* Permite que o clique passe para o botão invisível */
    }
    
    .fast-action-icon {
        color: #d4af37;
        font-size: 1.2rem;
        margin-right: 15px;
    }
    
    .fast-action-text {
        color: white;
        font-weight: 500;
        font-size: 0.9rem;
        flex-grow: 1;
        text-align: left;
    }
    
    .fast-action-chevron {
        color: #d4af37;
        font-size: 1rem;
    }

    /* CORREÇÃO DO CLIQUE: Força a coluna a ser a referência de posicionamento */
    div[data-testid="stColumn"]:has(.fast-action-item) {
        position: relative !important;
    }
    
    /* CORREÇÃO DA DIV INTERNA DO STREAMLIT: Faz o container do botão ocupar o card todo */
    div[data-testid="stColumn"]:has(.fast-action-item) div[data-testid="element-container"]:has(button) {
        position: absolute !important;
        top: 0;
        left: 0;
        width: 100% !important;
        height: 100% !important;
        z-index: 10 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Torna o botão do Streamlit completamente invisível, mas 100% clicável */
    div[data-testid="stColumn"]:has(.fast-action-item) button {
        width: 100% !important;
        height: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: transparent !important;
        box-shadow: none !important;
        cursor: pointer !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Aplica o efeito visual de hover no card de baixo quando passa o mouse na coluna */
    div[data-testid="stColumn"]:has(.fast-action-item):hover .fast-action-item {
        background-color: #333 !important;
    }
    
</style>
""", unsafe_allow_html=True)

def renderizar_acao_rapida(icon_class, text):
    """Renderiza apenas a estrutura visual do card."""
    return f"""
    <div class="fast-action-item">
        <i class="{icon_class} fast-action-icon"></i>
        <span class="fast-action-text">{text}</span>
        <i class="fa fa-chevron-right fast-action-chevron"></i>
    </div>
    """

# --- INICIALIZAÇÃO DE ESTADOS ---
if 'formulario_ativo' not in st.session_state:
    st.session_state.formulario_ativo = 'none'

USUARIOS_FILE = "usuarios.json"
ADMIN_MESTRE_USER = "admin"
ADMIN_MESTRE_PASS = "master2026"

# --- FUNÇÕES DE GERENCIAMENTO (MANTIDAS) ---
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
        "salao_central": {"senha": "admin123", "tipo": "Cliente", "vencimento": vencimento_padrao, "status": "Ativo"},
        "barbearia_vanguard": {"senha": "corte2026", "tipo": "Teste", "vencimento": (datetime.now(TZ) + timedelta(days=7)).strftime("%Y-%m-%d"), "status": "Ativo"}
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
        with open(servicos_file, "r") as f: return json.load(f)
    return {"Corte de Cabelo": 25.00, "Barba": 25.00, "Combo Cabelo e Barba": 50.00}

def salvar_servicos(servicos):
    servicos_file, _ = obter_nomes_arquivos()
    with open(servicos_file, "w") as f: json.dump(servicos, f, indent=4)

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
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario_logado' not in st.session_state: st.session_state.usuario_logado = None
if 'eh_admin' not in st.session_state: st.session_state.eh_admin = False

usuarios_cadastrados = carregar_usuarios()

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
                st.rerun()
            elif usuario_input in usuarios_cadastrados and usuarios_cadastrados[usuario_input]["senha"] == senha_input:
                dados_user = usuarios_cadastrados[usuario_input]
                data_vencimento = datetime.strptime(dados_user["vencimento"], "%Y-%m-%d").date()
                if datetime.now(TZ).date() > data_vencimento or dados_user.get("status") == "Suspenso":
                    st.error("❌ ACESSO BLOQUEADO! Licença vencida.")
                    st.stop()
                st.session_state.autenticado = True
                st.session_state.usuario_logado = usuario_input
                st.session_state.eh_admin = False
                st.session_state.servicos = carregar_servicos()
                st.session_state.fluxo_caixa = carregar_fluxo()
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# --- INTERFACE 1: ADMINISTRADOR MESTRE ---
if st.session_state.eh_admin:
    st.title("👑 Central do Administrador")
    st.markdown("---")
    col_cad, col_lista = st.columns([1, 1.2])
    with col_cad:
        st.subheader("➕ Registrar ou Renovar Salão")
        with st.form("form_cadastro_cliente"):
            novo_usuario = st.text_input("Usuário do Salão:").strip().lower()
            nova_senha = st.text_input("Senha de Acesso:", type="password").strip()
            tipo_conta = st.selectbox("Tipo de Conta:", ["Teste", "Cliente"])
            dias_validade = st.number_input("Dias de Validade:", min_value=1, value=30)
            if st.form_submit_button("Salvar Conta"):
                if novo_usuario and nova_senha:
                    vencimento_calculado = (datetime.now(TZ) + timedelta(days=dias_validade)).strftime("%Y-%m-%d")
                    usuarios_cadastrados[novo_usuario] = {"senha": nova_senha, "tipo": tipo_conta, "vencimento": vencimento_calculado, "status": "Ativo"}
                    salvar_usuarios(usuarios_cadastrados); st.success("Salão configurado!"); st.rerun()
    with col_lista:
        st.subheader("👥 Salões Cadastrados")
        lista_formatada = [{"Salão / Usuário": u, "Tipo": i["tipo"], "Vencimento": datetime.strptime(i['vencimento'], "%Y-%m-%d").strftime("%d/%m/%Y")} for u, i in usuarios_cadastrados.items()]
        st.dataframe(pd.DataFrame(lista_formatada), use_container_width=True, hide_index=True)
    with st.sidebar:
        if st.button("🚪 Sair do Modo ADM", use_container_width=True):
            st.session_state.autenticado = False; st.rerun()
    st.stop()

# --- INTERFACE 2: PAINEL DO CLIENTE ---
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

tab0, tab1, tab2 = st.tabs(["🚀 Início / Ações Rápidas", "📊 Dashboard", "📜 Histórico"])

with tab0:
    st.markdown('<div class="sim-header"><span class="sim-header-title">Fio&Caixa</span><span class="sim-header-icons"><i class="fa fa-bell"></i> <i class="fa fa-user-circle"></i></span></div>', unsafe_allow_html=True)
    st.markdown('<div class="fast-actions-header"><span class="fast-actions-title">Ações rápidas</span><div class="fast-actions-line"></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="fast-actions-container">', unsafe_allow_html=True)
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    
    with col_a:
        st.markdown(renderizar_acao_rapida("fa fa-scissors", "Novo atendimento"), unsafe_allow_html=True)
        if st.button("", key="btn_atend"):
            st.session_state.formulario_ativo = 'new_atendimento'; st.rerun()
    with col_b:
        st.markdown(renderizar_acao_rapida("fa fa-shopping-cart", "Nova venda"), unsafe_allow_html=True)
        if st.button("", key="btn_venda"):
            st.session_state.formulario_ativo = 'new_venda'; st.rerun()
    with col_c:
        st.markdown(renderizar_acao_rapida("fa fa-piggy-bank", "Contas a receber"), unsafe_allow_html=True)
        if st.button("", key="btn_receber"):
            st.session_state.formulario_ativo = 'new_receber'; st.rerun()
    with col_d:
        st.markdown(renderizar_acao_rapida("fa fa-hand-holding-usd", "Contas a pagar"), unsafe_allow_html=True)
        if st.button("", key="btn_pagar"):
            st.session_state.formulario_ativo = 'new_pagar'; st.rerun()
    with col_e:
        st.markdown(renderizar_acao_rapida("fa fa-chart-bar", "Relatórios"), unsafe_allow_html=True)
        if st.button("", key="btn_relatorios"):
            st.session_state.formulario_ativo = 'view_relatorios'; st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

    # --- EXIBIÇÃO DINÂMICA DOS FORMULÁRIOS ---
    formulario_ativo = st.session_state.formulario_ativo

    if formulario_ativo == 'new_atendimento':
        st.subheader("📥 REGISTRAR ENTRADA (Atendimento Concluído)")
        if list(st.session_state.servicos.keys()):
            servico_selecionado = st.selectbox("Selecione o Serviço realizado:", list(st.session_state.servicos.keys()))
            preco_final = st.number_input("Valor Cobrado (R$):", value=float(st.session_state.servicos[servico_selecionado]), step=1.0)
            data_entrada = st.date_input("Data do Atendimento:", datetime.now(TZ).date())
            if st.button("Confirmar e Lançar Entrada", type="primary"):
                nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_entrada), "Tipo": "Entrada", "Descrição": f"Atendimento: {servico_selecionado}", "Valor": preco_final}])
                st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa)
                st.session_state.formulario_ativo = 'none'; st.rerun()
        else: st.info("Cadastre serviços na barra lateral.")
        if st.button("Fechar", key="c_atend"): st.session_state.formulario_ativo = 'none'; st.rerun()

    elif formulario_ativo == 'new_venda':
        st.subheader("📤 REGISTRAR SAÍDA (Pagamento de Despesas)")
        descricao_saida = st.text_input("Descrição da Despesa (Ex: Luz, Aluguel):")
        valor_saida = st.number_input("Valor (R$):", min_value=0.0, step=5.0)
        data_saida = st.date_input("Data do Pagamento:", datetime.now(TZ).date())
        if st.button("Confirmar Saída", type="primary"):
            if descricao_saida and valor_saida > 0:
                nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_saida), "Tipo": "Saída", "Descrição": descricao_saida, "Valor": -valor_saida}])
                st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa)
                st.session_state.formulario_ativo = 'none'; st.rerun()
        if st.button("Fechar", key="c_venda"): st.session_state.formulario_ativo = 'none'; st.rerun()

    elif formulario_ativo == 'new_receber':
        st.subheader("⏳ REGISTRAR PENDÊNCIA (Serviço Fiado)")
        if list(st.session_state.servicos.keys()):
            nome_devedor = st.text_input("Nome do Cliente:")
            servico_pendente = st.selectbox("Selecione o Serviço:", list(st.session_state.servicos.keys()))
            preco_final_p = st.number_input("Valor Pendente (R$):", value=float(st.session_state.servicos[servico_pendente]))
            data_pendencia = st.date_input("Data:", datetime.now(TZ).date())
            if st.button("Salvar Fiado", type="primary"):
                if nome_devedor:
                    nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_pendencia), "Tipo": "Pendência", "Descrição": f"Fiado de: {nome_devedor} ({servico_pendente})", "Valor": preco_final_p}])
                    st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa)
                    st.session_state.formulario_ativo = 'none'; st.rerun()
        if st.button("Fechar", key="c_receber"): st.session_state.formulario_ativo = 'none'; st.rerun()

    elif formulario_ativo == 'new_pagar':
        st.subheader("✅ CONFIRMAR RECEBIMENTO DE FIADO")
        df_pendencias = df_fluxo_caixa[df_fluxo_caixa['Tipo'] == 'Pendência']
        if not df_pendencias.empty:
            opcoes_pendentes = {f"{row['Descrição']} - R$ {abs(row['Valor']):.2f}": idx for idx, row in df_pendencias.iterrows()}
            pendencia_selecionada = st.selectbox("Selecione o cliente pagando:", list(opcoes_pendentes.keys()))
            if st.button("Dar Baixa (Recebido)", type="primary"):
                idx_alterar = opcoes_pendentes[pendencia_selecionada]
                st.session_state.fluxo_caixa.at[idx_alterar, 'Tipo'] = 'Entrada'
                st.session_state.fluxo_caixa.at[idx_alterar, 'Data'] = pd.to_datetime(datetime.now(TZ).date())
                st.session_state.fluxo_caixa.at[idx_alterar, 'Descrição'] = st.session_state.fluxo_caixa.at[idx_alterar, 'Descrição'].replace("Fiado de:", "Recebido Fiado:") + " [PAGO]"
                salvar_fluxo(st.session_state.fluxo_caixa); st.session_state.formulario_ativo = 'none'; st.rerun()
        else: st.info("Nenhum fiado em aberto.")
        if st.button("Fechar", key="c_pagar"): st.session_state.formulario_ativo = 'none'; st.rerun()
        
    elif formulario_ativo == 'view_relatorios':
        st.subheader("📊 Resumo de Fechamento")
        c1, c2 = st.columns(2)
        c1.metric("Líquido do Dia", f"R$ {lucro_dia:.2f}")
        c2.metric("Líquido do Mês", f"R$ {lucro_mes:.2f}")
        if st.button("Fechar", key="c_rel"): st.session_state.formulario_ativo = 'none'; st.rerun()
    else:
        st.info("👆 Clique em um dos cards de ação acima para interagir com o sistema.")

# --- SIDEBAR: CONFIGURAÇÕES DE SERVIÇOS ---
with st.sidebar:
    st.header("⚙️ Configurações")
    nome_salao = st.session_state.usuario_logado.replace("_", " ").title()
    st.title(f"✂️ {nome_salao}")
    st.markdown("---")
    opcoes_gerenciamento = ["➕ Cadastrar Novo Serviço"] + list(st.session_state.servicos.keys())
    servico_sel = st.selectbox("Escolha uma ação:", opcoes_gerenciamento)
    
    nome_padrao = "" if servico_sel == "➕ Cadastrar Novo Serviço" else servico_sel
    preco_padrao = 0.0 if servico_sel == "➕ Cadastrar Novo Serviço" else float(st.session_state.servicos[servico_sel])
    
    novo_servico = st.text_input("Nome do Serviço:", value=nome_padrao)
    novo_preco = st.number_input("Preço (R$):", min_value=0.0, value=preco_padrao, step=5.0)
    
    if st.button("Salvar Serviço", type="primary"):
        if novo_servico:
            if servico_sel != "➕ Cadastrar Novo Serviço": del st.session_state.servicos[servico_sel]
            st.session_state.servicos[novo_servico] = novo_preco; salvar_servicos(st.session_state.servicos); st.rerun()
            
    if servico_sel != "➕ Cadastrar Novo Serviço" and st.button("🗑️ Excluir"):
        del st.session_state.servicos[servico_sel]; salvar_servicos(st.session_state.servicos); st.rerun()
        
    if st.button("🚪 Sair do Painel", use_container_width=True):
        st.session_state.autenticado = False; st.rerun()

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader("📊 Resumo Financeiro")
    m1, m2, m3 = st.columns(3)
    m1.metric("Fechamento Dia", f"R$ {lucro_dia:.2f}")
    m2.metric("Últimos 7 Dias", f"R$ {lucro_sem:.2f}")
    m3.metric("Mês Atual", f"R$ {lucro_mes:.2f}")
    st.markdown("---")
    st.bar_chart(pd.DataFrame({"Categoria": ["Entradas", "Saídas"], "Total (R$)": [ent_mes, abs(sai_mes)]}), x="Categoria", y="Total (R$)", color="#29b6f6")

# --- TAB 2: HISTÓRICO ---
with tab2:
    st.subheader("📜 Histórico de Transações")
    if not df_fluxo_caixa.empty:
        df_filtro = df_fluxo_caixa.dropna(subset=['Data']).copy()
        df_filtro['Mês/Ano'] = df_filtro['Data'].dt.strftime('%m/%Y')
        meses = sorted(df_filtro['Mês/Ano'].unique(), reverse=True)
        mes_escolhido = st.selectbox("📅 Selecione o mês:", ["Ver Tudo"] + meses)
        df_exibicao = df_filtro[df_filtro['Mês/Ano'] == mes_escolhido] if mes_escolhido != "Ver Tudo" else df_filtro
        if not df_exibicao.empty:
            df_vis = df_exibicao.sort_index(ascending=False).copy()
            df_vis['Data'] = df_vis['Data'].dt.strftime('%d/%m/%Y')
            df_vis = df_vis.drop(columns=['Mês/Ano'])
            def colorir(row):
                if row['Tipo'] == 'Entrada': return ['background-color: #d4edda; color: #155724'] * 4
                elif row['Tipo'] == 'Saída': return ['background-color: #f8d7da; color: #721c24'] * 4
                return ['background-color: #fff3cd; color: #856404'] * 4
            st.dataframe(df_vis.style.apply(colorir, axis=1).format({"Valor": "R$ {:.2f}"}), use_container_width=True)
    else: st.info("Nenhuma movimentação.")
