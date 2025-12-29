"""
Skill-Gap Masr - RAG Engine Module

This is the "brain" of the system. It handles:
1. Retrieving relevant job descriptions from ChromaDB
2. Comparing them against a student's CV
3. Using Groq LLM (Llama 3) to generate a gap analysis report

Why Groq? It's completely free with generous rate limits and
uses fast Llama 3 models.
"""

import os
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

import config


# =============================================================================
# SYSTEM PROMPT - The "Secret Sauce"
# =============================================================================
# This prompt is tuned for the Egyptian tech job market context.
# It instructs the LLM to be encouraging but direct, and to recognize
# local market-specific requirements.

SYSTEM_PROMPT = """You are "Skill-Gap Masr", an expert career advisor specializing in the Egyptian tech job market.

Your role is to analyze the gap between a student's current skills (from their CV) and the requirements of tech jobs in Egypt (from job descriptions).

## Your Analysis Framework:

### 1. HARD SKILLS GAP
Identify missing technical skills. Be specific:
- ❌ Missing: "Job requires PyTorch, CV shows only TensorFlow"
- ✅ Match: "Both require Python - this is covered"

### 2. SOFT/REGIONAL REQUIREMENTS
Flag any Egyptian market-specific requirements:
- Military Status (for male candidates)
- Location requirements (Cairo, Giza, New Cairo, Maadi, etc.)
- Language requirements (Arabic/English proficiency)
- University preferences mentioned (Cairo University, Helwan, Ain Shams, etc.)

### 3. EXPERIENCE GAP
Note experience level mismatches:
- Fresh Graduate vs. 1-2 years required
- Internship experience vs. full-time required

### 4. ACTIONABLE RECOMMENDATIONS
For each gap, suggest SPECIFIC actions:
- Free resources (YouTube channels, Coursera free courses)
- Weekend projects to fill the gap
- Open source contributions relevant to Egyptian companies
- Local tech communities (Cairo AI, Egyptian Geeks, etc.)

## Egyptian Market Context You Understand:
- Major tech companies: Instabug, Swvl, Vodafone IS, Valeo Egypt, Orange Labs, IBM Egypt
- Startup hubs: Smart Village, GrEEK Campus, The District
- Common requirements: Git proficiency, English communication, Competitive Programming background
- Fresh grad reality: Many roles accept "0-1 years" as fresh graduate friendly

## Output Format:
Use clear sections with emojis. Be encouraging but honest. If the student is close to qualified, emphasize that! If there are major gaps, prioritize the top 3 most important ones to fix first.

Remember: You're mentoring an Egyptian CS student. Be warm, practical, and specific to their local context.
"""


class SkillGapAnalyzer:
    """
    Main class for skill gap analysis between CVs and job requirements.

    This class handles:
    1. Loading the existing ChromaDB vector store
    2. Retrieving relevant job descriptions based on role query
    3. Running the gap analysis chain with Gemini LLM
    """

    def __init__(self):
        """
        Initialize the analyzer with embeddings, vector store, and LLM.

        Raises:
            ValueError: If GOOGLE_API_KEY environment variable is not set
        """
        # Try Streamlit secrets first (for cloud deployment), then fall back to .env
        try:
            import streamlit as st
            groq_api_key = st.secrets.get("GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY")
        except Exception:
            groq_api_key = os.getenv("GROQ_API_KEY")
            
        if not groq_api_key or groq_api_key == "your_api_key_here":
            raise ValueError(
                "GROQ_API_KEY not set!\n"
                "1. Get a FREE API key from: https://console.groq.com/keys\n"
                "2. Add GROQ_API_KEY=your_key to your .env file"
            )

        # Initialize embeddings (same model as ingestion)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # Load existing vector store
        if not config.CHROMA_PERSIST_DIR.exists():
            raise FileNotFoundError(
                f"Vector store not found at {config.CHROMA_PERSIST_DIR}\n"
                "Please run: python ingest.py"
            )

        self.vector_store = Chroma(
            persist_directory=str(config.CHROMA_PERSIST_DIR),
            embedding_function=self.embeddings,
            collection_name="skill_gap_masr",
        )

        # Initialize Groq LLM (Llama 3)
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=config.LLM_TEMPERATURE,
            api_key=groq_api_key,
        )

        # Create the analysis prompt template
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    """## Target Role:
{role}

## Relevant Job Descriptions from Egyptian Market:
{job_context}

## Student's CV:
{cv_text}

---

Please provide a comprehensive Skill Gap Analysis Report for this student targeting the role above.
Focus on practical, actionable insights specific to the Egyptian tech market.""",
                ),
            ]
        )

        # Create the chain
        self.chain = self.prompt | self.llm | StrOutputParser()

    def get_relevant_jobs(self, role: str, k: int = None) -> List[Document]:
        """
        Retrieve relevant job descriptions for a given role.

        Args:
            role: The target role (e.g., "Junior ML Engineer")
            k: Number of documents to retrieve (default from config)

        Returns:
            List of relevant Document objects with job description content
        """
        if k is None:
            k = config.RETRIEVAL_K

        # Search for relevant job descriptions only
        results = self.vector_store.similarity_search(
            query=role, k=k, filter={"doc_type": config.DOC_TYPE_JOB}
        )

        return results

    def analyze_gap(self, cv_text: str, role: str) -> str:
        """
        Generate a skill gap analysis report.

        This is the main analysis function that:
        1. Retrieves relevant job descriptions
        2. Combines them with the CV
        3. Sends to Gemini for analysis
        4. Returns a formatted report

        Args:
            cv_text: The student's CV content as text
            role: The target role they're interested in

        Returns:
            Formatted skill gap analysis report as markdown string
        """
        # Get relevant job descriptions
        relevant_jobs = self.get_relevant_jobs(role)

        if not relevant_jobs:
            return (
                "⚠️ **No relevant job descriptions found!**\n\n"
                "Please make sure you've run the ingestion pipeline:\n"
                "```bash\npython ingest.py\n```\n\n"
                "And that you have job description files in `data/market_jobs/`"
            )

        # Format job context
        job_context = "\n\n---\n\n".join(
            [
                f"**Source:** {doc.metadata.get('source_name', 'Unknown')}\n\n{doc.page_content}"
                for doc in relevant_jobs
            ]
        )

        # Run the chain
        try:
            report = self.chain.invoke(
                {"role": role, "job_context": job_context, "cv_text": cv_text}
            )
            return report

        except Exception as e:
            return (
                f"❌ **Error generating analysis:** {str(e)}\n\n"
                "This might be a temporary API issue. Please try again."
            )

    def get_all_job_titles(self) -> List[str]:
        """
        Get a list of unique job titles from the vector store.

        Useful for populating dropdown menus in the UI.

        Returns:
            List of job title strings found in the database
        """
        # Get all job documents
        try:
            results = self.vector_store.get(
                where={"doc_type": config.DOC_TYPE_JOB},
                include=["documents", "metadatas"],
            )

            titles = set()
            for doc in results.get("documents", []):
                # Try to extract title from first line
                if doc:
                    first_line = doc.split("\n")[0]
                    if "JOB TITLE:" in first_line.upper():
                        title = first_line.split(":", 1)[-1].strip()
                        titles.add(title)

            return sorted(list(titles)) if titles else []

        except Exception:
            return []


if __name__ == "__main__":
    # Quick test of the analyzer
    print("Testing Skill Gap Analyzer...")

    try:
        analyzer = SkillGapAnalyzer()
        print("✅ Analyzer initialized successfully!")

        # Test retrieval
        jobs = analyzer.get_relevant_jobs("Junior ML Engineer")
        print(f"✅ Retrieved {len(jobs)} relevant job descriptions")

        # Test analysis with sample CV
        sample_cv = """
        NAME: Test Student
        SKILLS: Python, Machine Learning, TensorFlow
        EDUCATION: B.Sc. Computer Science, Cairo University
        """

        print("\n📝 Running gap analysis (this may take a moment)...")
        report = analyzer.analyze_gap(sample_cv, "Junior ML Engineer")
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
