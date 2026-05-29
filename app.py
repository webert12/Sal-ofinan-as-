import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import json
import time

# --- CONFIGURAÇÃO DE FUSO HORÁRIO ---
TZ = ZoneInfo("America/Sao_Paulo")

# Configuração da página
st.set_page_config(page_title="Gestão Financeira - Salão", layout="wide", page_icon="✂️")

# --- ESTILIZAÇÃO CSS PROFISSIONAL E CORREÇÕES VISUAIS ---
st.markdown("""
<style>
    /* ... (mantenha seu CSS anterior aqui) ... */

    /* FORÇAR CENTRALIZAÇÃO DOS BOTÕES DE INCREMENTO */
    div[data-testid="stNumberInputContainer"] > div {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    div[data-testid="stNumberInputContainer"] button {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        height: 40px !important; /* Altura fixa para garantir centralização */
        width: 40px !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Remove qualquer margem interna extra que o Streamlit possa estar aplicando */
    div[data-testid="stNumberInputStepDown"] p, 
    div[data-testid="stNumberInputStepUp"] p {
        margin: 0 !important;
        line-height: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Correção específica para dispositivos móveis */
    @media (max-width: 768px) {
        div[data-testid="stNumberInputContainer"] button {
            height: 35px !important;
            width: 35px !important;
        }
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

tab1, tab0, tab2 = st.tabs(["📊 Dashboard", "🚀 Início / Ações Rápidas", "📜 Histórico"])

# --- TAB 1: DASHBOARD GRÁFICO ---
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
            st.session_state.formulario_ativo = 'none' if st.session_state.formulario_ativo == 'new_atendimento' else 'new_atendimento'
            st.rerun()
            
        if st.session_state.formulario_ativo == 'new_atendimento':
            st.markdown('<div class="embedded-form-container">', unsafe_allow_html=True)
            st.write("**📥 Novo Atendimento**")
            if list(st.session_state.servicos.keys()):
                servico_selecionado = st.selectbox("Serviço realizado:", list(st.session_state.servicos.keys()), key="f_atend_serv")
                preco_final = st.number_input("Valor Cobrado (R$):", value=float(st.session_state.servicos[servico_selecionado]), step=1.0, key="f_atend_prc")
                data_entrada = st.date_input("Data:", datetime.now(TZ).date(), key="f_atend_dt")
                if st.button("Lançar", type="primary", key="f_atend_save", use_container_width=True):
                    nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_entrada), "Tipo": "Entrada", "Descrição": f"Atendimento: {servico_selecionado}", "Valor": preco_final}])
                    st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa)
                    
                    st.markdown('<div class="confirmacao-dourada">✅ Atendimento registrado com sucesso!</div>', unsafe_allow_html=True)
                    st.session_state.formulario_ativo = 'none'
                    time.sleep(1.2)
                    st.rerun()
            else:
                st.info("Cadastre serviços na barra lateral.")
            st.markdown('</div>', unsafe_allow_html=True)
            
    with col_b:
        st.markdown('<div class="is-action-card"></div>', unsafe_allow_html=True)
        if st.button("🛍️ Nova despesa  ❯", key="btn_venda", use_container_width=True):
            st.session_state.formulario_ativo = 'none' if st.session_state.formulario_ativo == 'new_venda' else 'new_venda'
            st.rerun()
            
        if st.session_state.formulario_ativo == 'new_venda':
            st.markdown('<div class="embedded-form-container">', unsafe_allow_html=True)
            st.write("**📤 Registrar Despesa**")
            descricao_saida = st.text_input("Descrição (Ex: Luz, Aluguel):", key="f_venda_desc")
            valor_saida = st.number_input("Valor pago (R$):", min_value=0.0, step=5.0, key="f_venda_val")
            data_saida = st.date_input("Data:", datetime.now(TZ).date(), key="f_venda_dt")
            if st.button("Confirmar", type="primary", key="f_venda_save", use_container_width=True):
                if descricao_saida and valor_saida > 0:
                    nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_saida), "Tipo": "Saída", "Descrição": descricao_saida, "Valor": -valor_saida}])
                    st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa)
                    
                    st.markdown('<div class="confirmacao-dourada">✅ Despesa registrada com sucesso!</div>', unsafe_allow_html=True)
                    st.session_state.formulario_ativo = 'none'
                    time.sleep(1.2)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
    with col_c:
        st.markdown('<div class="is-action-card"></div>', unsafe_allow_html=True)
        if st.button("💰 Marcar fiado  ❯", key="btn_receber", use_container_width=True):
            st.session_state.formulario_ativo = 'none' if st.session_state.formulario_ativo == 'new_receber' else 'new_receber'
            st.rerun()
            
        if st.session_state.formulario_ativo == 'new_receber':
            st.markdown('<div class="embedded-form-container">', unsafe_allow_html=True)
            st.write("**⏳ Registrar Fiado**")
            if list(st.session_state.servicos.keys()):
                nome_devedor = st.text_input("Nome do Cliente:", key="f_fiado_nome")
                servico_pendente = st.selectbox("Serviço:", list(st.session_state.servicos.keys()), key="f_fiado_serv")
                preco_final_p = st.number_input("Valor (R$):", value=float(st.session_state.servicos[servico_pendente]), key="f_fiado_prc")
                data_pendencia = st.date_input("Data:", datetime.now(TZ).date(), key="f_fiado_dt")
                if st.button("Salvar", type="primary", key="f_fiado_save", use_container_width=True):
                    if nome_devedor:
                        nova_linha = pd.DataFrame([{"Data": pd.to_datetime(data_pendencia), "Tipo": "Pendência", "Descrição": f"Fiado de: {nome_devedor} ({servico_pendente})", "Valor": preco_final_p}])
                        st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True); salvar_fluxo(st.session_state.fluxo_caixa)
                        
                        st.markdown('<div class="confirmacao-dourada">✅ Corte fiado pendente registrado!</div>', unsafe_allow_html=True)
                        st.session_state.formulario_ativo = 'none'
                        time.sleep(1.2)
                        st.rerun()
            else:
                st.info("Cadastre serviços na barra lateral.")
            st.markdown('</div>', unsafe_allow_html=True)
            
    with col_d:
        st.markdown('<div class="is-action-card"></div>', unsafe_allow_html=True)
        if st.button("💸 Receber fiado  ❯", key="btn_pagar", use_container_width=True):
            st.session_state.formulario_ativo = 'none' if st.session_state.formulario_ativo == 'new_pagar' else 'new_pagar'
            st.rerun()
            
        if st.session_state.formulario_ativo == 'new_pagar':
            st.markdown('<div class="embedded-form-container">', unsafe_allow_html=True)
            st.write("**✅ Receber Fiado**")
            df_pendencias = df_fluxo_caixa[df_fluxo_caixa['Tipo'] == 'Pendência']
            if not df_pendencias.empty:
                opcoes_pendentes = {f"{row['Descrição']} - R$ {abs(row['Valor']):.2f}": idx for idx, row in df_pendencias.iterrows()}
                pendencia_selecionada = st.selectbox("Selecione o cliente:", list(opcoes_pendentes.keys()), key="f_pago_sel")
                if st.button("Dar Baixa", type="primary", key="f_pago_save", use_container_width=True):
                    idx_alterar = opcoes_pendentes[pendencia_selecionada]
                    st.session_state.fluxo_caixa.at[idx_alterar, 'Tipo'] = 'Entrada'
                    st.session_state.fluxo_caixa.at[idx_alterar, 'Data'] = pd.to_datetime(datetime.now(TZ).date())
                    st.session_state.fluxo_caixa.at[idx_alterar, 'Descrição'] = st.session_state.fluxo_caixa.at[idx_alterar, 'Descrição'].replace("Fiado de:", "Recebido Fiado:") + " [PAGO]"
                    salvar_fluxo(st.session_state.fluxo_caixa)
                    
                    st.markdown('<div class="confirmacao-dourada">✅ Baixa de fiado registrada com sucesso!</div>', unsafe_allow_html=True)
                    st.session_state.formulario_ativo = 'none'
                    time.sleep(1.2)
                    st.rerun()
            else:
                st.info("Nenhum fiado em aberto.")
            st.markdown('</div>', unsafe_allow_html=True)
            
    with col_e:
        st.markdown('<div class="is-action-card"></div>', unsafe_allow_html=True)
        if st.button("📊 Ver relatórios  ❯", key="btn_relatorios", use_container_width=True):
            st.session_state.formulario_ativo = 'none' if st.session_state.formulario_ativo == 'view_relatorios' else 'view_relatorios'
            st.rerun()
            
        if st.session_state.formulario_ativo == 'view_relatorios':
            st.markdown('<div class="embedded-form-container">', unsafe_allow_html=True)
            st.write("**📊 Resumo Rápido**")
            st.metric("Líquido Diário", f"R$ {lucro_dia:.2f}")
            st.metric("Líquido Mensal", f"R$ {lucro_mes:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

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
