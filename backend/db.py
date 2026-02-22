import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_profile_documents(profile_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT resume_path, id_card_path, bank_stmt_path FROM profiles WHERE id = %s",
        (profile_id,)
    )
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        return None
    print('returning result')
    return {
        "resume_path": result[0],
        "id_card_path": result[1],
        "bank_stmt_path": result[2]
    }

def save_profile_extractions(
    profile_id: str,
    resume_data,
    id_card_data,
    bank_stmt_data,
):
    """Insert extracted data for a profile into the database.

    This is a placeholder implementation that assumes a table named
    ``profile_extractions`` with columns ``profile_id``, ``resume_data``,
    ``id_card_data`` and ``bank_stmt_data``. The data columns are stored as
    JSON (or text) depending on the database configuration.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Placeholder SQL – adjust column types / table name as needed.
    insert_sql = """
        INSERT INTO profile_extractions
        (profile_id, extracted_data, doc_type)
        VALUES 
                (%s, %s, %s), 
                (%s, %s, %s), 
                (%s, %s, %s)
        ON CONFLICT (profile_id, doc_type) DO UPDATE SET
            extracted_data = EXCLUDED.extracted_data
        ;
    """
    tuples = (
        profile_id, resume_data, "resume",
        profile_id, id_card_data, "id_card",
        profile_id, bank_stmt_data, "bank_stmt",
    )
    cursor.execute(insert_sql, tuples)
    conn.commit()
    cursor.close()
    conn.close()

def get_profile_extractions(profile_id: str):
    """Retrieve previously saved extractions for a given profile.

    Returns a dictionary with keys ``resume_data``, ``id_card_data`` and
    ``bank_stmt_data`` if a record exists, otherwise ``None``.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    select_sql = """
    SELECT  
        extracted_data, doc_type
    FROM profile_extractions 
    WHERE profile_id = %s
    """
    cursor.execute(select_sql, (profile_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    if not result:
        return None
    
    data = {
        "resume": result[0],
        "id_card": result[1],
        "bank_stmt": result[2],
    }
    for row in result:
        data[row['doc_type']] = row['extracted_data']
    return data

def get_profile_data(profile_id: str):
    """Fetch profile information for the given ``profile_id``.

    This is a placeholder implementation that assumes a table named
    ``profiles`` with columns such as ``person_name``, ``person_age``, etc.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    select_sql = """
        SELECT 
            person_name, 
            person_age
        FROM profiles
        WHERE id = %s
    """
    cursor.execute(select_sql, (profile_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def save_profile_decision(profile_id: str, decision: str, reason: str) -> bool:
    """Mock function to save a recommendation decision for a profile.
    This is a placeholder that would normally persist the decision to Postgres.
    """
    db_conn = get_connection()
    cursor = db_conn.cursor()
    sql = f"""
    UPDATE profiles SET 
        processing_status = 'done',
        decision = %s,
        reason = %s
    WHERE id = %s
    """
    cursor.execute(sql, (decision, reason, profile_id))
    db_conn.commit()
    cursor.close()
    db_conn.close()
    return True