import streamlit as st
import openai
import os
from PIL import Image
import time
import json
import streamlit.components.v1 as components
import speech_recognition as sr

# Configurações iniciais
st.set_page_config(
    page_title="AD&M IA",
    page_icon="💙",
    layout="wide",
)

# CSS personalizado para estilizar a interface
theme_css = """
<style>
/* Esconde elementos indesejados */
._link_gzau3_10, ._profileContainer_gzau3_53,
footer, iframe[title="streamlit branding"],
[data-testid="stToolbar"], div[data-testid="stActionButtonIcon"],
div[style*="position: fixed"][style*="right: 0px"][style*="bottom: 0px"] {
    display: none !important;
    visibility: hidden !important;
}

/* Ajuste de estilos */
header {visibility: hidden;}
.block-container {padding-top: 1rem;}

/* Sidebar */
.stSidebar .stMarkdown, .stSidebar label,
.stSidebar .stTextInput, .stSidebar .stTextArea,
.stSidebar .stButton, .stSidebar .stExpander {
    color: white !important;
}

/* Principal */
.stMarkdown, .stTextInput, .stTextArea,
.stButton, .stExpander {
    color: black !important;
}

/* Uploader */
.stFileUploader > div > div {
    background-color: white;
    color: black;
    border-radius: 10px;
    padding: 10px;
    border: 1px solid #ccc;
}
.stFileUploader label {
    color: black !important;
}
.stFileUploader button {
    background-color: #8dc50b;
    color: white;
    border-radius: 5px;
    border: none;
    padding: 8px 16px;
}

/* Notificações */
div[data-testid="stNotification"] > div > div {
    background-color: white !important;
    color: black !important;
    border-radius: 10px !important;
    padding: 10px !important;
    border: 1px solid #ccc !important;
}
div[data-testid="stNotification"] > div > div > div:first-child {
    color: #8dc50b !important;
}

/* Subtítulo */
.subtitulo {
    font-size: 16px !important;
    color: black !important;
}

/* Chat input */
.stChatInput input, .stChatInput textarea {
    color: white !important;
}
.stChatInput input::placeholder, .stChatInput textarea::placeholder {
    color: white !important;
    opacity: 1;
}

/* Logo */
.stImage > img {
    filter: drop-shadow(0 0 0 #8dc50b);
}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)

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
    '<cp class="subtitulo">Sou uma IA desenvolvida pela AD&M consultoria empresarial, reunindo estudos e documentos sobre seu projeto e estou aqui para te ajudar 😁 !</p>',
    unsafe_allow_html=True
)

# Estado
if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []

def salvar_estado():
    with open("estado_bot.json", "w") as f:
        json.dump({"mensagens_chat": st.session_state.mensagens_chat}, f)

def carregar_estado():
    if os.path.exists("estado_bot.json"):
        with open("estado_bot.json", "r") as f:
            estado = json.load(f)
            st.session_state.mensagens_chat = estado.get("mensagens_chat", [])
carregar_estado()

def limpar_historico():
    st.session_state.mensagens_chat = []
    salvar_estado()

def carregar_contexto():
    contexto = ""
    arquivos_contexto = ["contexto1.txt", "contexto2.txt", "contexto3.txt", "contexto4.txt"]
    for arquivo in arquivos_contexto:
        if os.path.exists(arquivo):
            with open(arquivo, "r", encoding="utf-8") as f:
                contexto += f.read() + "\n\n"
        else:
            st.error(f"Arquivo de contexto não encontrado: {arquivo}")
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

    chunks = dividir_texto(contexto)
    chunks_relevantes = selecionar_chunks_relevantes(texto_usuario, chunks)

    contexto_pergunta = """
Você é a AD&M IA, uma inteligência artificial treinada com base nos projetos, documentos e metodologias utilizadas pela AD&M Consultoria Empresarial. Seu papel é:

1. Fornecer respostas claras, educadas e baseadas em dados reais;
2. Gerar insights estratégicos e práticos que o cliente possa aplicar imediatamente;
3. Sempre responder com objetividade, linguagem simples e foco em Administração, Gestão de Processos, Planejamento Estratégico e Soluções Empresariais;
4. Se basear no conteúdo a seguir (trechos de projetos anteriores) para responder a pergunta;
5. Caso não encontre resposta no contexto, responda com sugestões realistas baseadas em boas práticas de consultoria júnior.

Mantenha sempre um tom profissional e propositivo.

Abaixo estão trechos relevantes para sua análise:
"""
    for i, chunk in enumerate(chunks_relevantes):
        contexto_pergunta += f"\n--- Parte {i+1} do Contexto ---\n{chunk}\n"

    mensagens = [
        {"role": "system", "content": contexto_pergunta},
        {"role": "user", "content": texto_usuario}
    ]

    for tentativa in range(3):
        try:
            time.sleep(1)
            resposta = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=mensagens,
                temperature=0.5,
                max_tokens=800
            )
            return resposta["choices"][0]["message"]["content"]
        except Exception as e:
            if tentativa < 2:
                time.sleep(2)
                continue
            else:
                return f"Erro ao gerar a resposta: {str(e)}"

# Sidebar
if LOGO_BOT:
    st.sidebar.image(LOGO_BOT, width=300)
else:
    st.sidebar.markdown("**Logo não encontrada**")

api_key = st.sidebar.text_input("🔑 Chave API OpenAI", type="password", placeholder="Insira sua chave API")
if api_key:
    openai.api_key = api_key
    if st.sidebar.button("🧹 Limpar Histórico do Chat", key="limpar_historico"):
        limpar_historico()
        st.sidebar.success("Histórico do chat limpo com sucesso!")
else:
    st.warning("Por favor, insira sua chave de API para continuar.")

user_input = st.chat_input("💬 Sua pergunta:")
if user_input and user_input.strip():
    st.session_state.mensagens_chat.append({"user": user_input, "bot": None})
    resposta = gerar_resposta(user_input)
    st.session_state.mensagens_chat[-1]["bot"] = resposta
    salvar_estado()

with st.container():
    if st.session_state.mensagens_chat:
        for mensagem in st.session_state.mensagens_chat:
            if mensagem["user"]:
                with st.chat_message("user"):
                    st.markdown(f"**Você:** {mensagem['user']}", unsafe_allow_html=True)
            if mensagem["bot"]:
                with st.chat_message("assistant"):
                    st.markdown(f"**AD&M IA:**\n\n{mensagem['bot']}", unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            st.markdown("*AD&M IA:* Nenhuma mensagem ainda.", unsafe_allow_html=True)

