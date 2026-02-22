import operator
import requests
from fastapi import FastAPI, HTTPException
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
app = FastAPI()

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
        response = ollama.chat(model=_MODEL_NAME, messages=state.get("messages", []))
    except Exception as exc:
        raise RuntimeError(f"Ollama request failed: {exc}")
    # Ollama returns a dict with a ``message`` key containing ``content``.
    assistant_msg = response.get("message", {}).get("content", "")
    # Append the assistant reply to the message list.
    messages = list(state.get("messages", []))
    messages.append(AIMessage(assistant_msg))
    return {"messages": messages, "assistant_reply": assistant_msg}

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

@app.get("/v1/health")
def root():
    return {"status": "ok", "message": "Chatbot server running"}


@app.post("/chat/{profile_id}", response_model=ChatResponse)
async def chat(profile_id: str, payload: ChatRequest):
    """Receive a user message and return the assistant's reply.

    * ``thread_id`` – identifier for the conversation (e.g., a UUID or user ID).
    * ``payload.message`` – the new user message.
    """
    if not payload.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Check if a conversation already exists for this profile.
    if profile_id in _thread_states:
        # Existing thread – continue the conversation.
        messages = _thread_states[profile_id]
    else:
        # No existing thread – create a new one with the system prompt.
        # Fetch extraction context from the external service.
        try:
            extraction_resp = requests.get(f"http://localhost:8000/extractions/{profile_id}")
            extraction_resp.raise_for_status()
            data = extraction_resp.json()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Failed to fetch extraction data: {exc}")

        # Populate placeholders in the PROMPT.
        placeholder_map = {"EXTRACTIONS": data.get("message", "")}
        prompt_template = PromptTemplate.from_template(PROMPT)
        filled_prompt = prompt_template.format(**placeholder_map)
    
        # Initialise the message list with a system message containing the prompt.
        messages = [SystemMessage(content=filled_prompt)]
        # Store the new thread state.
        _thread_states[profile_id] = messages

    # Append the new user message.
    messages.append(HumanMessage(content=payload.message))
    # Run the LangGraph workflow with the updated state.
    result = await graph.ainvoke({"messages": messages})
    # Store the updated history (includes the assistant reply).
    _thread_states[profile_id] = result["messages"]
    return ChatResponse(reply=result["assistant_reply"], thread_id=profile_id)

# ---------------------------------------------------------------------------
# If this file is executed directly, start the server (useful for debugging).
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
