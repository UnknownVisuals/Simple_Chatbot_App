# AI Assistant with Role-Play & Knowledge Base

This project is an interactive chatbot application built with Python, Streamlit, and AI APIs (Google Gemini or Telkom AI). It demonstrates how to create a sophisticated AI assistant that can adopt different personalities (roles) and answer questions based on information from uploaded PDF and Excel documents.

This repository is the final output of the **"Machine Learning (Developing): How To Make Simple Chatbot"** training module.

## ✨ Features

| Feature                        | Description                                                                                                                      |
| :----------------------------- | :------------------------------------------------------------------------------------------------------------------------------- |
| 🎭 **Dynamic Role-Playing**    | Choose from multiple AI personas (e.g., General Assistant, Customer Service) to change the chatbot's tone, expertise, and style. |
| 📚 **Document Knowledge Base** | Upload PDF and Excel documents for the chatbot to use as a primary source of information (Retrieval-Augmented Generation).       |
| 🧠 **Conversation Memory**     | Remembers the context of the current conversation using Streamlit's session state.                                               |
| 🚀 **Interactive Web UI**      | A clean and user-friendly web interface built entirely in Python with Streamlit.                                                 |
| 🤖 **Dual AI Support**         | Choose between Google Gemini or Telkom AI models with identical functionality.                                                   |

## 🛠️ Technologies Used

| Category                   | Technology / Library                               |
| :------------------------- | :------------------------------------------------- |
| **Backend**                | Python 3.9+                                        |
| **AI Models**              | Google Gemini API (`gemini-2.5-flash`) / Telkom AI |
| **Web Framework**          | Streamlit                                          |
| **Environment & Packages** | uv                                                 |
| **Document Processing**    | PyPDF2 (PDF), pandas + openpyxl (Excel)            |
| **Table Formatting**       | tabulate                                           |
| **API Key Management**     | python-dotenv                                      |

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

### 5. Set Up Your API Key

For **Google Gemini** (main.py):

1. Get your Google Gemini API key from [Google AI Studio](https://aistudio.google.com/).
2. In the root of the project folder, create a new file named `.env`.
3. Open the `.env` file and add your API key in the following format:

   ```env
   GEMINI_API_KEY="AIzaSy...your...secret...key..."
   ```

For **Telkom AI** (main_telkom.py):

1. Get your Telkom AI API key from your Telkom AI provider.
2. Add the Telkom API key to your `.env` file:

   ```env
   TELKOM_API_KEY="your...telkom...api...key..."
   ```

You can have both API keys in the same `.env` file to use either version.

## ▶️ Usage

Once the setup is complete, you can run either version of the application:

**For Google Gemini version:**

```bash
streamlit run main.py
```

**For Telkom AI version:**

```bash
streamlit run main_telkom.py
```

Your web browser will automatically open to the application's interface.

Both versions offer identical functionality - the only difference is the AI model used for generating responses.

## ⚙️ How It Works

### File Structure

- **`main.py`:** The Google Gemini-based chatbot version. Contains all application logic for the Google Gemini API integration.
- **`main_telkom.py`:** The Telkom AI-based chatbot version. Contains identical functionality but uses the Telkom AI API instead of Google Gemini.

Both files provide the exact same features and user experience, differing only in the AI model used.

### Core Components

- **Streamlit:** Renders the web interface. All UI elements like the sidebar, chat messages, and file uploader are created using Streamlit functions (`st.sidebar`, `st.chat_message`, etc.).
- **Session State (`st.session_state`):** This crucial Streamlit feature stores the conversation history and knowledge base content, so data persists between user interactions.
- **Role-Playing:** A Python dictionary (`ROLES`) stores different system prompts. When a user selects a role, the corresponding system prompt guides the AI model's behavior.
- **Knowledge Base (RAG):** When PDF or Excel files are uploaded:
  - **PDFs:** `PyPDF2` library extracts text content
  - **Excel files:** `pandas` and `openpyxl` read data, converted to markdown tables using `tabulate`
  - All content is appended to the system prompt, instructing the AI to use this information as a primary source when answering questions.

## 🙏 Acknowledgments

- This project was developed as part of a training module by **Danantara Indonesia** and **Telkom Indonesia**.
