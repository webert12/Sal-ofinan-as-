import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import json

# ==============================
# FUSO HORÁRIO OFICIAL BRASIL
# ==============================
FUSO_BR = ZoneInfo("America/Sao_Paulo")

def agora_brasil():
    return datetime.now(FUSO_BR)

# ==============================
# DATA FIXA DO BRASIL (ANTI BUG)
# ==============================
def hoje_brasil():
    return agora_brasil().date()

# Mantém sempre a data correta do Brasil
if "data_brasil" not in st.session_state:
    st.session_state.data_brasil = hoje_brasil()

# Configuração da página
st.set_page_config(
    page_title="Gestão Financeira - Salão",
    layout="wide",
    page_icon="✂️"
)

USUARIOS_FILE = "usuarios.json"

# --- CONFIGURAÇÃO DO ADMINISTRADOR MESTRE (VOCÊ) ---
ADMIN_MESTRE_USER = "admin"
ADMIN_MESTRE_PASS = "master2026"

# --- FUNÇÕES DE GERENCIAMENTO DE USUÁRIOS (COM TRATAMENTO DE VALIDADE) ---
def carregar_usuarios():

    hoje_str = st.session_state.data_brasil.strftime("%Y-%m-%d")

    vencimento_padrao = (
        agora_brasil() + timedelta(days=30)
    ).strftime("%Y-%m-%d")

    if os.path.exists(USUARIOS_FILE):

        with open(USUARIOS_FILE, "r") as f:
            dados = json.load(f)

        # Migração automática caso o arquivo antigo esteja no formato antigo
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
            "vencimento": (
                agora_brasil() + timedelta(days=7)
            ).strftime("%Y-%m-%d"),
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

    return (
        f"servicos_{usuario}.json",
        f"fluxo_caixa_{usuario}.csv"
    )

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

            # CORREÇÃO: Forçar conversão para data pura
            df['Data'] = pd.to_datetime(
                df['Data'],
                errors='coerce'
            ).dt.date

            return df

        except Exception:
            return pd.DataFrame(
                columns=["Data", "Tipo", "Descrição", "Valor"]
            )

    return pd.DataFrame(
        columns=["Data", "Tipo", "Descrição", "Valor"]
    )

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

        usuario_input = st.text_input(
            "Usuário do Salão ou ADM:"
        ).strip().lower()

        senha_input = st.text_input(
            "Senha:",
            type="password"
        )

        botao_entrar = st.form_submit_button(
            "Entrar no Sistema"
        )

        if botao_entrar:

            if (
                usuario_input == ADMIN_MESTRE_USER
                and senha_input == ADMIN_MESTRE_PASS
            ):

                st.session_state.autenticado = True
                st.session_state.usuario_logado = "Administrador"
                st.session_state.eh_admin = True

                st.success("Acesso master concedido!")
                st.rerun()

            elif (
                usuario_input in usuarios_cadastrados
                and usuarios_cadastrados[usuario_input]["senha"] == senha_input
            ):

                # --- VALIDAÇÃO DE EXPIRAÇÃO AUTOMÁTICA ---
                dados_user = usuarios_cadastrados[usuario_input]

                data_vencimento = datetime.strptime(
                    dados_user["vencimento"],
                    "%Y-%m-%d"
                ).date()

                hoje = st.session_state.data_brasil

                if (
                    hoje > data_vencimento
                    or dados_user.get("status") == "Suspenso"
                ):

                    st.error(
                        f"❌ ACESSO BLOQUEADO! "
                        f"O período de {dados_user['tipo']} venceu em "
                        f"{data_vencimento.strftime('%d/%m/%Y')}. "
                        f"Entre em contato com o suporte para renovação."
                    )

                    st.stop()

                st.session_state.autenticado = True
                st.session_state.usuario_logado = usuario_input
                st.session_state.eh_admin = False

                st.session_state.servicos = carregar_servicos()
                st.session_state.fluxo_caixa = carregar_fluxo()

                st.success(f"Carregando painel de {usuario_input}...")
                st.rerun()

            else:
                st.error(
                    "Usuário ou senha incorretos. "
                    "Verifique suas credenciais."
                )

    st.stop()

# =====================================================================
# --- INTERFACE 1: PAINEL DO ADMINISTRADOR MESTRE ---
# =====================================================================

if st.session_state.eh_admin:

    st.title(
        "👑 Central do Administrador - Gestão de Clientes & Licenças"
    )

    st.markdown(
        "Aqui você cadastra novos salões, define períodos de teste "
        "e gerencia vencimentos."
    )

    st.markdown("---")

    col_cad, col_lista = st.columns([1, 1.2])

    with col_cad:

        st.subheader("➕ Registrar ou Renovar Salão")

        with st.form("form_cadastro_cliente"):

            novo_usuario = st.text_input(
                "Identificador/Usuário do Salão:",
                help="Ex: salao_do_bairro"
            ).strip().lower()

            nova_senha = st.text_input(
                "Senha de Acesso:",
                type="password"
            ).strip()

            tipo_conta = st.selectbox(
                "Tipo de Conta:",
                ["Teste", "Cliente"]
            )

            dias_validade = st.number_input(
                "Dias de Acesso/Validade:",
                min_value=1,
                max_value=365,
                value=7 if tipo_conta == "Teste" else 30
            )

            btn_cadastrar = st.form_submit_button(
                "Salvar / Atualizar Conta",
                type="primary"
            )

            if btn_cadastrar:

                if not novo_usuario or not nova_senha:

                    st.error(
                        "Preencha o usuário e senha para salvar."
                    )

                elif novo_usuario == ADMIN_MESTRE_USER:

                    st.error("Nome reservado do sistema.")

                else:

                    vencimento_calculado = (
                        agora_brasil() + timedelta(days=dias_validade)
                    ).strftime("%Y-%m-%d")

                    usuarios_cadastrados[novo_usuario] = {
                        "senha": nova_senha,
                        "tipo": tipo_conta,
                        "vencimento": vencimento_calculado,
                        "status": "Ativo"
                    }

                    salvar_usuarios(usuarios_cadastrados)

                    st.success(
                        f"Sucesso! Salão '{novo_usuario}' configurado "
                        f"como '{tipo_conta}' válido por "
                        f"{dias_validade} dias "
                        f"(Até "
                        f"{datetime.strptime(vencimento_calculado, '%Y-%m-%d').strftime('%d/%m/%Y')}"
                        f")."
                    )

                    st.rerun()

    with col_lista:

        st.subheader(
            "👥 Salões Cadastrados e Status de Licença"
        )

        lista_formatada = []

        for user, info in usuarios_cadastrados.items():

            dt_venc = datetime.strptime(
                info['vencimento'],
                "%Y-%m-%d"
            ).date()

            status_real = (
                "Ativo"
                if st.session_state.data_brasil <= dt_venc
                else "🔴 Expirado"
            )

            lista_formatada.append({
                "Salão / Usuário": user,
                "Tipo": info["tipo"],
                "Vencimento": dt_venc.strftime("%d/%m/%Y"),
                "Situação": status_real
            })

        df_usuarios = pd.DataFrame(lista_formatada)

        st.dataframe(
            df_usuarios,
            use_container_width=True,
            hide_index=True
        )
