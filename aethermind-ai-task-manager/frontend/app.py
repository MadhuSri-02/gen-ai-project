import os
from datetime import date
from typing import Any

import requests
import streamlit as st

st.set_page_config(page_title="AetherMind | AI Task Manager", page_icon="🧠", layout="wide")

DEFAULT_BACKEND = "https://aethermind-ai-task-manager.onrender.com"
try:
    BACKEND_URL = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", DEFAULT_BACKEND)).rstrip("/")
except Exception:
    BACKEND_URL = os.getenv("BACKEND_URL", DEFAULT_BACKEND).rstrip("/")

st.markdown("""

<style>
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    padding: 2rem;
    border-radius: 20px;
    background: linear-gradient(
        120deg,
        #f5f0ff 0%,
        #f0f5ff 50%,
        #ecfdfb 100%
    );
    border: 1px solid #e2e8f0;
    margin-bottom: 1.5rem;
    color: #111827;
    box-shadow: 0 4px 18px rgba(15, 23, 42, 0.05);
}

.hero h1 {
    color: #111827 !important;
    font-size: 2.6rem;
    font-weight: 800;
    margin-bottom: 1rem;
}

.hero p {
    color: #374151 !important;
    font-size: 1.05rem;
    line-height: 1.7;
}

.hero p b {
    color: #1f2937 !important;
}

.small-muted {
    color: #374151;
    font-size: 0.92rem;
}
</style>

""", unsafe_allow_html=True)

def api_request(method: str, path: str, **kwargs: Any) -> Any:
    try:
        response = requests.request(method, f"{BACKEND_URL}{path}", timeout=40, **kwargs)
        if not response.ok:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise RuntimeError(f"API error ({response.status_code}): {detail}")
        if response.status_code == 204:
            return None
        return response.json()
    except requests.ConnectionError as exc:
        raise RuntimeError(
            f"Cannot connect to the backend at {BACKEND_URL}. Start FastAPI in another terminal."
        ) from exc
    except requests.Timeout as exc:
        raise RuntimeError("The backend took too long to respond. Please try again.") from exc

def display_due(value: str | None) -> str:
    return value if value else "No deadline"

st.markdown("""
<div class="hero">
  <h1>🧠 AetherMind</h1>
  <p><b>Your personal AI task manager</b></p>
  <p>Turn everyday language into clear, organized tasks — then review and save them.</p>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1.15, 0.85], gap="large")
with left:
    st.subheader("✨ Create a task with AI")
    st.caption("Example: Finish my GenAI assignment by 2026-11-02. High priority.")
    user_text = st.text_area(
        "Describe your task",
        placeholder="I need to complete my Python assignment next Monday. It is high priority.",
        height=120,
        max_chars=3000,
        key="task_input",
    )
    if st.button("✨ Extract task details", type="primary", use_container_width=True):
        if len(user_text.strip()) < 5:
            st.error("Please describe the task in at least 5 characters.")
        else:
            with st.spinner("AI is extracting task details…"):
                try:
                    result = api_request("POST", "/extract", json={"text": user_text.strip()})
                    st.session_state["draft"] = result["extracted"]
                    st.success("Extraction successful. Review the fields before saving.")
                except RuntimeError as exc:
                    st.error(str(exc))

    st.divider()
    st.subheader("✍️ Or add a task manually")
    st.caption("Manual entry works even if you have not configured an AI API key.")
    with st.form("manual_task_form", clear_on_submit=True):
        manual_title = st.text_input("Task title", max_chars=200)
        manual_due = st.date_input("Deadline (optional)", value=None)
        manual_priority = st.selectbox("Priority", ["Medium", "High", "Low"])
        manual_notes = st.text_area("Notes (optional)", max_chars=1000)
        manual_submit = st.form_submit_button("Save task manually", use_container_width=True)
    if manual_submit:
        if len(manual_title.strip()) < 3:
            st.error("Task title must contain at least 3 characters.")
        else:
            payload = {
                "title": manual_title.strip(),
                "due_date": manual_due.isoformat() if isinstance(manual_due, date) else None,
                "priority": manual_priority,
                "notes": manual_notes.strip(),
            }
            try:
                api_request("POST", "/tasks", json=payload)
                st.success("Task saved to the database.")
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))

with right:
    st.subheader("🔎 Review extracted task")
    draft = st.session_state.get("draft")
    if draft:
        with st.form("review_task_form"):
            edited_title = st.text_input("Task title", value=draft.get("title", ""), max_chars=200)
            due_default = draft.get("due_date")
            try:
                due_value = date.fromisoformat(due_default) if due_default else None
            except ValueError:
                due_value = None
            edited_due = st.date_input("Deadline", value=due_value)
            edited_priority = st.selectbox(
                "Priority", ["Low", "Medium", "High"],
                index=["Low", "Medium", "High"].index(draft.get("priority", "Medium"))
            )
            edited_notes = st.text_area("Notes", value=draft.get("notes", ""), max_chars=1000)
            confirm_save = st.form_submit_button("✅ Confirm and save", type="primary", use_container_width=True)
        if confirm_save:
            if len(edited_title.strip()) < 3:
                st.error("Task title must contain at least 3 characters.")
            else:
                payload = {
                    "title": edited_title.strip(),
                    "due_date": edited_due.isoformat() if isinstance(edited_due, date) else None,
                    "priority": edited_priority,
                    "notes": edited_notes.strip(),
                }
                try:
                    saved = api_request("POST", "/tasks", json=payload)
                    st.success(f"Saved task #{saved['id']} to SQLite.")
                    st.session_state.pop("draft", None)
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))
    else:
        st.info("Your AI-extracted task fields will appear here. Review them and confirm before saving.")
    st.markdown('<p class="small-muted">AI output is a draft until you confirm it.</p>', unsafe_allow_html=True)

st.divider()
st.subheader("📋 Your tasks")
if st.button("↻ Refresh tasks"):
    st.rerun()
try:
    tasks = api_request("GET", "/tasks")
    if not tasks:
        st.info("No tasks yet. Create one above to get started.")
    else:
        pending = sum(1 for task in tasks if task["status"] == "Pending")
        completed = len(tasks) - pending
        m1, m2, m3 = st.columns(3)
        m1.metric("Total tasks", len(tasks))
        m2.metric("Pending", pending)
        m3.metric("Completed", completed)

        for task in tasks:
            with st.container(border=True):
                c1, c2 = st.columns([5, 1.5])
                with c1:
                    icon = "✅" if task["status"] == "Completed" else "📝"
                    st.markdown(f"**{icon} {task['title']}**")
                    st.caption(
                        f"Priority: {task['priority']}  ·  Deadline: {display_due(task.get('due_date'))}  ·  "
                        f"Status: {task['status']}  ·  ID: {task['id']}"
                    )
                    if task.get("notes"):
                        st.write(task["notes"])
                with c2:
                    if task["status"] == "Pending":
                        if st.button("Mark complete", key=f"complete_{task['id']}", use_container_width=True):
                            try:
                                api_request("PATCH", f"/tasks/{task['id']}/status", json={"status": "Completed"})
                                st.success("Task completed.")
                                st.rerun()
                            except RuntimeError as exc:
                                st.error(str(exc))
                    else:
                        if st.button("Reopen", key=f"reopen_{task['id']}", use_container_width=True):
                            try:
                                api_request("PATCH", f"/tasks/{task['id']}/status", json={"status": "Pending"})
                                st.rerun()
                            except RuntimeError as exc:
                                st.error(str(exc))
                    if st.button("Delete", key=f"delete_{task['id']}", use_container_width=True):
                        try:
                            api_request("DELETE", f"/tasks/{task['id']}")
                            st.success("Task deleted.")
                            st.rerun()
                        except RuntimeError as exc:
                            st.error(str(exc))
except RuntimeError as exc:
    st.error(str(exc))

with st.expander("ℹ️ Project architecture and API"):
    st.markdown("""
    **Workflow:** User text → Mistral AI JSON extraction → Pydantic schema validation → FastAPI → SQLite → Streamlit confirmation.

    - `POST /extract`: extracts structured task details using AI.
    - `POST /tasks`: validates and creates a database record.
    - `GET /tasks`: returns saved tasks.
    - `PATCH /tasks/{id}/status`: updates task status.
    - `DELETE /tasks/{id}`: deletes a task.
    - `GET /health`: deployment health check.

    **Error cases:** empty/short input, missing API key, AI rate limit, invalid JSON/schema, backend offline, and nonexistent task ID.
    """)
