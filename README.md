# AI Assistant with Role-Play & Knowledge Base

This project is an interactive chatbot application built with Python, Streamlit, and the Google Gemini API. It demonstrates how to create a sophisticated AI assistant that can adopt different personalities (roles) and answer questions based on information from uploaded PDF documents.

This repository is the final output of the **"Machine Learning (Developing): How To Make Simple Chatbot"** training module.

## ✨ Features

| Feature                     | Description                                                                                                                      |
| :-------------------------- | :------------------------------------------------------------------------------------------------------------------------------- |
| 🎭 **Dynamic Role-Playing** | Choose from multiple AI personas (e.g., General Assistant, Customer Service) to change the chatbot's tone, expertise, and style. |
| 📚 **PDF Knowledge Base**   | Upload PDF documents for the chatbot to use as a primary source of information (Retrieval-Augmented Generation).                 |
| 🧠 **Conversation Memory**  | Remembers the context of the current conversation using Streamlit's session state.                                               |
| 🚀 **Interactive Web UI**   | A clean and user-friendly web interface built entirely in Python with Streamlit.                                                 |

## 🛠️ Technologies Used

| Category                   | Technology / Library                   |
| :------------------------- | :------------------------------------- |
| **Backend**                | Python 3.9+                            |
| **AI Model**               | Google Gemini API (`gemini-1.5-flash`) |
| **Web Framework**          | Streamlit                              |
| **Environment & Packages** | uv                                     |
| **PDF Processing**         | PyPDF2                                 |
| **API Key Management**     | python-dotenv                          |

## 🚀 Getting Started

Follow these steps to set up and run the project on your local machine.

### 1\. Prerequisites

Ensure you have **Python 3.9** or newer installed on your system. You can download it from [python.org](https://www.python.org/).

### 2\. Clone the Repository

Open your terminal and clone this repository:

```bash
git clone https://github.com/your-username/your-repository-name.git
cd your-repository-name
```

### 3\. Set Up the Virtual Environment

This project uses `uv` for fast and efficient environment management.

First, install `uv` if you haven't already:

```bash
pip install uv
```

Next, create and activate a virtual environment within the project folder:

```bash
# Create the virtual environment
uv venv

# Activate the environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 4\. Install Dependencies

With the virtual environment activated, install all project dependencies defined in `pyproject.toml` using a single command:

```bash
uv sync
```

This command reads the `pyproject.toml` and `uv.lock` files to create an environment that exactly matches the project's specifications.

### 5\. Set Up Your API Key

1.  Get your Google Gemini API key from [Google AI Studio](https://aistudio.google.com/).

2.  In the root of the project folder, create a new file named `.env`.

3.  Open the `.env` file and add your API key in the following format:

    ```
    GEMINI_API_KEY="AIzaSy...your...secret...key..."
    ```

## ▶️ Usage

Once the setup is complete, run the Streamlit application from your terminal:

```bash
streamlit run main.py
```

_(Note: Use `main.py` or `app.py` depending on your main script's filename)._

Your web browser will automatically open to the application's interface.

## ⚙️ How It Works

- **`main.py`:** The original main file for the Gemini-based chatbot. Contains all application logic for the Google Gemini API version.
- **`main_telkom.py`:** An alternative main file that uses the Telkom AI API instead of Google Gemini. This version is tailored for Telkom AI integration and includes:
  - Support for the Telkom AI API via the `openai` compatible client and `TELKOM_API_KEY` in your `.env` file.
  - The same Streamlit-based UI, role selection, and PDF knowledge base features as the Gemini version.
  - All role-play, knowledge base, and conversation memory features, but powered by Telkom AI.
  - Clear error handling and connection status for the Telkom API in the sidebar.
- **Streamlit:** Renders the web interface. All UI elements like the sidebar, chat messages, and file uploader are created using Streamlit functions (`st.sidebar`, `st.chat_message`, etc.).
- **Session State (`st.session_state`):** This crucial Streamlit feature is used to store the conversation history and the knowledge base text, so the data persists between user interactions.
- **Role-Playing:** A Python dictionary (`ROLES`) stores different system prompts. When a user selects a role, the corresponding system prompt is fed to the AI model to guide its behavior.
- **Knowledge Base (RAG):** When a PDF is uploaded, the `PyPDF2` library extracts its text. This text is appended to the system prompt, instructing the AI to use this information as a primary source when answering questions.

## 🙏 Acknowledgments

- This project was developed as part of a training module by **Danantara Indonesia** and **Telkom Indonesia**.
