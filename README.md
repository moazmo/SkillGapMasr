# 🇪🇬 Skill-Gap Masr (سد فجوة المهارات)

**Bridge the gap between your skills and the Egyptian tech job market.**

Skill-Gap Masr is a **RAG (Retrieval-Augmented Generation)** powered career advisor designed specifically for Egyptian Computer Science students and fresh graduates. It analyzes your CV against real job descriptions from top local tech companies (Instabug, Swvl, Vodafone IS, etc.) to identify skill gaps and provide actionable, localized learning recommendations.

![Streamlit UI](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white) ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=LangChain&logoColor=white) ![Groq](https://img.shields.io/badge/Groq-Llama_3-orange?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white)

---

## 🚀 Features

*   **🇪🇬 Egyptian Market Context:** Tuned to understand local nuances like "Military Status," university preferences (Cairo Univ, Helwan, etc.), and local tech hubs.
*   **📄 PDF & Text Support:** Ingests job descriptions and CVs in common formats.
*   **🧠 RAG Architecture:** Uses Retrieval-Augmented Generation to ground advice in actual market data, preventing generic hallucinations.
*   **💸 Zero-Cost Stack:** Built entirely on free/open-source tiers:
    *   **LLM:** Groq API (Llama 3.3 70B) - *Free & Fast*
    *   **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`) - *Local Component*
    *   **Vector DB:** ChromaDB - *Local Persistence*
*   **🔌 Extensible:** Easy to add new job descriptions or switch LLM providers.

## 🛠️ Architecture

1.  **Ingestion (`ingest.py`):** Loads job descriptions, chunks them, creates embeddings using HuggingFace, and stores them in ChromaDB.
2.  **RAG Engine (`rag_engine.py`):** Retrieves relevant jobs based on the target role and uses Llama 3 (via Groq) to analyze the gap.
3.  **Frontend (`app.py`):** A clean Streamlit interface for user interaction.

## 📦 Installation

### Prerequisites
*   Python 3.11+
*   Git

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/SkillGapMasr.git
cd SkillGapMasr
```

### 2. Create a Virtual Environment
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
1.  Copy the template:
    ```bash
    cp .env.template .env
    ```
2.  Get a **FREE** API Key from [Groq Console](https://console.groq.com/keys).
3.  Edit `.env` and paste your key:
    ```
    GROQ_API_KEY=gsk_your_key_here...
    ```

## 🏃 Usage

### 1. Ingest Data
First, you need to build the "Knowledge Base" of Egyptian job descriptions. We've included some samples in `data/market_jobs`.

```bash
python ingest.py
```
*Output: ✅ Ingestion Complete. Vector Store saved to `chroma_db/`*

### 2. Run the App
```bash
streamlit run app.py
```
The application will open in your browser at `http://localhost:8501`.

## 📂 Project Structure

```
SkillGapMasr/
├── app.py              # Streamlit Frontend
├── config.py           # Configuration settings
├── ingest.py           # Data Ingestion Pipeline
├── rag_engine.py       # Core RAG Logic
├── requirements.txt    # Dependencies
├── .env.template       # Environment variables template
├── data/
│   ├── market_jobs/    # Add .txt/.pdf Job Descriptions here
│   └── student_cvs/    # Add your CV here (or paste in UI)
└── chroma_db/          # Local Vector Database (Generated)
```

## 🤝 Contributing

Contributions are welcome! If you want to add more Egyptian job descriptions:
1.  Fork the repo.
2.  Add `.txt` files to `data/market_jobs/`.
3.  Submit a Pull Request.

## 📄 License

MIT License - free for all Egyptian students and developers.
