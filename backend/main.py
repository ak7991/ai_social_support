from fastapi import FastAPI, HTTPException
from db import (
    get_profile_documents,
    save_profile_extractions,
    get_profile_extractions,
    get_profile_data,
    save_profile_decision,
)
from utils import resume_parser, id_card_parser, bank_statement_parser
from bots import recommender_graph
from bots.chatbot import (
    _thread_states,
    graph,
    SystemMessage,
    HumanMessage,
    ChatRequest,
    ChatResponse,
    PROMPT,
    AgentState
)
from langchain_core.prompts import PromptTemplate
import requests

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok", "message": "FastAPI server running"}


@app.get("/v1/health")
def health():
    """Simple health check endpoint for the chatbot service."""
    return {"status": "ok", "message": "Chatbot server running"}


@app.post("/process/{profile_id}")
def process_profile(profile_id: str):
    # Fetch document paths from DB
    docs = get_profile_documents(profile_id)
    if not docs:
        raise HTTPException(status_code=404, detail="Profile not found")

    resume_path = docs["resume_path"]
    id_card_path = docs["id_card_path"]
    bank_stmt_path = docs["bank_stmt_path"]

    # Call parsers
    resume_data = resume_parser(resume_path)
    id_card_data = id_card_parser(id_card_path)
    bank_stmt_data = bank_statement_parser(bank_stmt_path)

    # Save extracted data to the database (placeholder implementation)
    try:
        save_profile_extractions(
            profile_id,
            resume_data,
            id_card_data,
            bank_stmt_data,
        )
    except Exception as e:
        # Log the error; for now we just raise an HTTP 500
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "profile_id": profile_id,
        "resume_data": resume_data,
        "id_card_data": id_card_data,
        "bank_stmt_data": bank_stmt_data
    }


@app.get("/extractions/{profile_id}")
def get_extractions(profile_id: str):
    """Fetch previously saved extractions for a given profile."""
    data = get_profile_extractions(profile_id)
    if not data:
        raise HTTPException(status_code=404, detail="Extractions not found for this profile")
    return {"status": "ok", "message": f"""
---

RESUME DATA:
{data["resume"]}
---

ID CARD DATA:
{data["id_card"]}

---

BANK STATEMENT DATA:
{data["bank_stmt"]}

---

"""
    }


@app.get("/profile/{profile_id}")
def get_profile(profile_id: str):
    """Fetch previously saved extractions for a given profile."""
    data = get_profile_data(profile_id)
    if not data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return {"status": "ok", "message": f"""
---

PROFILE DATA:
name: {data["person_name"]}
age: {data["person_age"]}

---

"""
    }


@app.post("/recommend/{profile_id}")
def recommend_profile(profile_id: str):
    """Invoke the recommender workflow for a profile and persist the decision.

    This endpoint constructs an initial agent state, invokes the compiled
    `StateGraph` workflow in `backend/bots/recommender_graph.py`, extracts the
    `decision` from the resulting state, and calls `save_profile_decision`.
    """
    try:
        init_state = {
            "profile_id": profile_id,
            "messages": [
                recommender_graph.SystemMessage(content="Starting financial support recommendation process.")
            ],
        }
        result = recommender_graph.app.invoke(init_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow invocation failed: {e}")

    raw_result = result.get("decision") if isinstance(result, dict) else None
    decision = "YES" if "YES" in raw_result[:5].upper() else "NO"
    save_profile_decision(profile_id, decision, raw_result)
    return {"profile_id": profile_id, "decision": decision, "state": result}


@app.post("/chat/{profile_id}", response_model=ChatResponse)
async def chat_endpoint(profile_id: str, payload: ChatRequest):
    """Receive a user message and return the assistant's reply.

    * ``payload.message`` – the new user message.
    * ``profile_id`` – identifier for the conversation (e.g., a UUID or user ID).
    """
    if not payload.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Retrieve or initialise thread state.
    if profile_id in _thread_states:
        messages = _thread_states[profile_id]
    else:
        # Fetch extraction context from the existing extraction endpoint.
        try:
            data = get_extractions(profile_id)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Failed to fetch extraction data: {exc}")
        print('Fetched extractions: ', data)
        placeholder_map = {"EXTRACTIONS": data.get("message", "")}
        prompt_template = PromptTemplate.from_template(PROMPT)
        filled_prompt = prompt_template.format(**placeholder_map)
        messages = [SystemMessage(content=filled_prompt)]
        _thread_states[profile_id] = messages

    # Append user message and invoke workflow.
    messages.append(HumanMessage(content=payload.message))
    print('invoking chatbot with messages: ', messages)
    result = await graph.ainvoke(AgentState(messages=messages))
    # Update stored state with assistant reply.
    _thread_states[profile_id] = result["messages"]
    return ChatResponse(reply=result["messages"][-1].content, thread_id=profile_id)

