import streamlit as st
import openai
import os
from PIL import Image
import time
import json
import hashlib
import io
import base64
import pdfplumber
import easyocr
import streamlit.components.v1 as components
import speech_recognition as sr

# Configurações iniciais
st.set_page_config(
    page_title="AD&M IA",
    page_icon="💙",
    layout="wide",
)

# Ocultar elementos do Streamlit
st.markdown("""
    <style>
    [data-testid="stToolbar"], header, footer, iframe[title="streamlit branding"] {
        visibility: hidden !important;
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

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

if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []
if "perguntas_respondidas" not in st.session_state:
    st.session_state.perguntas_respondidas = set()

MAX_HISTORICO = 5
reader = easyocr.Reader(['pt'], gpu=False)

def salvar_estado():
    with open("estado_bot.json", "w") as f:
        json.dump({
            "mensagens_chat": st.session_state.mensagens_chat,
            "perguntas_respondidas": list(st.session_state.perguntas_respondidas)
        }, f)

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

def extrair_texto_arquivo(uploaded_file):
    texto = ""
    try:
        if uploaded_file.name.endswith(".txt"):
            texto = uploaded_file.read().decode("utf-8")

        elif uploaded_file.name.endswith(".pdf"):
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    texto += page.extract_text() + "\n"

        elif uploaded_file.name.endswith((".png", ".jpg", ".jpeg")):
            image_bytes = uploaded_file.read()
            resultado = reader.readtext(image_bytes, detail=0, paragraph=True)
            texto = "\n".join(resultado)

    except Exception as e:
        st.warning(f"Erro ao processar {uploaded_file.name}: {e}")
    return texto

def carregar_contexto(uploaded_files):
    contexto = ""
    arquivos_contexto = ["contexto1.txt", "contexto2.txt", "contexto3.txt", "contexto4.txt"]
    for arquivo in arquivos_contexto:
        if os.path.exists(arquivo):
            with open(arquivo, "r", encoding="utf-8") as f:
                contexto += f.read() + "\n\n"

    for arquivo in uploaded_files:
        texto_arquivo = extrair_texto_arquivo(arquivo)
        if texto_arquivo:
            contexto += f"\n\n--- Conteúdo de {arquivo.name} ---\n{texto_arquivo}\n"

    return contexto

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

def gerar_resposta(texto_usuario, contexto):
    pergunta_hash = hashlib.sha256(texto_usuario.strip().lower().encode()).hexdigest()
    if pergunta_hash in st.session_state.perguntas_respondidas:
        return "Essa pergunta já foi respondida anteriormente. Deseja que eu a aprofunde ou traga uma perspectiva diferente?"

    chunks = dividir_texto(contexto)
    chunks_relevantes = selecionar_chunks_relevantes(texto_usuario, chunks)

    contexto_pergunta = "Você é a AD&M IA...\n"
    for i, chunk in enumerate(chunks_relevantes):
        contexto_pergunta += f"\n--- Parte {i+1} do Contexto ---\n{chunk}\n"

    mensagens = [{"role": "system", "content": contexto_pergunta}]
    historico = st.session_state.mensagens_chat[-MAX_HISTORICO:]
    for msg in historico:
        mensagens.append({"role": "user", "content": msg["user"]})
        if msg["bot"]:
            mensagens.append({"role": "assistant", "content": msg["bot"]})
    mensagens.append({"role": "user", "content": texto_usuario})

    for tentativa in range(3):
        try:
            time.sleep(1)
            resposta = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=mensagens,
                temperature=0.5,
                max_tokens=800
            )
            st.session_state.perguntas_respondidas.add(pergunta_hash)
            return resposta["choices"][0]["message"]["content"]
        except Exception as e:
            if tentativa < 2:
                time.sleep(2)
                continue
            else:
                return f"Erro ao gerar a resposta: {str(e)}"

def exportar_historico():
    texto = ""
    for m in st.session_state.mensagens_chat:
        texto += f"Você: {m['user']}\nAD&M IA: {m['bot']}\n\n"
    return texto

# Sidebar
if LOGO_BOT:
    st.sidebar.image(LOGO_BOT, width=300)
else:
    st.sidebar.markdown("**Logo não encontrada**")

uploaded_files = st.sidebar.file_uploader(
    "📎 Enviar arquivos de contexto (.txt, .pdf, .png, .jpg)",
    type=["txt", "pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

api_key = st.sidebar.text_input("🔑 Chave API OpenAI", type="password", placeholder="Insira sua chave API")
if api_key:
    openai.api_key = api_key
    if st.sidebar.button("🧹 Limpar Histórico do Chat", key="limpar_historico"):
        limpar_historico()
        st.sidebar.success("Histórico do chat limpo com sucesso!")
    if st.sidebar.button("📄 Exportar Histórico", key="exportar_txt"):
        historico = exportar_historico()
        b64 = base64.b64encode(historico.encode()).decode()
        href = f'<a href="data:file/txt;base64,{b64}" download="historico_chat_adm.txt">Clique aqui para baixar o histórico (.txt)</a>'
        st.sidebar.markdown(href, unsafe_allow_html=True)
else:
    st.warning("Por favor, insira sua chave de API para continuar.")

contexto = carregar_contexto(uploaded_files)
user_input = st.chat_input("💬 Sua pergunta:")
if user_input and user_input.strip():
    st.session_state.mensagens_chat.append({"user": user_input, "bot": None})
    resposta = gerar_resposta(user_input, contexto)
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


