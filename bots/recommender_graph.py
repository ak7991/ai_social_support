import os
from time import time
from typing import Any, Dict, TypedDict
import psycopg2
import hashlib
from psycopg2.extras import RealDictCursor

from langgraph.graph import StateGraph, END, START
import ollama

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen3-vl:8b"
# MODEL_NAME = "qwen3-vl:235b-cloud"

client = ollama.Client(host=OLLAMA_HOST)

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres"
}


def _load_cache(filetype: str, path: str) -> str | None:
    """Return cached content if it exists.

    The cache filename follows the pattern ``cache_{filetype}_{basename}.txt``
    where ``basename`` is the original filename without extension.
    """
    basename = os.path.splitext(os.path.basename(path))[0]
    cache_file = f"./cache_{filetype}_{basename}.txt"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    return None


def _save_cache(filetype: str, path: str, content: str) -> None:
    """Save ``content`` to the cache file for the given ``filetype`` and ``path``."""
    basename = os.path.splitext(os.path.basename(path))[0]
    cache_file = f"./cache_{filetype}_{basename}.txt"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Failed to write cache file {cache_file}: {e}")

def get_db_connection(state: Dict[str, Any]) -> Dict[str, Any]:
    """Establish a PostgreSQL connection and merge the cursor into the existing state.
    Returns a new state dict that includes all previous keys plus ``db_cursor``.
    """
    db_connection = psycopg2.connect(**DB_CONFIG)
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    new_state = dict(state)
    new_state["db_cursor"] = cursor
    return new_state

def debug_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Debug helper that logs the current state without mutating it.
    Returning the original ``state`` ensures that keys such as ``profile_id`` are not lost.
    """
    print("[DEBUG] Current state:", state)
    # No breakpoint in production; keep the state unchanged.
    return state


# Gets profile data for the user, like name, age, gender, etc.
def query_profile_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch profile information for the given ``profile_id`` and merge it into state.
    """
    profile_id = state.get("profile_id")
    sql = f"""
        SELECT person_name, person_age
        FROM profiles
        WHERE id = '{profile_id}';
    """
    print("Executing SQL for profile data:", sql)
    cursor = state.get("db_cursor")
    cursor.execute(sql)
    profile_data = cursor.fetchone()
    new_state = dict(state)
    new_state["profile"] = profile_data
    return new_state

# Gets extracted data from profile's documents.
def query_profile_extractions(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch extracted data from profile's documents and merge into state.
    """
    profile_id = state.get("profile_id", "unknown")
    sql = f"""
    SELECT 
        extracted_data, doc_type
    FROM profile_extractions
    WHERE profile_id = '{profile_id}';
    """
    print("Executing SQL for user data:", sql)
    cursor = state.get("db_cursor")
    cursor.execute(sql)
    profile_data = cursor.fetchall()
    bank_stmt_data, resume_data, id_card_data = "", "", ""
    for data, doc_type in profile_data:
        if doc_type == "bank_statement":
            bank_stmt_data = data
        elif doc_type == "resume":
            resume_data = data
        elif doc_type == "id_card":
            id_card_data = data
    formatted_data = f"""
BANK STATEMENT:
{bank_stmt_data}
------------------------
RESUME:
{resume_data}
------------------------
ID CARD:
{id_card_data}
    """
    new_state = dict(state)
    new_state["extractions"] = formatted_data
    return new_state


def get_recommendation_rules() -> str:
    """Simple node that returns the recommendation rules in plain text."""
    rules = (
        "Recommendation Rules:\n"
        "1. Income must be below $30,000.\n"
        "2. Age between 18 and 65.\n"
        "3. No existing financial support."
    )
    return rules


def call_ollama(prompt: str) -> str:
    """Utility to call the Ollama model.
    The model runs at http://localhost:11434 and the model name is `qwen3-vl:8b`.
    This is a very thin wrapper around a curl request; replace with a proper client as needed.
    """
    cache_key = hashlib.sha256(prompt.encode()).hexdigest()[:10]
    # Check cache first
    cached = _load_cache("recommender", cache_key)
    if cached is not None:
        print("Returning cached resume parsing result")
        return cached

    t1 = time()
    response = client.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are an unbiased decision maker."},
            {"role": "user", "content": prompt}
        ]
    )
    print(f'Successfully called Ollama in {time() - t1} seconds')
    _save_cache("recommender", cache_key, response["message"]["content"])
    return response["message"]["content"]


def decision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LLM node that decides if a user is recommended for financial support.
    Returns a merged state containing the decision.
    """
    prompt = (
        "You are a financial support recommender. Based on the following information, decide if the user should be recommended for support.\n\n"
        f"Profile: {state.get('profile')}\n"
        f"Extractions: {state.get('extractions')}\n"
        f"Rules: {state.get('rules')}\n\n"
        "Answer with 'YES' or 'NO' and a short justification."
    )
    print("[DEBUG] Entering decision_node")
    decision = call_ollama(prompt)
    print("[DEBUG] Decision result:", decision)
    new_state = dict(state)
    new_state["decision"] = decision
    return new_state


def verification_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LLM node that verifies the decision and merges the verification result.
    """
    prompt = (
        "You are a verifier for the financial support recommendation. Review the decision and justification below.\n\n"
        f"Decision: {state.get('decision')}\n"
        "If the decision seems correct, respond with 'ACCEPTED'. If not, respond with 'RETHINK' and provide a brief reason."
    )
    print("[DEBUG] Entering verification_node")
    verification = call_ollama(prompt)
    print("[DEBUG] Verification result:", verification)
    new_state = dict(state)
    new_state["verification"] = verification
    return new_state

# Define a TypedDict for the agent state to provide static typing.
class AgentState(TypedDict, total=False):
    profile_id: str
    db_cursor: Any
    profile: Dict[str, Any]
    extractions: str
    rules: str
    decision: str
    verification: str

# Define the graph using the AgentState type
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("connect_db", get_db_connection)
workflow.add_node("debug_state", debug_state)
workflow.add_node("sql_profile_data", query_profile_data)
workflow.add_node("sql_extractions", query_profile_extractions)
workflow.add_node("rules", lambda s: {**s, "rules": get_recommendation_rules()})
workflow.add_node("decision", decision_node)
workflow.add_node("verification", verification_node)

# Define edges
workflow.add_edge(START, "connect_db")
workflow.add_edge("connect_db", "debug_state")
workflow.add_edge("debug_state", "sql_profile_data")
# workflow.add_edge("connect_db", "sql_profile_data")
workflow.add_edge("sql_profile_data", "sql_extractions")
workflow.add_edge("sql_extractions", "rules")
workflow.add_edge("rules", "decision")
workflow.add_edge("decision", "verification")
workflow.add_edge("verification", END)

# Compile the graph
app = workflow.compile()

# Example entry point (for testing)
if __name__ == "__main__":
    profile_id = os.getenv("PROFILE_ID", "bd7dbd2f-849d-4eb1-95ba-1c2fce920760")
    # Initial empty state; nodes will populate it
    result = app.invoke({"profile_id": profile_id})
    print("Final result:", result)
