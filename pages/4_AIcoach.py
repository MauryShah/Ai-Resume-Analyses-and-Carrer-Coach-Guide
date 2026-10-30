
import io

import streamlit as st
import pymupdf
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

st.set_page_config(page_title="AI Career Coach", layout="wide")


def parse_pdf(file_bytes):
    with pymupdf.open(stream=io.BytesIO(file_bytes), filetype="pdf") as doc:
        return "\n\n".join(page.get_text() for page in doc)


st.markdown(
    """
    <div class="page-header">
        <h1>AI Career Coach</h1>
        <p>Get practical career guidance personalized to your resume.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Let's plan your next career move")

uploaded = st.file_uploader(
    "Upload your resume",
    type=["pdf"],
    key="coach_resume_upload",
)

if uploaded is not None:
    if st.session_state.get("coach_resume_name") != uploaded.name:
        st.session_state["coach_resume_text"] = parse_pdf(uploaded.getvalue())
        st.session_state["coach_resume_name"] = uploaded.name
        st.session_state["chat_history"] = []
        st.session_state.pop("quick_q", None)

resume = st.session_state.get("coach_resume_text", "")

if resume:
    st.success(f"Resume ready: {st.session_state['coach_resume_name']}")
else:
    st.info("Upload a PDF resume to start a personalized coaching conversation.")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

suggestions = [
    "What are my strongest skills?",
    "What jobs should I apply for?",
    "How can I improve my resume?",
    "What skills should I learn next?",
]

if resume and not st.session_state["chat_history"]:
    st.markdown("#### Suggested questions")
    cols = st.columns(2)

    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(suggestion, key=f"coach_suggestion_{i}"):
                st.session_state["quick_q"] = suggestion

for message in st.session_state["chat_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input(
    "Ask your career coach...",
    disabled=not bool(resume),
)

if "quick_q" in st.session_state:
    user_input = st.session_state.pop("quick_q")

if user_input:
    if not resume:
        st.warning("Please upload your resume first.")
    else:
        st.session_state["chat_history"].append(
            {"role": "user", "content": user_input}
        )

        history_text = "\n".join(
            f"{'Candidate' if message['role'] == 'user' else 'Coach'}: "
            f"{message['content']}"
            for message in st.session_state["chat_history"][:-1]
        )

        prompt = PromptTemplate(
            input_variables=["resume", "history", "question"],
            template="""
You are an experienced career coach who has read the candidate's resume.
Give practical and specific advice based on their background.
Keep your answer to 3 to 5 sentences unless more detail is needed.

Resume:
{resume}

Conversation so far:
{history}

Candidate question: {question}

Your response:
""",
        )

        llm = ChatGroq(model="openai/gpt-oss-20b")
        chain = prompt | llm | StrOutputParser()

        try:
            with st.spinner("Your career coach is thinking..."):
                reply = chain.invoke(
                    {
                        "resume": resume,
                        "history": history_text or "No previous conversation.",
                        "question": user_input,
                    }
                )

            st.session_state["chat_history"].append(
                {"role": "assistant", "content": reply}
            )
            st.rerun()

        except Exception as exc:
            st.error(f"Unable to get career advice: {exc}")
            # Remove the unanswered user message so it can be retried.
            if (
                st.session_state["chat_history"]
                and st.session_state["chat_history"][-1]["role"] == "user"
            ):
                st.session_state["chat_history"].pop()

if st.session_state["chat_history"]:
    st.divider()
    if st.button("Clear conversation"):
        st.session_state["chat_history"] = []
        st.rerun()
