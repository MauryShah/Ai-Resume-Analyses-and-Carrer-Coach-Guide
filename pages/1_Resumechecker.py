
import io
import os
import re
import streamlit as st
import pymupdf

from pathlib import Path
from dotenv import load_dotenv
from xml.sax.saxutils import escape

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


# ============================================================
# 1. PATHS AND ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# ============================================================
# 2. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Resume Checker | AI Career Coach",
    page_icon="📄",
    layout="wide",
)


# ============================================================
# 3. DARK THEME AND CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b1120;
        color: #e5e7eb;
    }

    [data-testid="stHeader"] {
        background-color: #0b1120;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #263449;
    }

    [data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    h1, h2, h3, h4 {
        color: #f8fafc !important;
    }

    p, label, .stMarkdown, li {
        color: #d1d5db;
    }

    [data-testid="stFileUploader"] {
        background-color: #111827;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
    }

    [data-testid="stFileUploader"] section {
        background-color: #111827;
    }

    [data-testid="stFileUploader"] button {
        background-color: #dc2626;
        color: #ffffff;
        border: none;
        border-radius: 8px;
    }

    [data-testid="stFileUploader"] button:hover {
        background-color: #b91c1c;
        color: #ffffff;
    }

    .stButton > button {
        background-color: #dc2626;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 1.2rem;
        font-weight: 600;
        width: 100%;
    }

    .stButton > button:hover {
        background-color: #b91c1c;
        color: white;
        border: none;
    }

    .stDownloadButton > button {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
    }

    .stDownloadButton > button:hover {
        background-color: #1d4ed8;
        color: white;
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    .report-container {
        background-color: #111827;
        border: 1px solid #263449;
        border-radius: 12px;
        padding: 22px;
        margin-top: 12px;
    }

    [data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #263449;
        padding: 16px;
        border-radius: 10px;
    }

    [data-testid="stMetricValue"] {
        color: #60a5fa;
    }

    hr {
        border-color: #263449;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 4. SESSION STATE
# ============================================================

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "resume_name" not in st.session_state:
    st.session_state.resume_name = ""

if "resume_report" not in st.session_state:
    st.session_state.resume_report = ""


# ============================================================
# 5. PDF RESUME TEXT EXTRACTION
# ============================================================

def parse_pdf(pdf_file):
    """Extract readable text from an uploaded PDF resume."""
    try:
        pdf_bytes = pdf_file.getvalue()

        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
            extracted_text = "\n".join(
                page.get_text("text") for page in document
            )

        return extracted_text.strip()

    except Exception as error:
        st.error(f"Could not read the PDF: {error}")
        return ""


# ============================================================
# 6. MARKDOWN FORMATTING FOR THE GENERATED REPORT
# ============================================================

def format_inline(text):
    """Convert basic Markdown bold and italic into ReportLab markup."""

    text = escape(text)

    # Normalize punctuation that can render incorrectly in some PDF fonts.
    replacements = {
        "\u2013": "-",   # en dash
        "\u2014": "-",   # em dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u00a0": " ",   # non-breaking space
        "\u2022": "-",   # bullet character
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Bold: **text** or __text__
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text,
    )
    text = re.sub(
        r"__(.+?)__",
        r"<b>\1</b>",
        text,
    )

    # Italic: *text* or _text_
    text = re.sub(
        r"(?<!\*)\*([^*]+?)\*(?!\*)",
        r"<i>\1</i>",
        text,
    )
    text = re.sub(
        r"(?<!_)_([^_]+?)_(?!_)",
        r"<i>\1</i>",
        text,
    )

    return text


# ============================================================
# 7. PROFESSIONAL PDF REPORT GENERATOR
# ============================================================

def create_report_pdf(report_text):
    """
    Convert the AI-generated resume analysis into a formatted PDF.

    Supports:
    - Headings
    - Bold and italic text
    - Bullet points
    - Numbered lists
    - Markdown tables
    - Score card
    - Page numbers and footer
    """

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.68 * inch,
        title="AI Resume Analysis Report",
        author="AI Resume Analyzer",
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="CustomReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            textColor=colors.HexColor("#163A70"),
            alignment=1,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CustomReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#64748b"),
            alignment=1,
            spaceAfter=18,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CustomReportHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#163A70"),
            spaceBefore=13,
            spaceAfter=6,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CustomReportSubheading",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#2563a6"),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CustomReportBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#263244"),
            spaceAfter=6,
            splitLongWords=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CustomReportBullet",
            parent=styles["CustomReportBody"],
            leftIndent=15,
            firstLineIndent=-9,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CustomReportSmall",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748b"),
        )
    )

    story = []

    # --------------------------------------------------------
    # Report title
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "AI RESUME ANALYSIS",
            styles["CustomReportTitle"],
        )
    )

    story.append(
        Paragraph(
            "Resume review, improvement recommendations and career insights",
            styles["CustomReportSubtitle"],
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=colors.HexColor("#2563eb"),
            spaceAfter=15,
        )
    )

    # --------------------------------------------------------
    # Extract overall score, if included in the AI response
    # --------------------------------------------------------

    score_match = re.search(
        r"(?:overall\s+)?score\s*[:\-]?\s*(\d{1,3})\s*(?:/|out\s+of)\s*100",
        report_text,
        flags=re.IGNORECASE,
    )

    if score_match:
        score = min(100, int(score_match.group(1)))

        score_table = Table(
            [
                [
                    Paragraph(
                        "<b>OVERALL RESUME SCORE</b>",
                        styles["CustomReportBody"],
                    ),
                    Paragraph(
                        f"<font color='#163A70'><b>{score}/100</b></font>",
                        ParagraphStyle(
                            name="ScoreValue",
                            parent=styles["CustomReportBody"],
                            fontSize=19,
                            leading=23,
                            alignment=1,
                        ),
                    ),
                ]
            ],
            colWidths=[4.7 * inch, 1.8 * inch],
        )

        score_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor("#eff6ff"),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.8,
                        colors.HexColor("#bfdbfe"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        12,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        12,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                ]
            )
        )

        story.append(score_table)
        story.append(Spacer(1, 14))

    # --------------------------------------------------------
    # Clean report text
    # --------------------------------------------------------

    cleaned_text = report_text.replace("\r\n", "\n").replace("\r", "\n")

    # Prevent the overall score from appearing twice.
    if score_match:
        cleaned_text = re.sub(
            r"^\s*(?:[-*]\s*)?(?:overall\s+)?score\s*[:\-]?\s*"
            r"\d{1,3}\s*(?:/|out\s+of)\s*100\s*$",
            "",
            cleaned_text,
            flags=re.IGNORECASE | re.MULTILINE,
        )

    lines = cleaned_text.split("\n")
    index = 0

    # --------------------------------------------------------
    # Parse Markdown-style report line by line
    # --------------------------------------------------------

    while index < len(lines):
        line = lines[index].strip()

        # Skip empty lines and horizontal separators.
        if not line or re.fullmatch(r"[-*_]{3,}", line):
            index += 1
            continue

        # Markdown table detection.
        if "|" in line and index + 1 < len(lines):
            next_line = lines[index + 1].strip()

            is_table_header = (
                "|" in next_line
                and bool(
                    re.fullmatch(
                        r"[\s|:\-]+",
                        next_line,
                    )
                )
            )

            if is_table_header:
                table_lines = [line]
                index += 2

                while index < len(lines):
                    table_line = lines[index].strip()

                    if not table_line or "|" not in table_line:
                        break

                    table_lines.append(table_line)
                    index += 1

                parsed_rows = []

                for table_line in table_lines:
                    cells = [
                        cell.strip()
                        for cell in table_line.strip("|").split("|")
                    ]

                    # Skip Markdown separator rows.
                    if cells and all(
                        re.fullmatch(r":?-{2,}:?", cell.replace(" ", ""))
                        for cell in cells
                    ):
                        continue

                    parsed_rows.append(cells)

                if parsed_rows:
                    column_count = max(
                        len(row) for row in parsed_rows
                    )

                    normalized_rows = []

                    for row_number, row in enumerate(parsed_rows):
                        row = row + [""] * (column_count - len(row))

                        formatted_row = []

                        for cell in row:
                            formatted_cell = format_inline(cell)

                            if row_number == 0:
                                formatted_cell = (
                                    f"<b>{formatted_cell}</b>"
                                )

                            formatted_row.append(
                                Paragraph(
                                    formatted_cell,
                                    styles["CustomReportSmall"],
                                )
                            )

                        normalized_rows.append(formatted_row)

                    available_width = (
                        letter[0] - document.leftMargin - document.rightMargin
                    )

                    column_width = available_width / column_count

                    report_table = Table(
                        normalized_rows,
                        colWidths=[column_width] * column_count,
                        repeatRows=1,
                        hAlign="LEFT",
                    )

                    report_table.setStyle(
                        TableStyle(
                            [
                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (-1, 0),
                                    colors.HexColor("#163A70"),
                                ),
                                (
                                    "TEXTCOLOR",
                                    (0, 0),
                                    (-1, 0),
                                    colors.white,
                                ),
                                (
                                    "BACKGROUND",
                                    (0, 1),
                                    (-1, -1),
                                    colors.white,
                                ),
                                (
                                    "ROWBACKGROUNDS",
                                    (0, 1),
                                    (-1, -1),
                                    [
                                        colors.white,
                                        colors.HexColor("#f1f5f9"),
                                    ],
                                ),
                                (
                                    "GRID",
                                    (0, 0),
                                    (-1, -1),
                                    0.4,
                                    colors.HexColor("#cbd5e1"),
                                ),
                                (
                                    "VALIGN",
                                    (0, 0),
                                    (-1, -1),
                                    "TOP",
                                ),
                                (
                                    "LEFTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    6,
                                ),
                                (
                                    "RIGHTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    6,
                                ),
                                (
                                    "TOPPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    6,
                                ),
                                (
                                    "BOTTOMPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    6,
                                ),
                            ]
                        )
                    )

                    story.append(report_table)
                    story.append(Spacer(1, 10))

                continue

        # Markdown headings.
        if line.startswith("### "):
            heading = format_inline(line[4:].strip())
            story.append(
                Paragraph(
                    heading,
                    styles["CustomReportSubheading"],
                )
            )
            index += 1
            continue

        if line.startswith("## "):
            heading = format_inline(line[3:].strip())
            story.append(
                Paragraph(
                    heading,
                    styles["CustomReportHeading"],
                )
            )
            index += 1
            continue

        if line.startswith("# "):
            heading = format_inline(line[2:].strip())
            story.append(
                Paragraph(
                    heading,
                    styles["CustomReportHeading"],
                )
            )
            index += 1
            continue

        # Bullet points.
        if re.match(r"^(?:[-*•])\s+", line):
            bullet_text = re.sub(
                r"^(?:[-*•])\s+",
                "",
                line,
            )

            story.append(
                Paragraph(
                    f"&bull;&nbsp;&nbsp;{format_inline(bullet_text)}",
                    styles["CustomReportBullet"],
                )
            )
            index += 1
            continue

        # Numbered lists.
        numbered_match = re.match(r"^(\d+)[.)]\s+(.+)$", line)

        if numbered_match:
            number = numbered_match.group(1)
            item_text = numbered_match.group(2)

            story.append(
                Paragraph(
                    f"<b>{number}.</b>&nbsp;&nbsp;"
                    f"{format_inline(item_text)}",
                    styles["CustomReportBullet"],
                )
            )
            index += 1
            continue

        # Ordinary paragraph.
        story.append(
            Paragraph(
                format_inline(line),
                styles["CustomReportBody"],
            )
        )

        index += 1

    # --------------------------------------------------------
    # Footer and page numbers
    # --------------------------------------------------------

    def add_page_footer(canvas, doc):
        canvas.saveState()

        page_width, _ = letter

        canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
        canvas.setLineWidth(0.5)

        canvas.line(
            doc.leftMargin,
            0.48 * inch,
            page_width - doc.rightMargin,
            0.48 * inch,
        )

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))

        canvas.drawString(
            doc.leftMargin,
            0.30 * inch,
            "AI Resume Analyzer | Confidential Career Report",
        )

        canvas.drawRightString(
            page_width - doc.rightMargin,
            0.30 * inch,
            f"Page {doc.page}",
        )

        canvas.restoreState()

    # Build PDF.
    document.build(
        story,
        onFirstPage=add_page_footer,
        onLaterPages=add_page_footer,
    )

    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 8. GROQ AI CONFIGURATION
# ============================================================

def get_resume_analysis(resume_text):
    """Send resume text to Groq and return the analysis."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY was not found. Check your .env file."
        )

    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0.2,
        api_key=api_key,
    )

    prompt = PromptTemplate.from_template(
        """
You are an experienced resume reviewer and career coach.

Analyze the following resume carefully. Give clear, practical,
honest feedback in simple English.

Use Markdown formatting in your answer.

Include these sections:

# Overall Resume Score
Give a score out of 100 and briefly explain the score.

## 1. Resume Summary
Explain the overall quality of the resume.

## 2. Strengths
List the strongest points.

## 3. Weaknesses
Explain what is missing, unclear, or poorly presented.

## 4. Skills Analysis
Review the technical skills, tools, and soft skills mentioned.

## 5. Experience and Projects
Evaluate how the experience and projects are presented.
If the candidate has limited experience, suggest ways to improve
academic or personal projects.

## 6. ATS Compatibility
Explain how well the resume is likely to work with Applicant
Tracking Systems. Do not claim to have tested it against a real ATS.

## 7. Improvement Recommendations
Provide specific changes the candidate should make.

## 8. Suggested Resume Bullet Points
Give examples of stronger bullet points where appropriate.
Do not invent achievements, employment, qualifications, or metrics.
Clearly label examples that require the candidate to insert real details.

## 9. Final Action Plan
Give a prioritized checklist of the next steps.

Keep the feedback constructive, specific, and easy to understand.
Do not assume facts that are not stated in the resume.

RESUME TEXT:
{resume_text}
"""
    )

    chain = prompt | llm | StrOutputParser()

    return chain.invoke({"resume_text": resume_text})


# ============================================================
# 9. PAGE HEADER
# ============================================================

st.title("📄 AI Resume Checker")

st.markdown(
    """
    Upload your resume and let AI review its strengths, weaknesses,
    ATS compatibility, and areas for improvement.

    **Supported format:** PDF
    """
)

st.divider()


# ============================================================
# 10. RESUME UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Upload your resume (PDF)",
    type=["pdf"],
    help="Upload a text-based PDF resume for analysis.",
)

if uploaded_file is not None:
    if uploaded_file.name != st.session_state.resume_name:
        extracted_text = parse_pdf(uploaded_file)

        if extracted_text:
            st.session_state.resume_text = extracted_text
            st.session_state.resume_name = uploaded_file.name
            st.session_state.resume_report = ""

            st.success(
                f"Resume uploaded successfully: {uploaded_file.name}"
            )
        else:
            st.warning(
                "No readable text was found in this PDF. "
                "If it is a scanned resume, OCR may be required."
            )

# ------------------------------------------------------------
# Show resume status
# ------------------------------------------------------------

if st.session_state.resume_text:
    st.info(
        f"Current resume: {st.session_state.resume_name}"
    )

    with st.expander("Preview extracted resume text"):
        st.text(st.session_state.resume_text[:12000])

    st.caption(
        f"Extracted approximately "
        f"{len(st.session_state.resume_text.split())} words."
    )


# ============================================================
# 11. ANALYZE RESUME
# ============================================================

analyze_clicked = st.button(
    "🔍 Analyze My Resume",
    disabled=not bool(st.session_state.resume_text),
)

if analyze_clicked:
    try:
        with st.spinner(
            "AI is reviewing your resume. This may take a moment..."
        ):
            st.session_state.resume_report = get_resume_analysis(
                st.session_state.resume_text
            )

        st.success("Resume analysis completed!")

    except Exception as error:
        st.error(
            f"Could not analyze the resume: {error}"
        )


# ============================================================
# 12. DISPLAY REPORT AND DOWNLOAD PDF
# ============================================================

if st.session_state.resume_report:
    st.divider()
    st.subheader("📊 Your Resume Analysis")

    st.markdown(
        '<div class="report-container">',
        unsafe_allow_html=True,
    )

    st.markdown(st.session_state.resume_report)

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    try:
        pdf_bytes = create_report_pdf(
            st.session_state.resume_report
        )

        st.download_button(
            label="📥 Download Professional PDF Report",
            data=pdf_bytes,
            file_name="AI_Resume_Analysis_Report.pdf",
            mime="application/pdf",
        )

    except Exception as error:
        st.error(
            f"The analysis was generated, but the PDF could not "
            f"be created: {error}"
        )


# ============================================================
# 13. RESET ANALYSIS
# ============================================================

st.divider()

if st.session_state.resume_text or st.session_state.resume_report:
    if st.button("🔄 Clear Resume and Start Again"):
        st.session_state.resume_text = ""
        st.session_state.resume_name = ""
        st.session_state.resume_report = ""
        st.rerun()
