import streamlit as st
from utils.supabase_client import get_supabase

st.set_page_config(
    page_title="Login • MarksUp",
    page_icon="🛵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# CSS
# --------------------------------------------------
st.markdown("""
<style>
    .stApp {
        max-width: 420px;
        margin: auto;
        padding-top: 2rem;
    }
    h1 {
        font-size: 1.8rem !important;
        text-align: center;
        color: #1a1a2e !important;
    }
    .stButton > button {
        width: 100%;
        height: 3rem;
        border-radius: 10px;
        background-color: #FF6B00;
        color: white;
        font-weight: 600;
        border: none;
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("<h1>MarksUp Login</h1>", unsafe_allow_html=True)
st.caption("Rider & Admin access only")

st.write("")

# --------------------------------------------------
# Login Form
# --------------------------------------------------
email = st.text_input("Email", placeholder="your@email.com")
password = st.text_input("Password", type="password")

login_btn = st.button("Login")

if login_btn:
    if not email or not password:
        st.error("Please enter both email and password.")
    else:
        try:
            supabase = get_supabase()

            # Sign in
            result = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            user = result.user

            if user:
                # Get profile/role
                profile = supabase.table("profiles")\
                    .select("role, full_name, rider_id")\
                    .eq("id", user.id)\
                    .single()\
                    .execute()

                if profile.data:
                    role = profile.data["role"]
                    st.session_state["user"] = {
                        "id": user.id,
                        "email": email,
                        "role": role,
                        "full_name": profile.data.get("full_name"),
                        "rider_id": profile.data.get("rider_id")
                    }

                    st.success(f"Welcome {profile.data.get('full_name') or email}!")

                    # Redirect based on role
                    if role == "admin":
                        st.switch_page("pages/21_Admin_Dashboard.py")
                    elif role == "rider":
                        st.switch_page("pages/11_Rider_Dashboard.py")
                    else:
                        st.error("Unknown role.")
                else:
                    st.error("No profile found. Contact admin.")
            else:
                st.error("Login failed.")

        except Exception as e:
            st.error(f"Login failed: {str(e)}")