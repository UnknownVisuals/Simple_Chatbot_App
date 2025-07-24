import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
import tempfile

# Muat environment variables dari file .env
load_dotenv()

# Konfigurasi API key Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.title("My First AI Chatbot")

# Daftar peran (role) yang telah ditentukan sebelumnya untuk AI
# Setiap peran memiliki prompt sistem (perintah) dan ikon sendiri
ROLES = {
    "General Assistant": {
        "system_prompt": "You are a helpful AI assistant. Be friendly, informative, and professional.",
        "icon": "🤖",
    },
    "Customer Service": {
        "system_prompt": """You are a professional customer service representative. You should:
        - Be polite, empathetic, and patient
        - Focus on solving customer problems
        - Ask clarifying questions when needed
        - Offer alternatives and solutions
        - Maintain a helpful and positive tone
        - If you can't solve something, explain how to escalate""",
        "icon": "📞",
    },
    "Technical Support": {
        "system_prompt": """You are a technical support specialist. You should:
        - Provide clear, step-by-step technical solutions
        - Ask about system specifications and error messages
        - Suggest troubleshooting steps in logical order
        - Explain technical concepts in simple terms
        - Be patient with non-technical users""",
        "icon": "⚙️",
    },
    "Teacher/Tutor": {
        "system_prompt": """You are an educational tutor. You should:
        - Explain concepts clearly and simply
        - Use examples and analogies to aid understanding
        - Encourage learning and curiosity
        - Break down complex topics into manageable parts
        - Provide practice questions or exercises when appropriate""",
        "icon": "📚",
    },
}


# Fungsi untuk mengekstrak teks dari file PDF yang diunggah
def extract_text_from_pdf(pdf_file):
    """Mengekstrak teks dari file PDF yang diunggah"""
    try:
        # Buat file sementara untuk menyimpan PDF yang diunggah
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_file.getvalue())
            tmp_file_path = tmp_file.name

        # Buka dan baca file PDF sementara
        with open(tmp_file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            # Loop setiap halaman dalam PDF untuk mengambil teksnya
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

        # Hapus file sementara setelah selesai diproses
        os.unlink(tmp_file_path)
        return text
    except Exception as e:
        # Tampilkan pesan error jika gagal mengekstrak teks
        st.error(f"Error extracting PDF text: {str(e)}")
        return None


# --- Bagian Sidebar untuk Konfigurasi ---
with st.sidebar:
    st.header("⚙️ Configuration")

    # Pilihan untuk mengubah peran (role) AI
    st.subheader("🎭 Select Role")
    selected_role = st.selectbox(
        "Choose assistant role:", options=list(ROLES.keys()), index=0
    )

    # Bagian untuk mengunggah file PDF sebagai basis pengetahuan (knowledge base)
    st.subheader("📚 Knowledge Base")
    uploaded_files = st.file_uploader(
        "Upload PDF documents:", type=["pdf"], accept_multiple_files=True
    )

    # Proses file yang diunggah
    if uploaded_files:
        # Inisialisasi 'knowledge_base' di session_state jika belum ada
        if "knowledge_base" not in st.session_state:
            st.session_state.knowledge_base = ""

        # Ekstrak teks dari file-file yang baru diunggah
        new_knowledge = ""
        for pdf_file in uploaded_files:
            st.write(f"📄 Processing: {pdf_file.name}")
            pdf_text = extract_text_from_pdf(pdf_file)
            if pdf_text:
                # Tambahkan teks dari PDF ke variabel dengan format penanda
                new_knowledge += f"\n\n=== DOCUMENT: {pdf_file.name} ===\n{pdf_text}"

        # Perbarui basis pengetahuan jika ada konten baru dan belum ada sebelumnya
        if new_knowledge and new_knowledge not in st.session_state.knowledge_base:
            st.session_state.knowledge_base += new_knowledge
            st.success(f"✅ Processed {len(uploaded_files)} document(s)")

    # Tombol untuk menghapus seluruh basis pengetahuan
    if st.button("🗑️ Clear Knowledge Base"):
        st.session_state.knowledge_base = ""
        st.success("Knowledge base cleared!")

    # Tampilkan status basis pengetahuan (jumlah kata)
    if "knowledge_base" in st.session_state and st.session_state.knowledge_base:
        word_count = len(st.session_state.knowledge_base.split())
        st.metric("Knowledge Base", f"{word_count} words")

# --- Inisialisasi Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Antarmuka Chat Utama ---
# Tampilkan riwayat percakapan
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Inisialisasi model
model = genai.GenerativeModel("gemini-1.5-flash")

if prompt := st.chat_input("Tanya sesuatu..."):
    st.chat_message("user").markdown(prompt)

    response = model.generate_content(prompt)

    with st.chat_message("assistant"):
        st.markdown(response.text)
