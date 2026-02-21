import streamlit as st
import psycopg2

# ------------------------
# Mock Database (In-Memory)
# ------------------------
if "users" not in st.session_state:
    st.session_state.users = {}

if "profiles" not in st.session_state:
    st.session_state.profiles = [
        {"name": "Rahul Sharma", "age": 28, "gender": "Male", "status": "Pending"},
        {"name": "Anita Verma", "age": 32, "gender": "Female", "status": "Approved"},
    ]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "login"


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
            actual_password = db_cursor.execute(q).fetchone()[0]
            if password == actual_password:
                print("login success!")
                st.session_state.logged_in = True
                go_to("dashboard")
            else:
                st.error("Invalid credentials")

    with tab2:
        new_email = st.text_input("New Email")
        new_password = st.text_input("New Password", type="password")

        if st.button("Signup"):
            q = f"select email from users where email = '{new_email}'"
            if len(db_cursor.execute(q).fetchone()) == 1:
                st.warning("User already exists")
            else:
                i_q = f"insert into users (email, password) values ('{new_email}', '{new_password}')"
                st.session_state.users[new_email] = new_password
                st.success("Signup successful! Please login.")


# ------------------------
# Dashboard Page
# ------------------------
def dashboard_page():
    st.title("📊 Dashboard")

    st.subheader("Submitted Profiles")

    for profile in st.session_state.profiles:
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

    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, max_value=120)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])

    doc_type = st.selectbox(
        "Select Document Type",
        ["Bank Statement", "ID Card", "Resume", "Credit Report"]
    )

    uploaded_file = st.file_uploader("Attach Document")

    if st.button("Submit Profile"):
        if name:
            st.session_state.profiles.append({
                "name": name,
                "age": age,
                "gender": gender,
                "status": "Pending"
            })
            st.success("Profile submitted successfully!")
            go_to("dashboard")
        else:
            st.error("Name is required")

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
db_cursor = db_connection.cursor()
if not st.session_state.logged_in:
    login_page(db_connection, db_cursor)
else:
    if st.session_state.page == "dashboard":
        dashboard_page()
    elif st.session_state.page == "create_profile":
        create_profile_page()
