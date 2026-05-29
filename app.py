import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import json

# --- CONFIGURAÇÃO DE FUSO HORÁRIO ---
TZ = ZoneInfo("America/Sao_Paulo")

# Configuração da página
st.set_page_config(page_title="Gestão Financeira - Salão", layout="wide", page_icon="✂️")

# --- ESTILIZAÇÃO CSS PROFISSIONAL E COMPATÍVEL ---
st.markdown("""
<style>
    /* Estilos globais para tema escuro */
    body, .stApp {
        background-color: #121212;
        color: white;
    }
    
    /* Simulação de cabeçalho superior */
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
    
    /* Título "Ações rápidas" e linha dourada */
    .fast-actions-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
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

    /* Oculta o marcador estrutural usado para isolar os estilos */
    .is-action-card {
        display: none;
    }

    /* TRANSFORMAÇÃO DOS BOTÕES NATIVOS EM CARDS SEGUROS */
    div[data-testid="stColumn"]:has(.is-action-card) button {
        background-color: #22252a !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
        padding: 18px 15px !important;
        min-height: 75px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 10px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15) !important;
        cursor: pointer !important;
    }
    
    /* Estilização do texto dentro do botão-card */
    div[data-testid="stColumn"]:has(.is-action-card) button p {
        color: white !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        margin: 0 !important;
        text-align: left !important;
    }
    
    /* Efeito ao passar o mouse (Hover) nos Cards */
    div[data-testid="stColumn"]:has(.is-action-card) button:hover {
        background-color: #2a2e35 !important;
        border-color: #d4af37 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(212, 175, 55, 0.1) !important;
    }
    
    /* Efeito de Clique Ativo */
    div[data-testid="stColumn"]:has(.is-action-card) button:active {
        background-color: #d4af37 !important;
        border-color: #d4af37 !important;
    }
    div[data-testid="stColumn"]:has(.is-action-card) button:active p {
        color: #121212 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE ESTADOS ---
if 'formulario_ativo' not in st.session_state:
    st.session_state.formulario_ativo = 'none'

USUARIOS_FILE = "usuarios.json"
ADMIN_MESTRE_USER = "admin"
ADMIN_MESTRE_PASS = "master2026"

# --- FUNÇÕES DE GERENCIAMENTO DE ARQUIVOS ---
def carregar_usuarios():
    vencimento_padrao = (datetime.now(TZ) + timedelta(days=30)).strftime("%Y-%m-%d")
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r") as f:
            dados = json.load(f)
        usuarios_atualizados = {}
        modificado = False
        for k, v in dados.items():
            if isinstance(v, str):
                usuarios_atualizados[k] = {"senha": v, "tipo": "Cliente", "vencimento": vencimento_padrao, "status": "Ativo"}
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

# ALTERADO: Mudança na ordem das abas para trazer o Dashboard para a frente
tab1, tab0, tab2 = st.tabs(["📊 Dashboard", "🚀 Início / Ações Rápidas", "📜 Histórico"])

# --- TAB 1: DASHBOARD GRÁFICO (AGORA NA FRENTE) ---
with tab1:
    st.subheader("📊 Resumo Financeiro Estruturado")
    m1, m2, m3 = st.columns(3)
    m1.metric("Fechamento do Dia", f"R$ {lucro_dia:.2f}")
    m2.metric("Acumulado 7 Dias", f"R$ {lucro_sem:.2f}")
    m3.metric("Faturamento do Mês", f"R$ {lucro_mes:.2f}")
    st.markdown("---")
    st.bar_chart(pd.DataFrame({"Categoria": ["Entradas", "Saídas"], "Total (R$)": [ent_mes, abs(sai_mes)]}), x="Categoria", y="Total (R$)", color="#29b6f6")

# --- TAB 0: COMANDOS E AÇÕES RÁPIDAS ---
with tab0:
    st.markdown('<div class="sim-header"><span class="sim-header-title">Fio&Caixa</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="fast-actions-header"><span class="fast-actions-title">Ações rápidas</span><div class="fast-actions-line"></div></div>', unsafe_allow_html=True)

    # Grid de Ações Rápidas
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    
    with col_a:
        st.markdown('<div class="is-action-card"></div>', unsafe_allow_html=True)
        if st.button("✂️ Novo atendimento  ❯", key="btn_atend", use_container_width=True):
            st.session_state.formulario_ativo = 'new_atendimento'
            st.rerun()
            
    with col_b:
        st.markdown('<div class="is-action-card"></div>', unsafe_allow_html=True)
        if st.button("🛍️ Nova despesa  ❯", key="btn_venda", use_container_width=True):
            st.session_state.formulario_ativo = 'new_venda'
            st.rerun()
            
    with col_c:
        st.markdown('<div class="is-action-card"></div>', unsafe_allow_html=True)
        if st.button("💰 Marcar fiado  ❯", key="btn_receber", use_container_width=True):
            st.session_state.formulario_ativo = 'new_receber'
            st.rerun()
            
    with col_d:
        st.markdown('<div class="is-action-card"></div>', unsafe_allow_html=True)
        if st.button("💸 Receber fiado  ❯", key="btn_pagar", use_container_width=True):
            st.session_state.formulario_ativo = 'new_pagar'
            st.rerun()
            
    with col_e:
        st.markdown('<div class="is-action-card"></div>', unsafe_allow_html=True)
        if st.button("📊 Ver relatórios  ❯", key="btn_relatorios", use_container_width=True):
            st.session_state.formulario_ativo = 'view_relatorios'
            st.rerun()

    # --- EXIBIÇÃO DINÂMICA DOS FORMULÁRIOS (IMEDIATAMENTE ABAIXO DOS BOTÕES) ---
    formulario_ativo = st.session_state.formulario_ativo

    if formulario_ativo != 'none':
        # Container colado e destacado com borda dourada suave indicando atividade
        st.markdown('<div style="margin-top: 15px; background-color: #1a1d21; padding: 20px; border-radius: 8px; border: 1px solid #d4af37;">', unsafe_allow_html=True)
        
        if formulario_ativo == 'new_atendimento':
            st.subheader("📥 REGISTRAR ENTRADA (Atendimento Concluído)")
            if list(st.session_state.servicos.keys()):
                servico_selecionado = st.selectbox("Selecione o Serviço realizado:", list(st.session_state.servicos.keys()))
                preco_final = st.number_input("Valor Cobrado (R$):", value=float(st.session_state.servicos[servico_selecionado]), step=1.0)
                data_entrada = st.date_input("Data do Atendimento:", datetime.now(TZ).date())
                
                c_btn1, c_btn2 = st.columns([1, 4])
                if c_btn1.button("Lançar Entrada", type="primary"):
                    nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_entrada), "Tipo": "Entrada", "Descrição": f"Atendimento: {servico_selecionado}", "Valor": preco_final}])
                    st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa)
                    st.session_state.formulario_ativo = 'none'; st.rerun()
                if c_btn2.button("Cancelar", key="c_atend"): st.session_state.formulario_ativo = 'none'; st.rerun()
            else: 
                st.info("Por favor, cadastre serviços na barra lateral antes de começar.")
                if st.button("Fechar"): st.session_state.formulario_ativo = 'none'; st.rerun()

        elif formulario_ativo == 'new_venda':
            st.subheader("📤 REGISTRAR SAÍDA (Pagamento de Despesas)")
            descricao_saida = st.text_input("Descrição da Despesa (Ex: Luz, Aluguel, Produtos):")
            valor_saida = st.number_input("Valor pago (R$):", min_value=0.0, step=5.0)
            data_saida = st.date_input("Data do Pagamento:", datetime.now(TZ).date())
            
            c_btn1, c_btn2 = st.columns([1, 4])
            if c_btn1.button("Confirmar Saída", type="primary"):
                if descricao_saida and valor_saida > 0:
                    nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_saida), "Tipo": "Saída", "Descrição": descricao_saida, "Valor": -valor_saida}])
                    st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa)
                    st.session_state.formulario_ativo = 'none'; st.rerun()
            if c_btn2.button("Cancelar", key="c_venda"): st.session_state.formulario_ativo = 'none'; st.rerun()

        elif formulario_ativo == 'new_receber':
            st.subheader("⏳ REGISTRAR PENDÊNCIA (Serviço Fiado)")
            if list(st.session_state.servicos.keys()):
                nome_devedor = st.text_input("Nome do Cliente Devedor:")
                servico_pendente = st.selectbox("Selecione o Serviço:", list(st.session_state.servicos.keys()))
                preco_final_p = st.number_input("Valor Pendente (R$):", value=float(st.session_state.servicos[servico_pendente]))
                data_pendencia = st.date_input("Data da pendência:", datetime.now(TZ).date())
                
                c_btn1, c_btn2 = st.columns([1, 4])
                if c_btn1.button("Salvar Registro", type="primary"):
                    if nome_devedor:
                        nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_pendencia), "Tipo": "Pendência", "Descrição": f"Fiado de: {nome_devedor} ({servico_pendente})", "Valor": preco_final_p}])
                        st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa)
                        st.session_state.formulario_ativo = 'none'; st.rerun()
            if c_btn2.button("Cancelar", key="c_receber"): st.session_state.formulario_ativo = 'none'; st.rerun()

        elif formulario_ativo == 'new_pagar':
            st.subheader("✅ CONFIRMAR RECEBIMENTO DE FIADO")
            df_pendencias = df_fluxo_caixa[df_fluxo_caixa['Tipo'] == 'Pendência']
            if not df_pendencias.empty:
                opcoes_pendentes = {f"{row['Descrição']} - R$ {abs(row['Valor']):.2f}": idx for idx, row in df_pendencias.iterrows()}
                pendencia_selecionada = st.selectbox("Selecione o cliente que está pagando:", list(opcoes_pendentes.keys()))
                
                c_btn1, c_btn2 = st.columns([1, 4])
                if c_btn1.button("Dar Baixa (Pago)", type="primary"):
                    idx_alterar = opcoes_pendentes[pendencia_selecionada]
                    st.session_state.fluxo_caixa.at[idx_alterar, 'Tipo'] = 'Entrada'
                    st.session_state.fluxo_caixa.at[idx_alterar, 'Data'] = pd.to_datetime(datetime.now(TZ).date())
                    st.session_state.fluxo_caixa.at[idx_alterar, 'Descrição'] = st.session_state.fluxo_caixa.at[idx_alterar, 'Descrição'].replace("Fiado de:", "Recebido Fiado:") + " [PAGO]"
                    salvar_fluxo(st.session_state.fluxo_caixa); st.session_state.formulario_ativo = 'none'; st.rerun()
            else: 
                st.info("Nenhum registro de fiado em aberto no momento.")
            if st.button("Fechar Janela", key="c_pagar"): st.session_state.formulario_ativo = 'none'; st.rerun()
            
        elif formulario_ativo == 'view_relatorios':
            st.subheader("📊 Resumo Rápido de Fechamento")
            c1, c2 = st.columns(2)
            c1.metric("Faturamento Líquido do Dia", f"R$ {lucro_dia:.2f}")
            c2.metric("Faturamento Líquido do Mês", f"R$ {lucro_mes:.2f}")
            if st.button("Fechar Relatório", key="c_rel"): st.session_state.formulario_ativo = 'none'; st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #777; font-style: italic; margin-top:15px;'>Clique em uma das ações rápidas acima para abrir os painéis de lançamento.</p>", unsafe_allow_html=True)

# --- SIDEBAR: CONFIGURAÇÕES DE SERVIÇOS ---
with st.sidebar:
    st.header("⚙️ Configurações")
    nome_salao = st.session_state.usuario_logado.replace("_", " ").title()
    st.title(f"✂️ {nome_salao}")
    st.markdown("---")
    opcoes_gerenciamento = ["➕ Cadastrar Novo Serviço"] + list(st.session_state.servicos.keys())
    servico_sel = st.selectbox("Escolha um serviço para gerenciar:", opcoes_gerenciamento)
    
    nome_padrao = "" if servico_sel == "➕ Cadastrar Novo Serviço" else servico_sel
    preco_padrao = 0.0 if servico_sel == "➕ Cadastrar Novo Serviço" else float(st.session_state.servicos[servico_sel])
    
    novo_servico = st.text_input("Nome do Serviço:", value=nome_padrao)
    novo_preco = st.number_input("Preço Cobrado (R$):", min_value=0.0, value=preco_padrao, step=5.0)
    
    if st.button("Salvar Alteração", type="primary", use_container_width=True):
        if novo_servico:
            if servico_sel != "➕ Cadastrar Novo Serviço": del st.session_state.servicos[servico_sel]
            st.session_state.servicos[novo_servico] = novo_preco; salvar_servicos(st.session_state.servicos); st.rerun()
            
    if servico_sel != "➕ Cadastrar Novo Serviço" and st.button("🗑️ Remover Serviço do Catálogo", use_container_width=True):
        del st.session_state.servicos[servico_sel]; salvar_servicos(st.session_state.servicos); st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 Sair do Sistema", use_container_width=True):
        st.session_state.autenticado = False; st.rerun()

# --- TAB 2: HISTÓRICO DE LANÇAMENTOS ---
with tab2:
    st.subheader("📜 Histórico de Transações Completas")
    if not df_fluxo_caixa.empty:
        df_filtro = df_fluxo_caixa.dropna(subset=['Data']).copy()
        df_filtro['Mês/Ano'] = df_filtro['Data'].dt.strftime('%m/%Y')
        meses = sorted(df_filtro['Mês/Ano'].unique(), reverse=True)
        mes_escolhido = st.selectbox("📅 Escolha o mês de referência:", ["Ver Tudo"] + meses)
        df_exibicao = df_filtro[df_filtro['Mês/Ano'] == mes_escolhido] if mes_escolhido != "Ver Tudo" else df_filtro
        if not df_exibicao.empty:
            df_vis = df_exibicao.sort_index(ascending=False).copy()
            df_vis['Data'] = df_vis['Data'].dt.strftime('%d/%m/%Y')
            df_vis = df_vis.drop(columns=['Mês/Ano'])
            def colorir(row):
                if row['Tipo'] == 'Entrada': return ['background-color: #d4edda; color: #155724'] * 4
                elif row['Tipo'] == 'Saída': return ['background-color: #f8d7da; color: #721c24'] * 4
                return ['background-color: #fff3cd; color: #856404'] * 4
            st.dataframe(df_vis.style.apply(colorir, axis=1).format({"Valor": "R$ {:.2f}"}), use_container_width=True, hide_index=True)
    else: 
        st.info("Nenhuma movimentação financeira registrada até o momento.")
