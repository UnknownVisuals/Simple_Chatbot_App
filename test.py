# main.py
# ------------------------------------------------------------
# Telkom ConsultBot / KDMPedia Bot — All-in-One (POC)
# ------------------------------------------------------------
# Fitur:
# 1) Chat konsultatif (LLM)
# 2) Profil Perusahaan & Rekomendasi Pendekatan (LLM)
# 3) Tender Analyzer (PDF → OCR → Compliance via LLM)
# 4) Site Risk (Object Detection + LMM Advice + ringkasan teknis)
# 5) Voice Brief (STT → ringkasan 30 detik via LLM → TTS)
#
# Auth:
# - GEMINI_API_KEY dari .env / sidebar
# - Pilih skema header: bearer / x-api-key / apikey / bearer + x-api-key
#
# Endpoints dapat diubah dari sidebar.
# ------------------------------------------------------------

import os
import base64
import json
import requests
import streamlit as st
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# ---- Load .env ----
load_dotenv()

# --------------------------
# Endpoint default
# --------------------------
DEFAULT_ENDPOINTS = {
    "TELKOM_LLM": "https://telkom-ai-dag-api.apilogy.id/Telkom-LLM/0.0.4/llm",  # ← sudah pakai /llm
    "LMM": "https://telkom-ai-dag.api.apilogy.id/LargeMultimodalModel/0.0.2",
    "OCR": "http://telkom-ai-dag.api.apilogy.id/OCR_Document_Based/0.0.5",
    "OD": "http://telkom-ai-dag.api.apilogy.id/Object_Detection/0.0.1",
    "STT": "http://telkom-ai-dag.api.apilogy.id/Speech_To_Text/0.0.2",
    "TTS": "http://telkom-ai-dag.api.apilogy.id/Text_To_Speech/0.0.2",
}

# --------------------------
# System Prompt
# --------------------------
SYSTEM_PROMPT = (
    "Anda adalah Asisten Consultative Selling Telkom. Jawab ringkas, actionable, "
    "dan berbasis data. Selalu format hasil dengan blok berikut bila relevan:\n\n"
    "[Profil]\n"
    "[Pain Points]\n"
    "[Opportunity 90 Hari]\n"
    "[Risiko]\n"
    "[Next Best Action]\n"
    "[Talk Track 30 detik]\n"
    "[Data yang perlu diverifikasi]\n"
    "Jika pengguna mengunggah dokumen atau foto, lakukan analisis kontekstual."
)


# --------------------------
# Helpers
# --------------------------
def get_api_key() -> Optional[str]:
    key = st.session_state.get("GEMINI_API_KEY") or (
        st.secrets.get("GEMINI_API_KEY", None) if hasattr(st, "secrets") else None
    )
    key = key or os.getenv("GEMINI_API_KEY")
    # Strip whitespace and validate
    if key:
        key = key.strip()
        if len(key) < 10:  # Basic validation
            return None
    return key


def safe_get(d: Dict[str, Any], path: str, default=None):
    cur = d
    for p in path.split("."):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


def pretty_error(e: Exception) -> str:
    body = ""
    try:
        body = getattr(e, "response", None).text[:500]  # type: ignore
    except Exception:
        pass
    return f"⚠ {type(e).__name__}: {str(e)[:300]}{(' | body: ' + body) if body else ''}"


def b64encode_file(content_bytes: bytes, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(content_bytes).decode()


def ensure_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "endpoints" not in st.session_state:
        st.session_state.endpoints = DEFAULT_ENDPOINTS.copy()
    if "AUTH_SCHEME" not in st.session_state:
        st.session_state.AUTH_SCHEME = "bearer"


# --------------------------
# Auth & HTTP helpers
# --------------------------
def build_headers_for_scheme(scheme: str) -> Dict[str, str]:
    key = get_api_key()
    h = {"Content-Type": "application/json"}
    if not key:
        return h
    key = key.strip()

    if scheme == "bearer":
        h["Authorization"] = f"Bearer {key}"
    elif scheme == "x-api-key":
        h["x-api-key"] = key
    elif scheme == "apikey":
        h["apikey"] = key
    elif scheme == "bearer + x-api-key":
        h["Authorization"] = f"Bearer {key}"
        h["x-api-key"] = key

    # Debug logging (remove sensitive info)
    debug_headers = {
        k: (
            v[:20] + "..."
            if k.lower() in ["authorization", "x-api-key", "apikey"]
            else v
        )
        for k, v in h.items()
    }
    st.write(f"Debug - Headers being sent: {debug_headers}")

    return h


def post_json_auth(
    url: str, payload: Dict[str, Any], timeout: int = 120
) -> Dict[str, Any]:
    scheme = st.session_state.get("AUTH_SCHEME", "bearer")
    headers = build_headers_for_scheme(scheme)

    # Check if we have authentication
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "❌ No API key provided. Please set GEMINI_API_KEY in sidebar or .env file."
        )

    try:
        st.write(f"Debug - Making request to: {url}")
        st.write(f"Debug - Auth scheme: {scheme}")
        r = requests.post(url, json=payload, headers=headers, timeout=timeout)

        # Enhanced error handling for 401
        if r.status_code == 401:
            error_body = r.text[:500]
            raise RuntimeError(
                f"❌ Authentication failed (401). Please check your API key and auth scheme.\n"
                f"Current scheme: {scheme}\n"
                f"API Key (last 4 chars): ...{key[-4:] if key else 'None'}\n"
                f"Error details: {error_body}"
            )

        r.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"{e} | body: {r.text[:500]}") from e

    return r.json()


def post_json_plain(
    url: str, payload: Dict[str, Any], timeout: int = 120
) -> Dict[str, Any]:
    r = requests.post(
        url, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout
    )
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"{e} | body: {r.text[:500]}") from e
    return r.json()


# --------------------------
# API Wrappers
# --------------------------
def call_telkom_llm(
    user_text: str,
    system_prompt: str = SYSTEM_PROMPT,
    temperature: float = 0.2,
    max_tokens: int = 1200,
) -> str:
    url = st.session_state.endpoints["TELKOM_LLM"]
    payload = {
        "model": "telkom-llm-0.0.4",
        "inputs": {
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_text}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
    }
    resp = post_json_auth(url, payload, timeout=120)
    return safe_get(resp, "outputs.text", "Maaf, tidak ada keluaran dari LLM.")


def call_lmm(
    prompt: str,
    images_b64: Optional[List[str]] = None,
    files_b64: Optional[List[str]] = None,
) -> Dict[str, Any]:
    url = st.session_state.endpoints["LMM"]
    payload = {"inputs": {"prompt": prompt}}
    if images_b64:
        payload["inputs"]["images"] = images_b64
    if files_b64:
        payload["inputs"]["files"] = files_b64
    return post_json_auth(url, payload, timeout=150)


def call_ocr(pdf_b64: str) -> Dict[str, Any]:
    url = st.session_state.endpoints["OCR"]
    payload = {"file_base64": pdf_b64}
    return post_json_plain(url, payload, timeout=150)


def call_object_detection(
    image_b64: str, labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    if labels is None:
        labels = ["rack", "cable", "power-socket", "distribution-box", "ladder"]
    url = st.session_state.endpoints["OD"]
    payload = {"image_base64": image_b64, "labels": labels}
    return post_json_plain(url, payload, timeout=120)


def call_stt(audio_b64: str, language: str = "id") -> Dict[str, Any]:
    url = st.session_state.endpoints["STT"]
    payload = {"audio_base64": audio_b64, "language": language}
    return post_json_plain(url, payload, timeout=180)


def call_tts(text: str, voice: str = "id_female_1") -> Dict[str, Any]:
    url = st.session_state.endpoints["TTS"]
    payload = {"text": text, "voice": voice}
    return post_json_plain(url, payload, timeout=180)


# --------------------------
# UI
# --------------------------
st.set_page_config(page_title="Telkom ConsultBot (POC)", page_icon="🤖", layout="wide")
ensure_session_state()

with st.sidebar:
    st.header("⚙ Konfigurasi")

    # Enhanced API key input with validation
    current_key = os.getenv("GEMINI_API_KEY", "")
    st.session_state["GEMINI_API_KEY"] = st.text_input(
        "GEMINI_API_KEY",
        value=current_key,
        type="password",
        help="Nilai diambil otomatis dari .env; bisa diubah di sini.",
    )

    # API Key status indicator
    _k = get_api_key()
    if _k:
        if len(_k) < 10:
            st.error("⚠️ API key terlalu pendek. Periksa kembali.")
        else:
            st.success(f"✅ API Key loaded: ****{_k[-4:]}")
    else:
        st.error("❌ No API key detected")

    st.subheader("Auth")
    st.session_state.AUTH_SCHEME = st.selectbox(
        "Skema header untuk Telkom-LLM/LMM",
        options=["bearer", "x-api-key", "apikey", "bearer + x-api-key"],
        index=0,
        help="Coba x-api-key jika bearer gagal. Atau gunakan bearer + x-api-key.",
    )

    # Add troubleshooting tips
    st.info(
        "💡 Tips troubleshooting 401:\n"
        "• Pastikan API key benar\n"
        "• Coba ganti auth scheme\n"
        "• Periksa endpoint URL\n"
        "• Lihat debug info di bawah"
    )

    st.markdown("---")
    st.subheader("Endpoints")
    colL, colR = st.columns(2)
    with colL:
        st.text_input(
            "TELKOM_LLM",
            key="TELKOM_LLM",
            value=st.session_state.endpoints["TELKOM_LLM"],
        )
        st.text_input("OCR", key="OCR", value=st.session_state.endpoints["OCR"])
        st.text_input("STT", key="STT", value=st.session_state.endpoints["STT"])
    with colR:
        st.text_input("LMM", key="LMM", value=st.session_state.endpoints["LMM"])
        st.text_input("OD", key="OD", value=st.session_state.endpoints["OD"])
        st.text_input("TTS", key="TTS", value=st.session_state.endpoints["TTS"])
    if st.button("Simpan Endpoint"):
        for k in DEFAULT_ENDPOINTS:
            st.session_state.endpoints[k] = st.session_state[k]
        st.success("Endpoint tersimpan ✅")

    st.markdown("---")
    st.subheader("Tes Koneksi API")
    colt1, colt2 = st.columns(2)
    with colt1:
        if st.button("Test Telkom-LLM"):
            if not get_api_key():
                st.error("❌ Set API key dulu!")
            else:
                try:
                    ping = call_telkom_llm(
                        "ping", system_prompt="ping", temperature=0.0, max_tokens=16
                    )
                    st.success("✅ Telkom-LLM OK")
                    st.code(ping)
                except Exception as e:
                    st.error(pretty_error(e))
                    # Additional troubleshooting suggestions
                    if "401" in str(e) or "Unauthorized" in str(e):
                        st.markdown(
                            "**Solusi untuk 401:**\n"
                            "1. Periksa API key di .env atau sidebar\n"
                            "2. Coba auth scheme lain (x-api-key, apikey)\n"
                            "3. Pastikan endpoint URL benar\n"
                            "4. Hubungi admin untuk verifikasi akses"
                        )
    with colt2:
        if st.button("Test LMM"):
            try:
                pong = call_lmm("ping")
            except Exception as e:
                st.error(pretty_error(e))
            else:
                st.success("✅ LMM OK")
                st.json(pong)

st.title("🤖 Telkom ConsultBot — Consultative Selling Assistant (POC)")

tabs = st.tabs(
    [
        "💬 Chat",
        "🏷 Profil Perusahaan",
        "📄 Tender Analyzer",
        "🖼 Site Risk",
        "🎙 Voice Brief",
        "ℹ About",
    ]
)

# -------------
# Tab: Chat
# -------------
with tabs[0]:
    st.subheader("Chat Bebas (Consultative Selling)")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_msg = st.chat_input(
        "Ketik pesan (misal: 'Rekomendasi pendekatan untuk PT ABC sektor logistik')."
    )
    if user_msg:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)
        try:
            with st.chat_message("assistant"):
                with st.spinner("Memproses dengan Telkom-LLM..."):
                    answer = call_telkom_llm(user_msg, SYSTEM_PROMPT)
                    st.markdown(answer)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": answer}
                )
        except Exception as e:
            err = pretty_error(e)
            st.error(err)
            st.session_state.chat_history.append({"role": "assistant", "content": err})

# ------------------------
# Tab: Profil Perusahaan
# ------------------------
with tabs[1]:
    st.subheader("Profil Perusahaan & Strategi Pendekatan")
    company = st.text_input("Nama perusahaan (misal: PT Sinar Logistik)")
    industry = st.text_input("Industri (opsional, misal: Logistik)")
    products = st.multiselect(
        "Produk fokus",
        [
            "IndiBiz Internet",
            "SD-WAN",
            "MPLS/IPVPN",
            "WAN Optimization",
            "Cloud/Edge",
            "Security",
        ],
        default=["IndiBiz Internet", "SD-WAN"],
    )
    crm_snapshot = st.text_area(
        "Ringkasan CRM (opsional, JSON/teks singkat)", height=120
    )

    colA, colB = st.columns(2)
    with colA:
        do_profile = st.button("🔎 Profilkan")
    with colB:
        do_strategy = st.button("🧭 Rekomendasi Pendekatan")

    if do_profile or do_strategy:
        if not company:
            st.warning("Isi dulu nama perusahaan.")
        else:
            try:
                task = "profil" if do_profile else "strategi"
                with st.spinner(f"Meminta {task} ke Telkom-LLM..."):
                    user_prompt = (
                        f"Tugas: {'Profilkan' if do_profile else 'Rekomendasikan pendekatan untuk'} perusahaan berikut.\n"
                        f"Nama: {company}\n"
                        f"Industri: {industry or '-'}\n"
                        f"Produk target: {', '.join(products) if products else '-'}\n"
                        f"Data CRM ringkas: {crm_snapshot or '-'}\n"
                        f"Tujuan: peluang proyek 90 hari + next best action."
                    )
                    res = call_telkom_llm(user_prompt, SYSTEM_PROMPT, temperature=0.2)
                    st.markdown(res)
            except Exception as e:
                st.error(pretty_error(e))

# --------------------
# Tab: Tender Analyzer
# --------------------
with tabs[2]:
    st.subheader("Analisis Dokumen Tender (PDF → OCR → Compliance)")
    pdf_file = st.file_uploader("Unggah dokumen tender (PDF)", type=["pdf"])
    go = st.button("📑 Analisis Tender")

    if go:
        if not pdf_file:
            st.warning("Unggah dulu PDF tender.")
        else:
            try:
                pdf_bytes = pdf_file.read()
                pdf_b64 = b64encode_file(pdf_bytes, "application/pdf")
                with st.spinner("Menjalankan OCR..."):
                    ocr = call_ocr(pdf_b64)
                extracted_text = ocr.get("text", "")

                if not extracted_text:
                    st.error(
                        "OCR tidak menghasilkan teks. Pastikan PDF tidak terenkripsi atau coba ulang."
                    )
                else:
                    st.success(
                        f"OCR selesai — {len(extracted_text)} karakter diekstraksi."
                    )
                    with st.expander("Lihat cuplikan teks OCR"):
                        st.text(extracted_text[:5000])

                    analysis_prompt = (
                        "Analisis teks tender berikut. Buat ringkasan, tabel persyaratan (mandatory/optional), "
                        "timeline, kriteria evaluasi, dokumen wajib, serta rekomendasi go/no-go dan risiko utama.\n\n"
                        f"{extracted_text[:15000]}"
                    )
                    with st.spinner("Menyusun compliance checklist..."):
                        analysis = call_telkom_llm(
                            analysis_prompt,
                            system_prompt="Anda analis tender Telkom yang teliti, ringkas, dan patuh standar.",
                        )
                    st.markdown(analysis)

            except Exception as e:
                st.error(pretty_error(e))

# ---------------
# Tab: Site Risk
# ---------------
with tabs[3]:
    st.subheader("Asesmen Risiko Site (Foto → OD + LMM Advice)")
    img = st.file_uploader("Unggah foto lokasi (JPG/PNG)", type=["jpg", "jpeg", "png"])
    run_site = st.button("🛠 Analisis Site")

    if run_site:
        if not img:
            st.warning("Unggah dulu fotonya.")
        else:
            try:
                mime = (
                    "image/jpeg"
                    if img.type in ["image/jpg", "image/jpeg"]
                    else "image/png"
                )
                img_bytes = img.read()
                img_b64 = b64encode_file(img_bytes, mime)

                col1, col2 = st.columns(2)
                with col1:
                    st.image(
                        img_bytes, caption="Foto lokasi (input)", use_column_width=True
                    )

                with st.spinner("Object Detection..."):
                    od = call_object_detection(img_b64)

                with st.spinner("Analisis LMM..."):
                    lmm = call_lmm(
                        prompt="Analisis risiko instalasi dari foto berikut. Soroti bahaya & rekomendasi mitigasi dalam 3 poin ringkas.",
                        images_b64=[img_b64],
                    )

                with col2:
                    st.markdown("*Deteksi objek (ringkas):*")
                    st.json(od)
                    st.markdown("*Saran teknis (LMM):*")
                    st.json(lmm)

                # Ringkas jadi rekomendasi praktis
                detected = json.dumps(od)[:4000]
                lmm_text = json.dumps(lmm)[:4000]
                summary_prompt = (
                    "Ringkas hasil berikut menjadi rekomendasi teknis praktis untuk tim instalasi (maks 7 poin):\n"
                    f"Deteksi: {detected}\n"
                    f"Analisis LMM: {lmm_text}"
                )
                with st.spinner("Menyusun rekomendasi praktis..."):
                    summary = call_telkom_llm(
                        summary_prompt,
                        system_prompt="Anda engineer jaringan Telkom yang memberikan saran praktis dan aman.",
                    )
                st.markdown(summary)

            except Exception as e:
                st.error(pretty_error(e))

# ----------------
# Tab: Voice Brief
# ----------------
with tabs[4]:
    st.subheader("Voice → Briefing 30 detik (STT + LLM + TTS)")
    audio = st.file_uploader(
        "Unggah voice note (MP3/WAV/M4A)", type=["mp3", "wav", "m4a"]
    )
    run_voice = st.button("🎧 Proses Voice")

    if run_voice:
        if not audio:
            st.warning("Unggah dulu voice note.")
        else:
            try:
                ext = audio.name.lower().split(".")[-1]
                mime = (
                    "audio/mpeg"
                    if ext == "mp3"
                    else ("audio/wav" if ext == "wav" else "audio/mp4")
                )
                audio_bytes = audio.read()
                audio_b64 = b64encode_file(audio_bytes, mime)

                with st.spinner("Transkrip (STT)..."):
                    stt_res = call_stt(audio_b64, language="id")
                transcript = stt_res.get("text", "")

                if not transcript:
                    st.error("Gagal menghasilkan transkrip. Coba format audio lain.")
                else:
                    st.success("STT selesai.")
                    st.markdown("*Transkrip:*")
                    st.write(transcript)

                    with st.spinner("Ringkas jadi briefing 30 detik..."):
                        briefing = call_telkom_llm(
                            user_text=f"Ringkas jadi briefing AM 30 detik: poin inti, next step, CTA.\n\nTeks:\n{transcript}",
                            system_prompt="Anda konsultan penjualan Telkom. Jawab ringkas, praktis, dengan CTA jelas.",
                        )
                    st.markdown("*Briefing 30 detik (teks):*")
                    st.write(briefing)

                    with st.spinner("Text-to-Speech..."):
                        tts = call_tts(briefing, voice="id_female_1")
                    audio_out_b64 = tts.get("audio_base64")

                    if audio_out_b64:
                        # decode base64 (dengan / tanpa prefix data:)
                        b64data = (
                            audio_out_b64.split(",", 1)[1]
                            if "," in audio_out_b64
                            else audio_out_b64
                        )
                        try:
                            audio_bytes_out = base64.b64decode(b64data)
                            st.audio(audio_bytes_out, format="audio/mp3")
                            st.download_button(
                                "⬇ Unduh Audio Briefing",
                                data=audio_bytes_out,
                                file_name="briefing.mp3",
                            )
                        except Exception:
                            st.info(
                                "Audio TTS tersedia dalam base64 (tidak bisa diputar otomatis)."
                            )
                            st.code(audio_out_b64[:300] + "...")
                    else:
                        st.warning("TTS tidak mengembalikan audio.")

            except Exception as e:
                st.error(pretty_error(e))

# -------
# Tab: About
# -------
with tabs[5]:
    st.subheader("Tentang Aplikasi")
    st.markdown(
        """
*Telkom ConsultBot (POC)* membantu AM menjalankan consultative selling:
- Profil pelanggan & ekosistem
- Strategi pendekatan dan next best action
- Analisis tender (OCR → compliance checklist)
- Asesmen risiko site dari foto
- Voice note → briefing 30 detik (STT + TTS)

*Keamanan & Catatan*
- Jangan tempelkan data sensitif tanpa izin.
- Log bisa berisi prompt & hasil LLM untuk audit.
- Endpoint & skema auth dapat disesuaikan di sidebar.
"""
    )

st.markdown("<hr/>", unsafe_allow_html=True)
st.caption("© 2025 Telkom ConsultBot (POC) — All-in-One with selectable auth scheme.")
