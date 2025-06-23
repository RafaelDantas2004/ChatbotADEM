# VERSÃO CORRIGIDA E SIMPLIFICADA

import streamlit as st
import openai
import os
from PIL import Image
import time
import json
import hashlib
import glob

# Configurações iniciais
st.set_page_config(
    page_title="AD&M IA",
    page_icon="💙",
    layout="wide",
)

# -------------------------------------------------------------------
# BLOCO DE CSS PROBLEMÁTICO FOI COMPLETAMENTE REMOVIDO PARA GARANTIR
# QUE A BARRA LATERAL VOLTE A FUNCIONAR NORMALMENTE.
# -------------------------------------------------------------------

# Caminhos das logos
LOGO_BOT_PATH = "assets/Cópia de Logo BRANCA HD cópia.png"
ICON_PATH = "assets/icon_cade.png"

LOGO_BOT = Image.open(LOGO_BOT_PATH) if os.path.exists(LOGO_BOT_PATH) else None

# Header com ícone e título
if os.path.exists(ICON_PATH):
    col1, col2 = st.columns([1.5, 4])
    with col1:
        st.image(ICON_PATH, width=100)
    with col2:
        st.title("AD&M IA")
else:
    st.title("AD&M IA")

st.markdown(
    '<p class="subtitulo">Sou uma IA desenvolvida pela AD&M consultoria empresarial, reunindo estudos e documentos sobre seu projeto e estou aqui para te ajudar 😁 !</p>',
    unsafe_allow_html=True
)

if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []
if "perguntas_respondidas" not in st.session_state:
    st.session_state.perguntas_respondidas = set()

def salvar_estado():
    try:
        with open("estado_bot.json", "w") as f:
            json.dump({
                "mensagens_chat": st.session_state.mensagens_chat,
                "perguntas_respondidas": list(st.session_state.perguntas_respondidas)
            }, f)
    except Exception as e:
        st.error(f"Erro ao salvar estado: {e}")

def carregar_estado():
    if os.path.exists("estado_bot.json"):
        with open("estado_bot.json", "r") as f:
            estado = json.load(f)
            st.session_state.mensagens_chat = estado.get("mensagens_chat", [])
            st.session_state.perguntas_respondidas = set(estado.get("perguntas_respondidas", []))
carregar_estado()

def limpar_historico():
    st.session_state.mensagens_chat = []
    st.session_state.perguntas_respondidas = set()
    salvar_estado()

def carregar_contexto():
    contexto = ""
    for caminho in sorted(glob.glob("contextos/*.txt")):
        with open(caminho, "r", encoding="utf-8") as f:
            contexto += f.read() + "\n\n"
    return contexto

contexto = carregar_contexto()

def dividir_texto(texto, max_tokens=800):
    palavras = texto.split()
    chunks, chunk_atual = [], ""
    for palavra in palavras:
        if len(chunk_atual.split()) + len(palavra.split()) <= max_tokens:
            chunk_atual += palavra + " "
        else:
            chunks.append(chunk_atual.strip())
            chunk_atual = palavra + " "
    if chunk_atual:
        chunks.append(chunk_atual.strip())
    return chunks

def selecionar_chunks_relevantes(pergunta, chunks):
    palavras_chave = pergunta.lower().split()
    return [c for c in chunks if any(p in c.lower() for p in palavras_chave)][:4]

def gerar_resposta(texto_usuario):
    if not contexto:
        return "Erro: Nenhum contexto carregado."

    pergunta_hash = hashlib.sha256(texto_usuario.strip().lower().encode()).hexdigest()
    if pergunta_hash in st.session_state.perguntas_respondidas:
        return "Essa pergunta já foi respondida anteriormente. Deseja que eu a aprofunde ou traga uma perspectiva diferente?"

    chunks = dividir_texto(contexto)
    chunks_relevantes = selecionar_chunks_relevantes(texto_usuario, chunks)

    contexto_pergunta = """
Você é a AD&M IA, uma inteligência artificial treinada com base nos projetos, documentos e metodologias utilizadas pela AD&M Consultoria Empresarial, para prestar auxílio ao cliente do projeto que faz parte do seu contexto. Seu papel é:
1. Fornecer respostas claras, educadas e baseadas em dados reais e nos documentos oferecidos do projeto;
2. Gerar insights estratégicos e práticos que o cliente possa aplicar imediatamente, sabendo exatamente o que ele precisa fazer para colocar em prática as suas ideias;
3. Sempre responder com objetividade, linguagem simples e foco em Administração, Gestão de Processos, Planejamento Estratégico e Soluções Empresariais;
4. Se basear no conteúdo a seguir (trechos de projetos anteriores) para responder a pergunta;
5. Caso não encontre resposta no contexto, responda com sugestões realistas baseadas em boas práticas de consultorias empresariais de referência global.
Mantenha sempre um tom profissional e propositivo.
Abaixo estão trechos relevantes para sua análise:
"""
    for i, chunk in enumerate(chunks_relevantes):
        contexto_pergunta += f"\n--- Parte {i+1} do Contexto ---\n{chunk}\n"

    mensagens = [{"role": "system", "content": contexto_pergunta}]
    for msg in st.session_state.mensagens_chat:
        mensagens.append({"role": "user", "content": msg["user"]})
        if msg["bot"]:
            mensagens.append({"role": "assistant", "content": msg["bot"]})
    mensagens.append({"role": "user", "content": texto_usuario})

    for tentativa in range(3):
        try:
            with st.spinner("Pensando..."):
                time.sleep(1)
                resposta = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=mensagens,
                    temperature=0.6,
                    max_tokens=800
                )
                st.session_state.perguntas_respondidas.add(pergunta_hash)
                return resposta.choices[0].message["content"]
        except Exception as e:
            if tentativa < 2:
                time.sleep(2)
                continue
            else:
                st.error(f"Erro na API OpenAI: {str(e)}")
                return f"Desculpe, ocorreu um erro ao tentar gerar a resposta: {str(e)}"

# Sidebar - Agora deve funcionar sem problemas
st.sidebar.title("Configurações e Ações")
if LOGO_BOT:
    st.sidebar.image(LOGO_BOT, use_column_width=True)
else:
    st.sidebar.markdown("**Logo não encontrada**")

api_key = st.sidebar.text_input("🔑 Chave API OpenAI", type="password", placeholder="Insira sua chave API aqui")

if st.sidebar.button("🧹 Limpar Histórico do Chat"):
    limpar_historico()
    st.rerun()

if not api_key:
    st.info("Por favor, insira sua chave de API OpenAI na barra lateral para começar.")
    st.stop()

openai.api_key = api_key

# Lógica do Chat
if user_input := st.chat_input("💬 Sua pergunta:"):
    st.session_state.mensagens_chat.append({"user": user_input, "bot": None})
    resposta_bot = gerar_resposta(user_input)
    st.session_state.mensagens_chat[-1]["bot"] = resposta_bot
    salvar_estado()
    st.rerun()

# Exibição do histórico
for mensagem in st.session_state.mensagens_chat:
    with st.chat_message("user"):
        st.markdown(f"**Você:** {mensagem['user']}")
    if mensagem["bot"]:
        with st.chat_message("assistant"):
            st.markdown(f"**AD&M IA:**\n\n{mensagem['bot']}")

if not st.session_state.mensagens_chat:
    st.info("O histórico de chat está vazio. Faça uma pergunta para começar!")



