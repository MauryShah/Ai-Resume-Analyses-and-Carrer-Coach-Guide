
import io

import streamlit as st
import pymupdf
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

st.set_page_config(page_title="Resume Scorer", layout="wide")


def parse_pdf(file_bytes):
    with pymupdf.open(stream=io.BytesIO(file_bytes), filetype="pdf") as doc:
        return "\n\n".join(page.get_text() for page in doc)


# Page header
st.markdown(
    """
    <div class="page-header">
        <h1>Resume Scorer</h1>
        <p>Evaluate your resume across six key categories and discover quick wins.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Evaluate your resume")
st.write("Upload your resume and optionally specify the job you're targeting.")

uploaded = st.file_uploader(
    "Upload your resume",
    type=["pdf"],
    help="Upload a PDF resume for AI-powered scoring.",
    key="scorer_resume_upload",
)

if uploaded is not None:
    if st.session_state.get("scorer_resume_name") != uploaded.name:
        st.session_state["scorer_resume_text"] = parse_pdf(uploaded.getvalue())
        st.session_state["scorer_resume_name"] = uploaded.name
        st.session_state.pop("scorer_result", None)

resume = st.session_state.get("scorer_resume_text", "")

if resume:
    st.success(f"Resume ready: {st.session_state['scorer_resume_name']}")

job_role = st.text_input(
    "Target job role (optional)",
    placeholder="e.g. Data Analyst",
)

if st.button("Score My Resume", type="primary", use_container_width=True):
    if not resume.strip():
        st.warning("Please upload your resume first.")
    else:
        prompt = PromptTemplate(
            input_variables=["resume", "job_role"],
            template="""
You are a resume scoring expert.
Score the resume across 6 categories out of 10.
Target job role: {job_role}

Resume:
{resume}

Reply in EXACTLY this format with no extra text:

CLARITY: X/10 - reason
FORMAT: X/10 - reason
SKILLS: X/10 - reason
EXPERIENCE: X/10 - reason
IMPACT: X/10 - reason
ATS: X/10 - reason

OVERALL: XX/100

TOP 3 QUICK WINS:
1. ...
2. ...
3. ...
""",
        )

        llm = ChatGroq(model="openai/gpt-oss-20b")
        chain = prompt | llm | StrOutputParser()

        try:
            with st.spinner("Scoring your resume..."):
                st.session_state["scorer_result"] = chain.invoke(
                    {
                        "resume": resume,
                        "job_role": job_role.strip() or "Not specified",
                    }
                )
        except Exception as exc:
            st.error(f"Unable to score the resume: {exc}")

result = st.session_state.get("scorer_result")

if result:
    categories = ["CLARITY", "FORMAT", "SKILLS", "EXPERIENCE", "IMPACT", "ATS"]
    scores, reasons = {}, {}
    overall = None
    quick_wins = []
    in_wins = False

    for line in result.splitlines():
        stripped = line.strip()

        for cat in categories:
            if stripped.startswith(cat + ":"):
                try:
                    score_part, separator, reason = stripped.partition("-")
                    scores[cat] = max(
                        0, min(10, int(score_part.split(":")[1].strip().split("/")[0]))
                    )
                    reasons[cat] = reason.strip() if separator else ""
                except (ValueError, IndexError):
                    pass

        if stripped.startswith("OVERALL:"):
            try:
                overall = max(
                    0, min(100, int(stripped.split(":")[1].strip().split("/")[0]))
                )
            except (ValueError, IndexError):
                pass

        if "TOP 3 QUICK WINS" in stripped:
            in_wins = True
            continue

        if in_wins and stripped:
            if stripped.startswith(("1.", "2.", "3.")):
                quick_wins.append(stripped)

    st.markdown("---")
    st.markdown("### Your results")

    if overall is not None:
        st.metric("Overall Resume Score", f"{overall}/100")
        st.progress(overall / 100)

    cols = st.columns(2)

    for index, cat in enumerate(categories):
        score = scores.get(cat, 0)

        with cols[index % 2]:
            with st.container(border=True):
                st.markdown(f"**{cat.title()}**")
                st.progress(score / 10)
                st.markdown(f"**{score}/10**")
                if reasons.get(cat):
                    st.caption(reasons[cat])

    st.markdown("### Your top 3 quick wins")

    if quick_wins:
        for win in quick_wins:
            st.markdown(f"- {win}")
    else:
        st.info("Quick wins were not found in the expected format.")

    st.download_button(
        "Download scoring report",
        data=result,
        file_name="resume_scoring_report.txt",
        mime="text/plain",
        use_container_width=True,
    )
