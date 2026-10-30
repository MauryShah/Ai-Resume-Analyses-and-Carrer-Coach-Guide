
import io
import re
from xml.sax.saxutils import escape

import streamlit as st
import pymupdf
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from pathlib import Path

css_path = Path(__file__).parent.parent / "assets" / "style.css"

load_dotenv()

st.set_page_config(page_title="Cover Letter Generator", layout="wide")


def parse_pdf(file_bytes):
    with pymupdf.open(stream=io.BytesIO(file_bytes), filetype="pdf") as doc:
        return "\n\n".join(page.get_text() for page in doc)


def create_cover_letter_pdf(text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.8 * inch,
        leftMargin=0.8 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="LetterBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=16,
            textColor=colors.HexColor("#172033"),
            spaceAfter=12,
        )
    )

    story = []
    for paragraph in text.split("\n"):
        if paragraph.strip():
            story.append(Paragraph(escape(paragraph.strip()), styles["LetterBody"]))
            story.append(Spacer(1, 3))
        else:
            story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


st.markdown(
    """
    <div class="page-header">
        <h1>Cover Letter Generator</h1>
        <p>Create a tailored, professional cover letter for your next application.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Application details")

uploaded = st.file_uploader(
    "Upload your resume",
    type=["pdf"],
    key="cover_resume_upload",
)

if uploaded is not None:
    if st.session_state.get("cover_resume_name") != uploaded.name:
        st.session_state["cover_resume_text"] = parse_pdf(uploaded.getvalue())
        st.session_state["cover_resume_name"] = uploaded.name
        st.session_state.pop("cover_letter_result", None)

resume = st.session_state.get("cover_resume_text", "")

if resume:
    st.success(f"Resume ready: {st.session_state['cover_resume_name']}")

col1, col2 = st.columns(2)

with col1:
    job_title = st.text_input("Job title", placeholder="e.g. Data Scientist")

with col2:
    company = st.text_input("Company name", placeholder="e.g. Google")

job_description = st.text_area(
    "Job description",
    placeholder="Paste the job description here...",
    height=180,
)

if st.button("Generate Cover Letter", type="primary", use_container_width=True):
    if not resume.strip():
        st.warning("Please upload your resume first.")
    elif not job_title.strip():
        st.warning("Please enter the job title.")
    elif not company.strip():
        st.warning("Please enter the company name.")
    elif not job_description.strip():
        st.warning("Please enter the job description.")
    else:
        prompt = PromptTemplate(
            input_variables=["resume", "job_title", "company", "job_description"],
            template="""
You are a professional cover letter writer.
Write a cover letter using the resume below.

Resume:
{resume}

Job Title: {job_title}
Company: {company}
Job Description: {job_description}

The cover letter must have:
1. A strong opening showing enthusiasm for the role
2. A middle paragraph connecting resume skills to the job
3. A closing paragraph with a call to action

Keep the tone confident and human. Do not use placeholders like [Your Name] or [Date].
Write it as a complete ready-to-send letter.
""",
        )

        llm = ChatGroq(model="openai/gpt-oss-20b")
        chain = prompt | llm | StrOutputParser()

        try:
            with st.spinner("Writing your cover letter..."):
                st.session_state["cover_letter_result"] = chain.invoke(
                    {
                        "resume": resume,
                        "job_title": job_title.strip(),
                        "company": company.strip(),
                        "job_description": job_description.strip(),
                    }
                )
                st.session_state["cover_letter_company"] = company.strip()
        except Exception as exc:
            st.error(f"Unable to generate your cover letter: {exc}")

result = st.session_state.get("cover_letter_result")

if result:
    st.markdown("---")
    st.markdown("### Your generated cover letter")

    with st.container(border=True):
        st.markdown(result)

    safe_company = re.sub(
        r"[^A-Za-z0-9_-]+", "_",
        st.session_state.get("cover_letter_company", "company")
    ).strip("_") or "company"

    st.download_button(
        "Download cover letter as PDF",
        data=create_cover_letter_pdf(result),
        file_name=f"cover_letter_{safe_company}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )
