import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import json
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# Código para esconder o menu do topo, o cabeçalho e o rodapé padrão
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """

# Configuração da página
st.set_page_config(page_title="Gestão Financeira - Salão", layout="wide", page_icon="✂️")

USUARIOS_FILE = "usuarios.json"

# --- CONFIGURAÇÃO DO ADMINISTRADOR MESTRE (VOCÊ) ---
ADMIN_MESTRE_USER = "admin"
ADMIN_MESTRE_PASS = "master2026"

# --- FUNÇÕES DE GERENCIAMENTO DE USUÁRIOS (COM TRATAMENTO DE VALIDADE) ---
def carregar_usuarios():
    hoje_str = datetime.now().strftime("%Y-%m-%d")
    vencimento_padrao = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r") as f:
            dados = json.load(f)
            
        # Migração automática caso o arquivo antigo esteja no formato antigo (string simples)
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

    # Dados iniciais caso não exista o arquivo
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
            "vencimento": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "status": "Ativo"
        }
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
            if usuario_input == ADMIN_MESTRE_USER and senha_input == ADMIN_MESTRE_PASS:
                st.session_state.autenticado = True
                st.session_state.usuario_logado = "Administrador"
                st.session_state.eh_admin = True
                st.success("Acesso master concedido!")
                st.rerun()
            elif usuario_input in usuarios_cadastrados and usuarios_cadastrados[usuario_input]["senha"] == senha_input:
                
                # --- VALIDAÇÃO DE EXPIRAÇÃO AUTOMÁTICA ---
                dados_user = usuarios_cadastrados[usuario_input]
                data_vencimento = datetime.strptime(dados_user["vencimento"], "%Y-%m-%d").date()
                hoje = datetime.now().date()
                
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
# --- INTERFACE 1: PAINEL DO ADMINISTRADOR MESTRE (GERENCIAR LICENÇAS) ---
# =====================================================================
if st.session_state.eh_admin:
    st.title("👑 Central do Administrador - Gestão de Clientes & Licenças")
    st.markdown("Aqui você cadastra novos salões, define períodos de teste e gerencia vencimentos.")
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
                if not novo_usuario or not nova_senha:
                    st.error("Preencha o usuário e senha para salvar.")
                elif novo_usuario == ADMIN_MESTRE_USER:
                    st.error("Nome reservado do sistema.")
                else:
                    vencimento_calculado = (datetime.now() + timedelta(days=dias_validade)).strftime("%Y-%m-%d")
                    usuarios_cadastrados[novo_usuario] = {
                        "senha": nova_senha,
                        "tipo": tipo_conta,
                        "vencimento": vencimento_calculado,
                        "status": "Ativo"
                    }
                    salvar_usuarios(usuarios_cadastrados)
                    st.success(f"Sucesso! Salão '{novo_usuario}' configurado como '{tipo_conta}' válido por {dias_validade} dias (Até {datetime.strptime(vencimento_calculado, '%Y-%m-%d').strftime('%d/%m/%Y')}).")
                    st.rerun()
                    
    with col_lista:
        st.subheader("👥 Salões Cadastrados e Status de Licença")
        
        # Montar um DataFrame amigável para exibição das licenças
        lista_formatada = []
        for user, info in usuarios_cadastrados.items():
            dt_venc = datetime.strptime(info['vencimento'], "%Y-%m-%d").date()
            status_real = "Ativo" if datetime.now().date() <= dt_venc else "🔴 Expirado"
            lista_formatada.append({
                "Salão / Usuário": user,
                "Tipo": info["tipo"],
                "Vencimento": dt_venc.strftime("%d/%m/%Y"),
                "Situação": status_real
            })
            
        df_usuarios = pd.DataFrame(lista_formatada)
        st.dataframe(df_usuarios, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🗑️ Cancelar Conta Permanentemente")
        salao_remover = st.selectbox("Selecione o salão que deseja deletar:", ["Selecione..."] + list(usuarios_cadastrados.keys()))
        
        if st.button("Excluir Conta Permanentemente", type="primary"):
            if salao_remover != "Selecione...":
                del usuarios_cadastrados[salao_remover]
                salvar_usuarios(usuarios_cadastrados)
                st.warning(f"O acesso do salão '{salao_remover}' foi totalmente removido do servidor.")
                st.rerun()
            else:
                st.error("Selecione um salão válido para remover.")

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

nome_salao_formatado = st.session_state.usuario_logado.replace("_", " ").title()
st.title(f"✂️ {nome_salao_formatado} - Gestão Financeira")

# Mostrar detalhes da licença do próprio usuário logado de maneira sutil
dados_proprios = usuarios_cadastrados[st.session_state.usuario_logado]
venc_f = datetime.strptime(dados_proprios['vencimento'], "%Y-%m-%d").strftime("%d/%m/%Y")
st.markdown(f"*Painel Exclusivo | Licença Tipo: **{dados_proprios['tipo']}** (Válida até {venc_f})*")
st.markdown("---")

# --- SIDEBAR: GERENCIAR SERVIÇOS ---
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
        
    st.markdown("---")
    if st.button("🚪 Sair do Painel", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_logado = None
        st.session_state.eh_admin = False
        st.rerun()

# --- ABAS DA TELA PRINCIPAL ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💰 Lançar Movimentação", "📜 Histórico de Caixa"])

# --- TAB 2: LANÇAR MOVIMENTAÇÃO (LAYOUT ULTRA PROFISSIONAL E LIMPO) ---
with tab2:
    st.markdown("### 🛠️ Central de Lançamentos")
    st.markdown("Clique nos quadros abaixo para abrir os formulários de registro.")
    
    # QUADRO 1: ENTRADAS (ATENDIMENTO PAGO)
    with st.expander("📥 REGISTRAR ENTRADA (Atendimento Concluído e Pago)", expanded=False):
        if list(st.session_state.servicos.keys()):
            servico_selecionado = st.selectbox("Selecione o Serviço realizado:", list(st.session_state.servicos.keys()), key="selectbox_servico_atendimento")
            preco_sugerido = st.session_state.servicos[servico_selecionado]
            
            preco_final = st.number_input("Valor Cobrado (R$):", value=preco_sugerido, step=1.0, key=f"entrada_val_{servico_selecionado}")
            data_entrada = st.date_input("Data do Atendimento:", datetime.now().date(), key="entrada_data")
            
            if st.button("Confirmar e Lançar Entrada", type="primary"):
                nova_linha = pd.DataFrame([{
                    "Data": pd.to_datetime(data_entrada),
                    "Tipo": "Entrada",
                    "Descrição": f"Atendimento: {servico_selecionado}",
                    "Valor": preco_final
                }])
                st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True)
                salvar_fluxo(st.session_state.fluxo_caixa) 
                st.success("Entrada financeira registrada!")
                st.rerun()
        else:
            st.info("Cadastre pelo menos um serviço na barra lateral para registrar entradas.")

    # QUADRO 2: SAÍDAS (DESPESAS)
    with st.expander("📤 REGISTRAR SAÍDA (Pagamento de Contas e Custos)", expanded=False):
        descricao_saida = st.text_input("Descrição da Despesa (Ex: Luz, Aluguel, Produtos):")
        valor_saida = st.number_input("Valor da Despesa (R$):", min_value=0.0, step=5.0, key="saida_val")
        data_saida = st.date_input("Data do Pagamento:", datetime.now().date(), key="saida_data")
        
        if st.button("Confirmar e Lançar Saída", type="primary"):
            if descricao_saida and valor_saida > 0:
                nova_linha = pd.DataFrame([{
                    "Data": pd.to_datetime(data_saida),
                    "Tipo": "Saída",
                    "Descrição": descricao_saida,
                    "Valor": -valor_saida  
                }])
                st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True)
                salvar_fluxo(st.session_state.fluxo_caixa) 
                st.success("Despesa lançada com sucesso!")
                st.rerun()
            else:
                st.error("Preencha a descrição e o valor da despesa.")

    # QUADRO 3: PRODUTO FIADO (PENDÊNCIAS)
    with st.expander("⏳ REGISTRAR PENDÊNCIA (Corte / Serviço Fiado)", expanded=False):
        if list(st.session_state.servicos.keys()):
            nome_devedor = st.text_input("Nome do Cliente (Quem ficou devendo?):", key="input_nome_devedor").strip()
            servico_pendente = st.selectbox("Selecione o Serviço feito:", list(st.session_state.servicos.keys()), key="selectbox_servico_pendencia")
            preco_sugerido_p = st.session_state.servicos[servico_pendente]
            
            preco_final_p = st.number_input("Valor Pendente (R$):", value=preco_sugerido_p, step=1.0, key=f"pendencia_val_{servico_pendente}")
            data_pendencia = st.date_input("Data da Realização:", datetime.now().date(), key="pendencia_data")
            
            if st.button("Salvar Registro de Fiado", type="primary"):
                if nome_devedor:
                    nova_linha = pd.DataFrame([{
                        "Data": pd.to_datetime(data_pendencia),
                        "Tipo": "Pendência",
                        "Descrição": f"Fiado de: {nome_devedor} ({servico_pendente})",
                        "Valor": preco_final_p
                    }])
                    st.session_state.fluxo_caixa = pd.concat([st.session_state.fluxo_caixa, nova_linha], ignore_index=True)
                    salvar_fluxo(st.session_state.fluxo_caixa) 
                    st.success(f"Pendência de {nome_devedor} anotada.")
                    st.rerun()
                else:
                    st.error("Por favor, preencha o nome do cliente.")
        else:
            st.info("Cadastre pelo menos um serviço na barra lateral para registrar pendências.")

    # QUADRO 4: CONFIRMAR PAGAMENTO DE FIADO
    with st.expander("✅ CONFIRMAR RECEBIMENTO DE FIADO (Dar Baixa)", expanded=False):
        df_fluxo_atual = st.session_state.fluxo_caixa
        df_pendencias = df_fluxo_atual[df_fluxo_atual['Tipo'] == 'Pendência']
        
        if not df_pendencias.empty:
            opcoes_pendentes = {}
            for idx, row in df_pendencias.iterrows():
                try:
                    data_f = pd.to_datetime(row['Data']).strftime('%d/%m/%Y')
                except:
                    data_f = str(row['Data'])
                label_opcao = f"{row['Descrição']} - R$ {abs(row['Valor']):.2f} ({data_f})"
                opcoes_pendentes[label_opcao] = idx
                
            pendencia_selecionada = st.selectbox("Selecione o cliente que está pagando agora:", list(opcoes_pendentes.keys()), key="sb_dar_baixa_fiado")
            
            if st.button("Baixar Débito e Registrar Entrada de Caixa", type="primary", key="btn_confirmar_baixa_fiado"):
                idx_alterar = opcoes_pendentes[pendencia_selecionada]
                
                st.session_state.fluxo_caixa.at[idx_alterar, 'Tipo'] = 'Entrada'
                st.session_state.fluxo_caixa.at[idx_alterar, 'Data'] = pd.to_datetime(datetime.now().date())
                
                desc_anterior = st.session_state.fluxo_caixa.at[idx_alterar, 'Descrição']
                st.session_state.fluxo_caixa.at[idx_alterar, 'Descrição'] = desc_anterior.replace("Fiado de:", "Recebido Fiado:") + " [PAGO HOJE]"
                
                salvar_fluxo(st.session_state.fluxo_caixa)
                st.success("Sucesso! O valor foi migrado para as Entradas de hoje.")
                st.rerun()
        else:
            st.info("Não existem contas fiadas em aberto no momento.")

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
            
            def colorir_linhas(row):
                if row['Tipo'] == 'Entrada':
                    return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
                elif row['Tipo'] == 'Saída':
                    return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)
                elif row['Tipo'] == 'Pendência':
                    return ['background-color: #fff3cd; color: #856404; font-weight: bold'] * len(row)
                return [''] * len(row)
            
            tabela_estilizada = df_visualizacao.style.apply(colorir_linhas, axis=1).format(
                subset=["Valor"], 
                formatter=lambda x: f"R$ {x:.2f}".replace('.', ',')
            )
            
            st.dataframe(tabela_estilizada, use_container_width=True)
        else:
            st.info("Nenhum registro encontrado para este mês.")
    else:
        st.info("Nenhuma movimentação registrada até o momento.")
