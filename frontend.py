import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from utils import save_uploaded_file


st.session_state.user_email = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "login"

st.session_state.db_connection = None
st.session_state.db_cursor = None

# ------------------------
# Navigation Helpers
# ------------------------
def go_to(page_name):
    st.session_state.page = page_name


# ------------------------
# Login Page
# ------------------------
def login_page(db_connection, db_cursor):
    st.title("🔐 Login / Signup")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            q = f"select password from users where email = '{email}'"
            try:
                db_cursor.execute(q)
                actual_password = db_cursor.fetchone()['password']
                if password == actual_password:
                    print("login success!")
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    print('email ---> ', email)
                    go_to("dashboard")
                else:
                    print('actual_password: ', actual_password)
                    st.error("Invalid credentials")
            except Exception as e:
                print(e)
                st.error("Invalid credentials")

    with tab2:
        new_email = st.text_input("New Email")
        new_password = st.text_input("New Password", type="password")

        if st.button("Signup"):
            q = f"select email from users where email = '{new_email}'"
            db_cursor.execute(q)
            result = db_cursor.fetchone()
            if result is not None and len(result) == 1:
                st.warning("User already exists")
            else:
                i_q = f"insert into users (email, password) values ('{new_email}', '{new_password}')"
                db_cursor.execute(i_q)
                db_connection.commit()
                st.success("Signup successful! Please login.")


# ------------------------
# Dashboard Page
# ------------------------
def dashboard_page(db_cursor):
    st.title("📊 Dashboard")

    st.subheader("Submitted Profiles")
    user_email = st.session_state.user_email
    print('email ---> ', user_email)
    q = f"SELECT person_name, person_age, person_email, processing_status FROM profiles WHERE user_email = '{user_email}'"
    db_cursor.execute(q)
    profiles = db_cursor.fetchall()
    for profile in profiles:
        st.write(profile)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create New Profile"):
            go_to("create_profile")
    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            go_to("login")


# ------------------------
# Create Profile Page
# ------------------------
def create_profile_page():
    st.title("📝 Create New Profile")
    user_email = st.session_state.user_email
    name = st.text_input("Name")
    email = st.text_input("Email")
    age = st.number_input("Age", min_value=0, max_value=120)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    
    form = st.file_uploader("Attach form", type=["pdf", "png", "jpg"])
    bank_stmt = st.file_uploader("Attach bank statements", type=["pdf", "csv"])
    resume = st.file_uploader("Attach resume", type=["pdf", "jpg", "png"])
    credit_stmt = st.file_uploader("Attach credit stmt", type=["pdf", "csv"])
    id_card = st.file_uploader("Attach id card", type=["jpg", "png", "pdf"])
    files = [bank_stmt, resume, credit_stmt, id_card]
    names = ["bs", "rs", "cs", "id"]

    if st.button("Submit Profile"):
        if name and email and age:
            for file in [bank_stmt, resume, credit_stmt, id_card]:
                save_uploaded_file(file)
            st.success("Files uploaded")
            q = f"""
                INSERT INTO profiles
                 (user_email, person_name, person_age, person_email, form_path, 
                  bank_stmt_path, id_card_path, credit_stmt_path, resume_path,
                  processing_status)
                VALUES 
                ('{user_email}', '{name}', '{age}', '{email}', '{form.name}', 
                 '{bank_stmt.name}', '{id_card.name}', '{credit_stmt.name}', 
                  '{resume.name}', 'in-process')
                ;
            """
            st.session_state.db_cursor.execute(q)
            st.session_state.db_connection.commit()
            st.success("Profile submitted successfully!")
            go_to("dashboard")
        else:
            st.error("Name, age, email are required")

    if st.button("Back to Dashboard"):
        go_to("dashboard")


# ------------------------
# App Router
# ------------------------
db_connection = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    host="localhost",
    port=5432
)
db_cursor = db_connection.cursor(cursor_factory=RealDictCursor)
st.session_state.db_connection = db_connection
st.session_state.db_cursor = db_cursor

if not st.session_state.logged_in:
    login_page(db_connection, db_cursor)
else:
    if st.session_state.page == "dashboard":
        dashboard_page(db_cursor)
    elif st.session_state.page == "create_profile":
        create_profile_page()
