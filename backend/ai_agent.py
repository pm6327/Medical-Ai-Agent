from langchain.tools import tool

from tools import query_medgemma, call_emergency

# ---------- Tools ----------


@tool
def ask_mental_health_specialist(query: str) -> str:
    """
    Generate a therapeutic response using the MedGemma model.
    Use this for all general user queries, mental health questions, emotional concerns,
    or to offer empathetic, evidence-based guidance in a conversational tone.
    """
    return query_medgemma(query)


@tool
def emergency_call_tool() -> None:
    """
    Place an emergency call to the safety helpline's phone number via Twilio.
    Use this only if the user expresses suicidal ideation, intent to self-harm,
    or describes a mental health emergency requiring immediate help.
    """
    call_emergency()


@tool
def find_nearby_therapists_by_location(location: str) -> str:
    """
    Finds and returns a list of licensed therapists near the specified location.
    """
    return (
        f"Here are some therapists near {location}:\n"
        "- Dr. Ayesha Kapoor - +1 (555) 123-4567\n"
        "- Dr. James Patel - +1 (555) 987-6543\n"
        "- MindCare Counseling Center - +1 (555) 222-3333"
    )


# ---------- LLM + Agent ----------

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from config import GEMINI_API_KEY

tools = [
    ask_mental_health_specialist,
    emergency_call_tool,
    find_nearby_therapists_by_location,
]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # or whatever is now working
    temperature=0.2,
    api_key=GEMINI_API_KEY,
    max_retries=0,  # <--- keep retries OFF while developing
)

graph = create_react_agent(llm, tools=tools)

SYSTEM_PROMPT = """
You are an AI engine supporting mental health conversations with warmth and vigilance.
You have access to three tools:

1. `ask_mental_health_specialist`: Use this tool to answer all emotional or psychological queries with therapeutic guidance.
2. `find_nearby_therapists_by_location`: Use this tool if the user asks about nearby therapists or if recommending local professional help would be beneficial.
3. `emergency_call_tool`: Use this immediately if the user expresses suicidal thoughts, self-harm intentions, or is in crisis.

Always take necessary action. Respond kindly, clearly, and supportively.
"""

# ---------- Stream parsing ----------


def parse_response(stream):
    tool_called_name = "None"
    final_response = None

    for item in stream:
        # Handle both (event, data) and plain dict formats
        if isinstance(item, tuple) and len(item) == 2:
            _event, s = item
        else:
            s = item

        if not isinstance(s, dict):
            continue

        # --- Tool usage ---
        tool_data = s.get("tools")
        if tool_data:
            tool_messages = tool_data.get("messages")
            if tool_messages and isinstance(tool_messages, list):
                for msg in tool_messages:
                    tool_called_name = getattr(msg, "name", "None")

        # --- Agent messages ---
        agent_data = s.get("agent")
        if agent_data:
            messages = agent_data.get("messages")
            if messages and isinstance(messages, list):
                for msg in messages:
                    content = getattr(msg, "content", None)
                    if not content:
                        continue

                    # If it's already a string
                    if isinstance(content, str):
                        final_response = content
                    # Newer Gemini returns a list of chunks: [{"type": "text", "text": "..."}]
                    elif isinstance(content, list):
                        texts = []
                        for chunk in content:
                            # chunk can be dict or object
                            if isinstance(chunk, dict):
                                if chunk.get("type") == "text":
                                    texts.append(chunk.get("text", ""))
                            else:
                                t = getattr(chunk, "text", None)
                                if t:
                                    texts.append(t)
                        if texts:
                            final_response = "\n".join(texts)

    return tool_called_name, final_response
