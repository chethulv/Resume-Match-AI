import streamlit as st
import openai
import docx2txt
import fitz  # PyMuPDF
import os
from email.message import EmailMessage
import smtplib

# -------------------- CONFIG --------------------
openai.api_key = st.secrets["OPENAI_API_KEY"]  # store your API key in Streamlit secrets
EMAIL_RECEIVER = "venchethulv@gmail.com"

# -------------------- HELPERS --------------------
def extract_text(file):
    if file.name.endswith(".docx"):
        return docx2txt.process(file)
    elif file.name.endswith(".pdf"):
        text = ""
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    else:
        return ""

def send_email(subject, body, sender_email, sender_pass):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, sender_pass)
        smtp.send_message(msg)
        
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])  # Set once globally if you prefer

def get_match_score(jd, resume_text):
    prompt = f"""
You are an expert technical recruiter. Given the following job description and resume, score how well the resume matches the job out of 100. Also provide a short explanation and improvement suggestions.

Job Description:
{jd}

Resume:
{resume_text}

Return this in JSON:
{{"score": <0-100>, "explanation": "...", "suggestions": "..."}}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    result = eval(response.choices[0].message.content)
    return result


# -------------------- UI --------------------
st.title("🎯 ResumeMatchAI for Recruiters")
st.write("Upload a job description and multiple resumes. We'll rank them using AI.")

# Job Description
job_description = st.text_area("📄 Paste Job Description", height=250)

# Resume Upload
uploaded_files = st.file_uploader("📂 Upload Resumes (.pdf or .docx)", accept_multiple_files=True)

# API Key Input (Optional)
if "OPENAI_API_KEY" not in st.secrets:
    openai.api_key = st.text_input("🔑 Enter your OpenAI API key", type="password")

# Email Credentials
st.divider()
st.subheader("📨 Feedback Form")
with st.form("feedback_form"):
    feedback_name = st.text_input("Your Name")
    feedback_email = st.text_input("Your Email")
    feedback_message = st.text_area("Your Feedback", height=100)
    sender_email = st.text_input("📧 Your Gmail address to send feedback", type="default")
    sender_pass = st.text_input("🔐 App password (Gmail App Password)", type="password")
    submit_feedback = st.form_submit_button("Send Feedback")

    if submit_feedback:
        if feedback_message and sender_email and sender_pass:
            subject = f"ResumeMatchAI Feedback from {feedback_name}"
            body = f"From: {feedback_name} ({feedback_email})\n\n{feedback_message}"
            send_email(subject, body, sender_email, sender_pass)
            st.success("✅ Feedback sent successfully!")
        else:
            st.error("❌ All fields are required for sending feedback.")

# Resume Matching
st.divider()
if st.button("🚀 Match Resumes to Job Description") and job_description and uploaded_files:
    results = []
    with st.spinner("Processing resumes..."):
        for file in uploaded_files:
            resume_text = extract_text(file)
            score_data = get_match_score(job_description, resume_text)
            results.append((file.name, score_data['score'], score_data['explanation'], score_data['suggestions']))

    # Show Results
    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
    for name, score, explanation, suggestions in sorted_results:
        st.markdown(f"### 📌 {name}")
        st.write(f"**Score:** {score}/100")
        st.write(f"**Explanation:** {explanation}")
        st.write(f"**Suggestions:** {suggestions}")
        st.divider()
