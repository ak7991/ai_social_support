from fastapi import FastAPI, HTTPException
from db import get_profile_documents, save_profile_extractions, get_profile_extractions
from utils import resume_parser, id_card_parser, bank_statement_parser

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok", "message": "FastAPI server running"}

@app.post("/process")
def process_profiles():
    return {"status": "ok", "message": "FastAPI server running"}

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
    return f"""
---

RESUME DATA:
{data["resume_data"]}
---

ID CARD DATA:
{data["id_card_data"]}

---

BANK STATEMENT DATA:
{data["bank_stmt_data"]}

---

"""



@app.get("/profile/{profile_id}")
def get_profile_data(profile_id: str):
    """Fetch previously saved extractions for a given profile."""
    data = get_profile_data(profile_id)
    if not data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return f"""
---

PROFILE DATA:
name: {data["person_name"]}
age: {data["person_age"]}

---

"""


