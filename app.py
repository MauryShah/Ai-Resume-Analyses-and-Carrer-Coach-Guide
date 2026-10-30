
import streamlit as st
from pathlib import Path

# --------------------------------------------------
# 1. PAGE CONFIGURATION
# This must be the first Streamlit command.
# --------------------------------------------------
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# 2. SESSION STATE
# Keeps resume information available across reruns
# and between Streamlit pages.
# --------------------------------------------------
if "resume_text" not in st.session_state:
    st.session_state["resume_text"] = None

if "resume_name" not in st.session_state:
    st.session_state["resume_name"] = None

# --------------------------------------------------
# 3. LOAD SHARED CSS
# Using the location of this file ensures the CSS
# path works even if Streamlit starts elsewhere.
# --------------------------------------------------
css_path = Path(__file__).parent / "assets" / "style.css"

if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as css_file:
        st.markdown(
            f"<style>{css_file.read()}</style>",
            unsafe_allow_html=True
        )
else:
    st.warning(
        "CSS file not found. Please check that "
        "assets/style.css exists in your project."
    )

# --------------------------------------------------
# 4. HOMEPAGE HEADER
# --------------------------------------------------
st.markdown(
    """
    <div class="page-header">
        <h1>AI Resume Analyzer</h1>
        <p>
            Your personal AI-powered career assistant.
            Analyze your resume, improve your applications,
            and plan your next career move.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# 5. WELCOME SECTION
# --------------------------------------------------
st.markdown("## Welcome to your career dashboard")
st.markdown(
    "Choose a tool from the sidebar to get started."
)

st.write("")

# --------------------------------------------------
# 6. FEATURE CARDS
# --------------------------------------------------
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(
        """
        <div class="app-card">
            <h3>📄 Resume Checker</h3>
            <p>
                Get an AI-powered resume analysis with an
                overall score, strengths, weaknesses,
                missing skills, and improvement suggestions.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="app-card">
            <h3>✉️ Cover Letter Generator</h3>
            <p>
                Generate a personalized cover letter
                tailored to your target job and professional
                background.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class="app-card">
            <h3>📊 Resume Scorer</h3>
            <p>
                Evaluate your resume across multiple
                categories and discover practical ways
                to improve your score.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="app-card">
            <h3>🤖 AI Career Coach</h3>
            <p>
                Get personalized career guidance,
                identify skill gaps, and explore your
                next professional steps.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# --------------------------------------------------
# 7. FOOTER
# --------------------------------------------------
st.write("")

st.markdown(
    """
    <div style="
        text-align: center;
        color: #64748b;
        font-size: 0.85rem;
        padding: 1.5rem 0 0.5rem 0;
        border-top: 1px solid #e2e8f0;
        margin-top: 1rem;
    ">
        Built with Streamlit and Groq AI
        <br>
        Your smarter journey to career growth starts here.
    </div>
    """,
    unsafe_allow_html=True
)
