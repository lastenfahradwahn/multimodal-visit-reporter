"""
Streamlit frontend for the Multimodal Visit Reporter.

Communicates with a local FastAPI backend at http://localhost:8000.
"""

import requests
import streamlit as st
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE = "http://localhost:8000"
EXTRACT_URL = f"{API_BASE}/api/visits/extract"
SAVE_URL = f"{API_BASE}/api/visits/"
LIST_URL = f"{API_BASE}/api/visits/"

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Visit Reporter", layout="wide")
st.title("📋 Multimodal Visit Reporter")

# ---------------------------------------------------------------------------
# Helper: show raw error details only in development
# ---------------------------------------------------------------------------
def show_error(msg: str, details: str | None = None):
    """Display an error message and optionally detailed info."""
    st.error(msg)
    if details:
        with st.expander("Error details"):
            st.code(details)

# ---------------------------------------------------------------------------
# Sidebar: saved visits list
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📚 Saved Visits")
    try:
        resp = requests.get(LIST_URL)
        if resp.ok:
            visits = resp.json()
            if not visits:
                st.info("No visits saved yet.")
            else:
                for v in visits:
                    name = v.get("customer_name") or "Unknown"
                    date = v.get("visit_date", "")[:10]  # YYYY-MM-DD
                    sentiment = v.get("sentiment") or "no sentiment"
                    with st.expander(f"{name} – {date} ({sentiment})"):
                        st.json(v)
        else:
            show_error("Failed to load visits.", resp.text)
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Ensure the FastAPI server is running.")

# ---------------------------------------------------------------------------
# Main section: extraction
# ---------------------------------------------------------------------------
st.header("🎤 Extract a Visit Report")

# File uploader
uploaded_file = st.file_uploader(
    "Choose a file",
    type=["txt", "wav", "mp3", "m4a", "ogg", "jpg", "jpeg", "png", "gif", "webp"],
    help="Text notes, audio recordings, or whiteboard photos.",
)

# Input type selector
input_type = st.selectbox(
    "Input type",
    ["text", "audio", "image"],
    help="Choose the format of your file. Text for notes, Audio for voice recordings, Image for pictures.",
)

# Extract button
extract_btn = st.button("🔍 Extract Report", type="primary")

# ---------------------------------------------------------------------------
# Extraction logic
# ---------------------------------------------------------------------------
if extract_btn:
    if not uploaded_file:
        st.warning("Please upload a file first.")
    else:
        with st.spinner("Extracting… this may take a moment."):
            try:
                # Prepare the file for upload
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                data = {"input_type": input_type}

                resp = requests.post(EXTRACT_URL, files=files, data=data)

                if resp.ok:
                    report = resp.json()
                    # Store in session state for editing
                    st.session_state["extracted_report"] = report
                    st.success("Extraction complete! Review and edit below.")
                else:
                    # Try to extract a detail
                    detail = None
                    try:
                        detail = resp.json().get("detail")
                    except Exception:
                        pass
                    show_error(f"Extraction failed (HTTP {resp.status_code})", detail)

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Is the FastAPI server running?")
            except Exception as e:
                show_error("Unexpected error during extraction.", str(e))

# ---------------------------------------------------------------------------
# Editable form for extracted report
# ---------------------------------------------------------------------------
if "extracted_report" in st.session_state:
    report = st.session_state["extracted_report"]

    st.header("✏️ Edit Report")
    with st.form("edit_form"):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer Name", value=report.get("customer_name") or "")
            company = st.text_input("Company", value=report.get("company") or "")
            visit_date = st.text_input("Visit Date (YYYY-MM-DD)", value=report.get("visit_date") or "")
        with col2:
            topics = st.text_area(
                "Topics (comma separated)",
                value=", ".join(report.get("topics", [])) if report.get("topics") else "",
                help="e.g. product demo, pricing, support",
            )
            action_items = st.text_area(
                "Action Items (comma separated)",
                value=", ".join(report.get("action_items", [])) if report.get("action_items") else "",
                help="e.g. send email, schedule follow-up",
            )
            sentiment = st.selectbox(
                "Sentiment",
                ["positive", "neutral", "negative"],
                index=0 if report.get("sentiment") not in ["positive", "neutral", "negative"] else ["positive", "neutral", "negative"].index(report.get("sentiment")),
            )

        # Hidden field for raw_input_type
        raw_input_type = report.get("raw_input_type", input_type)

        # Save button
        save_btn = st.form_submit_button("💾 Save Report", type="primary")

    if save_btn:
        # Build the payload
        payload = {
            "customer_name": customer_name if customer_name else None,
            "company": company if company else None,
            "visit_date": visit_date if visit_date else None,
            "topics": [t.strip() for t in topics.split(",") if t.strip()],
            "action_items": [a.strip() for a in action_items.split(",") if a.strip()],
            "sentiment": sentiment,
            "raw_input_type": raw_input_type,
        }

        with st.spinner("Saving…"):
            try:
                resp = requests.post(SAVE_URL, json=payload)
                if resp.status_code == 201:
                    saved = resp.json()
                    st.success(f"Visit saved (ID: {saved.get('id')}).")
                    # Remove from session to avoid re-saving
                    del st.session_state["extracted_report"]
                    st.rerun()
                else:
                    detail = None
                    try:
                        detail = resp.json().get("detail")
                    except Exception:
                        pass
                    show_error(f"Save failed (HTTP {resp.status_code})", detail)
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Is the FastAPI server running?")
            except Exception as e:
                show_error("Unexpected error during save.", str(e))

# ---------------------------------------------------------------------------
# Reset button to clear extracted report
# ---------------------------------------------------------------------------
if "extracted_report" in st.session_state:
    if st.button("🗑️ Discard Report"):
        del st.session_state["extracted_report"]
        st.rerun()
