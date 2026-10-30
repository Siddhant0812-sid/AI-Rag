# 🎓 StudyBuddy AI — Collaborative Study Hub & Shared Document Vault

> [!TIP]
> 🌐 **Live Public Access URL**: **[https://veterinary-mba-former-bone.trycloudflare.com](https://veterinary-mba-former-bone.trycloudflare.com)**  
> Accessible globally from any smartphone, tablet, or laptop browser with zero setup or configuration.

An intelligent, 100% private **AI Study Partner** paired with a central **Shared Document Vault** designed for students, study groups, roommates, and classrooms.

Upload textbooks, lecture slides, past exams, and revision notes to a shared library that **anyone connected to your local network (Wi-Fi) can view, search, and directly download**. Study together with an AI that breaks down complex topics, creates practice quizzes, generates study flashcards, and synthesizes revision cram sheets grounded in your actual course materials.

---

## ✨ Highlights & Features

### 📚 1. Shared Study Library & Document Vault
- **Accessible to Everyone**: Anyone on your local network (Wi-Fi or LAN) can access `http://<your-ip>:8000` to browse, read, and download all shared study documents.
- **Direct File Downloads**: Every uploaded PDF, Markdown, TXT, CSV, or JSON document has a 1-click **Download** button to save the original file to phones, tablets, or laptops.
- **In-App Document Reader**: Built-in full-text document reader with keyword search, word count, and reading view so classmates don't need external PDF readers or editors.
- **Subject / Course Categorization**: Tag and filter study materials by subject:
  - 💻 Computer Science
  - 🧬 Biology & Life Sciences
  - ⚛️ Physics & Engineering
  - 📐 Mathematics & Statistics
  - 🧪 Chemistry
  - 📜 History & Humanities
  - 🌐 General Studies

---

### 🧠 2. StudyBuddy AI Pedagogical Engine
- **💬 Discuss & Learn**: Friendly, patient, structured study partner that answers academic questions clearly with step-by-step reasoning.
- **💡 Concept Explainer ("ELI5")**: Breaks down difficult concepts using intuitive real-world analogies, step-by-step logic, and summary takeaways.
- **📝 Practice Quiz Generator**: Automatically creates 3–4 question practice tests with multiple-choice options, correct answers, and thorough explanations.
- **📇 Flashcard Deck Maker**: Formats high-yield Q&A study cards complete with front prompts, back answers, and test-taking tips.
- **📑 Smart Cram Sheets & Summaries**: Extracts core definitions, key principles, formulas, and common exam traps/gotchas.
- **🎯 Focus Study Scope**: Study across *All Shared Library Notes* or target a *Specific Document* (e.g. "Quiz me specifically on my Bio notes").

---

### ⏱️ 3. Collaborative & Productivity Tools
- **🍅 Integrated Pomodoro Focus Timer**: 25-minute study intervals and 5-minute break alerts built directly into the header.
- **📡 One-Click Study Group Link Sharing**: Displays your local Wi-Fi IP address with a 1-click "Copy Link" modal to easily invite classmates.
- **🌐 Hybrid AI Architecture (Local + Cloud)**:
  - **🏠 100% Offline with Ollama**: Works out-of-the-box with local models like `qwen2.5:3b`, `qwen3:8b`, `llama3.2`, `mistral`.
  - **🌟 Google Gemini**: Stream directly from `gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`, or `gemini-3.8-flash`.
  - **⚡ OpenAI (ChatGPT)**: Use `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, or custom OpenAI-compatible endpoints (Groq, DeepSeek, OpenRouter).
  - **🧠 Anthropic Claude**: High-reasoning academic support with `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022`, or `claude-3-opus`.
- **Glassmorphic Academic UI**: Modern dark theme with high-contrast typography, LaTeX math rendering, syntax-highlighted code blocks, and responsive mobile-friendly layouts.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Ollama** installed and running (for offline local models):
  ```bash
  # Check if Ollama is running
  ollama list

  # Pull your preferred model (e.g. Qwen 2.5 3B or LLaMA 3.2)
  ollama pull qwen2.5:3b
  ```

### 2. Configure Cloud API Keys (Optional)
If you want to use cloud models (Gemini, ChatGPT, or Claude), simply drop your keys into the [.env](file:///c:/Users/Admin/Documents/Projects/local-rag-chatbot/.env) file:
```env
GEMINI_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
```
*(You can also enter or update keys anytime via the in-app **Settings** modal!)*

### 3. Launch the Application
Run the launcher from the project directory:

```bash
python run.py
```

The server binds to `0.0.0.0:8000`:
- **On your computer**: `http://localhost:8000`
- **For friends/classmates on your Wi-Fi**: `http://<your-local-ip>:8000`

---

## 🏗️ Architecture

```
local-rag-chatbot/
├── backend/
│   ├── app.py            # FastAPI endpoints (chat streaming, document downloads, preview, network info)
│   ├── rag_engine.py     # StudyEngine (text extractors, chunker, hybrid TF-IDF + BM25, study modes)
│   ├── ollama_client.py  # Async Ollama client for model streaming & health detection
│   ├── storage.py        # Shared document metadata, subject tagging & physical file storage
│   └── sample_docs.py    # Pre-packaged CS, Biology, and Physics exam guides
├── frontend/
│   ├── index.html        # Modern HTML5 workspace (Pomodoro widget, vault sidebar, reader modal)
│   ├── css/
│   │   └── style.css     # Dark glassmorphism academic design system
│   └── js/
│       └── app.js        # Event-driven streaming chat, document reader, timer, and vault manager
├── data/
│   ├── documents/        # Stored original study files (PDFs, Markdown, etc.) accessible for download
│   ├── metadata.json     # Document catalog with subject tags and statistics
│   └── chunks.json       # Parsed study segments for AI grounding
├── run.py                # Single-command runner with local IP detection & browser launcher
└── requirements.txt      # Lightweight dependencies (FastAPI, uvicorn, pypdf, scikit-learn)
```

---

## 📖 How to Share With Friends & Study Groups

StudyBuddy provides three flexible ways to share your vault and AI partner:

### Option 1: 🌐 Worldwide Public Internet Access (Public IP)
1. In the top bar, click the **Public IP** pill or open the Share modal.
2. Your public WAN address is automatically detected (e.g. `http://59.153.120.87:8000`).
3. **Router Port Forwarding**:
   - Open your router admin panel (`http://192.168.1.1` or `http://192.168.0.1`).
   - Navigate to **Port Forwarding / Virtual Server**.
   - Forward **Port 8000 (TCP)** to your host PC's local IP (e.g. `192.168.1.8`).
4. Anyone on the internet can now access `http://<your-public-ip>:8000` from anywhere in the world!

---

### Option 2: ⚡ Instant Public Tunnel (Zero Router Setup / Cloudflare)
Your application is accessible right now over Cloudflare's secure worldwide network:

- **Active Public URL**: **[https://veterinary-mba-former-bone.trycloudflare.com](https://veterinary-mba-former-bone.trycloudflare.com)**
- **1-Click Launch**: Double-click `run_public.bat` in the project root to start the public tunnel at any time.
- **Manual Command**:
  ```powershell
  .\cloudflared.exe tunnel --url http://localhost:8000
  ```
- **Alternative (Pinggy — Built into Windows SSH)**:
  ```powershell
  ssh -p 443 -R0:localhost:8000 a.pinggy.io
  ```

---

### Option 3: 📶 Local Wi-Fi (Same Network)
1. Connect your laptop and your friend's phone, tablet, or laptop to the **same Wi-Fi network**.
2. Run `python run.py`.
3. Open `http://<your-local-ip>:8000` (e.g. `http://192.168.1.8:8000`).
4. Zero configuration required—devices on the same Wi-Fi connect instantly!
