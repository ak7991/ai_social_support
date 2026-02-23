import operator
import requests
from pydantic import BaseModel
from typing import List, Dict, Any, Annotated
from dataclasses import dataclass, field
import ollama
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import PromptTemplate

PROMPT = """
You are a Financial Assistance Support Assistant.
You are given extracted applicant data from uploaded documents and a final eligibility decision. Your task is to clearly explain the decision and provide supportive financial advice.

INPUT CONTEXT

{{EXTRACTIONS}}

INSTRUCTIONS
- Greet the applicant by name if available.
- Clearly state the decision.
Briefly explain the reason using provided data only.
If rejected:
    - Suggest practical steps to improve financial stability (budgeting, income growth, debt reduction, savings, documentation fixes).
If approved:
    - Congratulate briefly.
    - Advise responsible usage and long-term stability.
- If data is limited, give general financial advice.
- Be empathetic, professional, and non-judgmental.
- Do not invent facts or policies.

OUTPUT STRUCTURE
- Greeting
- Decision statement
- Explanation
- Actionable advice (bullet points)
- Encouraging closing

Keep the response concise but helpful.
"""
# In‑memory store for thread states. Each thread maps to an ``AgentState`` instance.
_thread_states: Dict[str, "AgentState"] = {}

# Model name – change if you use a different Ollama model.
# _MODEL_NAME = "qwen3-vl:8b"
_MODEL_NAME = "qwen3-vl:235b-cloud"

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    thread_id: str

def llm_node(state: Dict[str, Any]):
    """Call Ollama with the current message history.

    The state is expected to contain a ``messages`` key – a list of ``BaseMessage``
    objects compatible with Ollama's API.
    """
    try:
        # Convert LangChain/BaseMessage objects into Ollama's expected message format
        messages_payload = []
        for m in state.messages:
            if isinstance(m, HumanMessage):
                role = "user"
            elif isinstance(m, AIMessage):
                role = "assistant"
            elif isinstance(m, SystemMessage):
                role = "system"
            else:
                role = getattr(m, "role", getattr(m, "type", "user"))
            content = getattr(m, "content", str(m))
            messages_payload.append({"role": role, "content": content})

        response = ollama.chat(model=_MODEL_NAME, messages=messages_payload)
    except Exception as exc:
        raise RuntimeError(f"Ollama request failed: {exc}")

    # Ollama returns a dict with a ``message`` key containing ``content``.
    assistant_msg = response.get("message", {}).get("content", "")

    # Append the assistant reply back into the workflow state as an AIMessage
    assistant_obj = AIMessage(content=assistant_msg)
    return {"messages": state.messages + [assistant_obj]}

# Define the graph – a single node that ends the workflow.
# Define a custom state class for the LangGraph workflow.
@dataclass
class AgentState:
    messages: Annotated[List[BaseMessage], operator.add]

workflow = StateGraph(AgentState)
workflow.add_node("llm", llm_node)
workflow.set_entry_point("llm")
workflow.add_edge("llm", END)
graph = workflow.compile()

