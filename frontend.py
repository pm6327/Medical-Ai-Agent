# frontend.py
import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000/ask"

TIMEOUT_SECONDS = 10  # adjust if needed

st.set_page_config(page_title="AI Mental Health Therapist", layout="wide")
st.title("🧠 SafeSpace – AI Mental Health Therapist")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat input
user_input = st.chat_input("What's on your mind today?")
if user_input:
    # Append user message immediately for responsive UI
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Show spinner while calling backend
    with st.spinner("Talking to the agent..."):
        try:
            headers = {"Content-Type": "application/json"}
            resp = response = requests.post(
                BACKEND_URL,
                json={"message": user_input},
                timeout=60,  # was 10
            )

        except requests.exceptions.RequestException as e:
            # Network/connection related errors
            err_msg = f"Could not reach backend: {e}"
            st.error(err_msg)
            st.session_state.chat_history.append(
                {"role": "assistant", "content": f"❌ {err_msg}"}
            )
        else:
            # We got a response from the backend (may or may not be JSON)
            raw = resp.text or "<empty response>"

            # If backend returned non-2xx, show helpful info
            if not resp.ok:
                st.error(f"Backend error: HTTP {resp.status_code}")
                st.write("Raw backend response:", raw)
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": f"❌ Backend returned HTTP {resp.status_code}. Check server logs.",
                    }
                )
            else:
                # Try to parse JSON safely (only once)
                try:
                    data = resp.json()
                except ValueError as e:
                    st.error("Backend did not return valid JSON.")
                    st.write("Raw backend response:", raw)
                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": "❌ Backend returned invalid JSON. See raw response above.",
                        }
                    )
                else:
                    # Defensive extraction of expected fields
                    answer = data.get("response") or data.get("message") or ""
                    tool = data.get("tool_called") or data.get("tool") or ""
                    # If backend returned an error-shaped JSON (like {"error": ...})
                    if "error" in data or not answer:
                        # show traceback or message if present (dev mode)
                        dev_msg = data.get("traceback") or data.get("message") or ""
                        st.warning(
                            "Backend returned an error object. See details below."
                        )
                        if dev_msg:
                            st.write(dev_msg)

                    display = (
                        f"{answer} WITH TOOL: [{tool}]"
                        if answer
                        else (
                            f"❌ No 'response' field in backend JSON. Full JSON: {data}"
                        )
                    )

                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": display}
                    )

# Render chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
