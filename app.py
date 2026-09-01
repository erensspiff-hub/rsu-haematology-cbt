# app.py

import streamlit as st
import time
import csv
import os
from data import question_data

MASTER_FILE = "master_score_list.csv"
TEST_DURATION_MINUTES = 30  # 30-minute exam timer

st.set_page_config(page_title="RSU MLS 462 CBT Portal", page_icon="🩸", layout="centered")

st.title("🩸 RIVERS STATE UNIVERSITY")
st.subheader("Faculty of Medical Laboratory Science")
st.write("**MLS 462/HBT 402: Practical Haematology Computer-Based Test**")
st.markdown("---")


# --- QUESTION CLASS DEFINITION (Combined to avoid import errors) ---
class Question:
    def __init__(self, q_text, q_choices, q_answer, q_type="single"):
        self.text = q_text
        self.choices = q_choices
        self.answer = q_answer
        self.type = q_type


def check_already_submitted(matric_no):
    if not os.path.exists(MASTER_FILE):
        return False
    with open(MASTER_FILE, mode="r") as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[1] == matric_no:
                return True
    return False


def save_to_master_list(name, matric_no, score, total):
    file_exists = os.path.exists(MASTER_FILE)
    with open(MASTER_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Full Name", "Matriculation Number", "Score", "Total", "Percentage (%)", "Timestamp"])
        percentage = round((score / total) * 100, 2)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([name, matric_no, score, total, percentage, timestamp])


# --- GLOBAL SESSION STATE INITIALIZATION ---
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "score" not in st.session_state:
    st.session_state.score = 0
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "question_bank" not in st.session_state:
    st.session_state.question_bank = [
        Question(item["text"], item["choices"], item["answer"], item.get("type", "single"))
        for item in question_data
    ]

# --- PHASE 1: LOGIN SCREEN ---
if not st.session_state.submitted:
    st.info(
        "Please enter your details to begin. Note: Multiple attempts are locked out, and the test is timed for 30 minutes.")

    with st.form("login_form"):
        full_name = st.text_input("Full Name (Surname First):")
        matric_no = st.text_input("Matriculation Number (e.g., RSU/2022/...):").upper()
        start_button = st.form_submit_button("Start Test")

        if start_button:
            if not full_name or not matric_no:
                st.error("❌ Both Full Name and Matriculation Number are required!")
            elif check_already_submitted(matric_no):
                st.error("🚨 ACCESS DENIED: A submission already exists for this Matriculation Number.")
            else:
                st.session_state.full_name = full_name
                st.session_state.matric_no = matric_no
                st.session_state.submitted = True
                st.session_state.start_time = time.time()
                st.rerun()

# --- PHASE 2: EXAM SESSION & TIMER ---
elif st.session_state.submitted and st.session_state.current_q < len(st.session_state.question_bank):

    elapsed_seconds = time.time() - st.session_state.start_time
    total_allowed_seconds = TEST_DURATION_MINUTES * 60
    remaining_seconds = total_allowed_seconds - elapsed_seconds

    if remaining_seconds <= 0:
        st.warning("⏰ Time is up! Your exam has been automatically submitted.")
        st.session_state.current_q = len(st.session_state.question_bank)
        st.rerun()

    mins, secs = divmod(int(remaining_seconds), 60)
    st.sidebar.markdown("### ⏱️ Time Remaining")
    st.sidebar.metric(label="Countdown", value=f"{mins:02d}:{secs:02d}")

    q_bank = st.session_state.question_bank
    idx = st.session_state.current_q
    current_question = q_bank[idx]

    st.write(f"### Question {idx + 1} of {len(q_bank)}")
    st.write(f"**{current_question.text}**")

    # Render UI dynamically based on Question Type
    if current_question.type in ["single", "true_false"]:
        user_choice = st.radio("Select option:", current_question.choices, key=f"q_{idx}")

        if st.button("Submit Answer"):
            selected_letter = user_choice.split(")")[0].strip().lower()
            if selected_letter == current_question.answer.lower():
                st.session_state.score += 1
            st.session_state.current_q += 1
            st.rerun()

    elif current_question.type == "multiple":
        st.info("💡 Note: This question has multiple correct answers. Select all that apply.")
        user_selections = []
        for choice in current_question.choices:
            if st.checkbox(choice, key=f"q_{idx}_{choice}"):
                user_selections.append(choice.split(")")[0].strip().lower())

        if st.button("Submit Answer"):
            if set(user_selections) == set([ans.lower() for ans in current_question.answer]):
                st.session_state.score += 1
            st.session_state.current_q += 1
            st.rerun()

    time.sleep(1)
    st.rerun()

# --- PHASE 3: RESULTS SCREEN & CSV EXPORT ---
else:
    total = len(st.session_state.question_bank)
    score = st.session_state.score
    percentage = round((score / total) * 100, 2)

    if "saved" not in st.session_state:
        save_to_master_list(st.session_state.full_name, st.session_state.matric_no, score, total)
        st.session_state.saved = True

    st.success("🎉 Test Completed & Submitted Successfully!")
    st.write(f"**Candidate:** {st.session_state.full_name}")
    st.write(f"**Matric No:** {st.session_state.matric_no}")
    st.metric(label="Your Final Score", value=f"{score} / {total}", delta=f"{percentage}%")
    st.info(
        "📊 Your score has been securely compiled into your continuous assessment master spreadsheet (`master_score_list.csv`). You may now close this page.")