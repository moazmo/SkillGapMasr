"""
Skill-Gap Masr - Streamlit Frontend

A clean, simple UI for analyzing skill gaps in the Egyptian tech market.
Built with Streamlit for rapid development and easy deployment.
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

import config
from ingest import run_ingestion
from rag_engine import SkillGapAnalyzer


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Skill-Gap Masr 🇪🇬",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CUSTOM STYLING
# =============================================================================
st.markdown(
    """
<style>
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: #a8d4ff;
        margin-top: 0.5rem;
        font-size: 1.1rem;
    }
    
    /* Report styling */
    .report-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border-left: 4px solid #2d5a87;
    }
    
    /* Sidebar styling */
    .sidebar-info {
        background: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #2d5a87 0%, #1e3a5f 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        border-radius: 8px;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #3d7ab7 0%, #2e4a6f 100%);
    }
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# HEADER
# =============================================================================
st.markdown(
    """
<div class="main-header">
    <h1>🎯 Skill-Gap Masr</h1>
    <p>Bridge the gap between your skills and the Egyptian tech market</p>
</div>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # Role Selection
    st.markdown("### 🎯 Target Role")
    role_options = [
        "Junior ML Engineer",
        "Junior AI Engineer",
        "Backend Developer",
        "Data Scientist",
        "Frontend Developer",
        "Full Stack Developer",
        "DevOps Engineer",
        "Mobile Developer",
    ]

    selected_role = st.selectbox(
        "What role are you targeting?",
        role_options,
        index=0,
        help="Select the role you're applying for in the Egyptian market",
    )

    # Custom role input
    custom_role = st.text_input(
        "Or enter a custom role:", placeholder="e.g., Computer Vision Engineer"
    )

    if custom_role:
        selected_role = custom_role

    st.markdown("---")

    # Ingestion Section
    st.markdown("### 📊 Data Management")

    st.markdown(
        """
    <div class="sidebar-info">
        <strong>📂 Data Directories:</strong><br>
        • Job Descriptions: <code>data/market_jobs/</code><br>
        • Student CVs: <code>data/student_cvs/</code>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 Rebuild Vector Store", help="Re-index all documents"):
        with st.spinner("Processing documents..."):
            try:
                run_ingestion()
                st.success("✅ Vector store rebuilt!")
                # Clear the cached analyzer to force reload
                if "analyzer" in st.session_state:
                    del st.session_state["analyzer"]
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.markdown("---")

    # Info Section
    st.markdown("### ℹ️ About")
    st.markdown("""
    **Skill-Gap Masr** helps Egyptian CS students:
    
    - 📋 Analyze job requirements from local companies
    - 🔍 Identify skill gaps in their CVs
    - 📚 Get actionable learning recommendations
    - 🎓 Prepare for the Egyptian tech market
    
    ---
    
    Built with ❤️ for Egyptian tech talent
    """)


# =============================================================================
# MAIN CONTENT
# =============================================================================

# Load sample CV as default
sample_cv_path = config.DATA_CVS_DIR / "my_cv.txt"
default_cv = ""
if sample_cv_path.exists():
    try:
        default_cv = sample_cv_path.read_text(encoding="utf-8")
    except Exception:
        pass

# CV Input Section
st.markdown("## 📄 Your CV / Resume")
st.markdown("Paste your CV content below or edit the sample:")

cv_text = st.text_area(
    "CV Content",
    value=default_cv,
    height=300,
    placeholder="Paste your CV here...",
    label_visibility="collapsed",
)

# Analyze Button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    analyze_clicked = st.button(
        "🔍 Analyze My Skill Gap", type="primary", use_container_width=True
    )

# =============================================================================
# ANALYSIS SECTION
# =============================================================================
if analyze_clicked:
    if not cv_text.strip():
        st.warning("⚠️ Please enter your CV content above.")
    else:
        # Check for API key (supports both .env and Streamlit Cloud secrets)
        import os
        from dotenv import load_dotenv

        load_dotenv()

        # Try Streamlit secrets first (for cloud deployment), then fall back to .env
        api_key = st.secrets.get("GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_api_key_here":
            st.error("""
            ❌ **Groq API Key not configured!**
            
            **For local development:**
            1. Get a FREE API key from [Groq Console](https://console.groq.com/keys)
            2. Add `GROQ_API_KEY=your_key` to your `.env` file
            
            **For Streamlit Cloud:**
            Add `GROQ_API_KEY` in your app's Secrets settings.
            """)
        else:
            st.markdown("---")
            st.markdown(f"## 📊 Gap Analysis Report")
            st.markdown(f"**Target Role:** {selected_role}")

            with st.spinner(
                "🔍 Analyzing your skills against Egyptian market requirements..."
            ):
                try:
                    # Initialize analyzer (cached in session state)
                    if "analyzer" not in st.session_state:
                        st.session_state["analyzer"] = SkillGapAnalyzer()

                    analyzer = st.session_state["analyzer"]

                    # Run analysis
                    report = analyzer.analyze_gap(cv_text, selected_role)

                    # Display report
                    st.markdown("---")
                    st.markdown(report)

                    # Download option
                    st.markdown("---")
                    st.download_button(
                        label="📥 Download Report",
                        data=report,
                        file_name=f"skill_gap_report_{selected_role.lower().replace(' ', '_')}.md",
                        mime="text/markdown",
                    )

                except FileNotFoundError as e:
                    st.error(f"""
                    ❌ **Vector store not found!**
                    
                    Please click "🔄 Rebuild Vector Store" in the sidebar first.
                    
                    Make sure you have job description files in `data/market_jobs/`
                    """)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🇪🇬 <strong>Skill-Gap Masr</strong> - Powered by Groq + Llama 3 & LangChain</p>
    <p style="font-size: 0.8rem;">
        Targeting: Instabug • Swvl • Vodafone IS • Valeo Egypt • and more
    </p>
</div>
""",
    unsafe_allow_html=True,
)
