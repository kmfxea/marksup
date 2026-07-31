import streamlit as st
from utils.supabase_client import get_supabase

st.set_page_config(page_title="Admin Dashboard • MarksUp", page_icon="🛵", layout="centered", initial_sidebar_state="collapsed")

# Auth check
if "user" not in st.session_state or st.session_state["user"].get("role") != "admin":
    st.warning("Admin access only.")
    st.stop()

st.markdown("""
<style>
    .stApp { max-width: 500px; margin: auto; }
    .stButton > button { width: 100%; border-radius: 10px; height: 2.8rem; font-weight: 600; }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("Admin Dashboard")
st.caption(f"Welcome, {st.session_state['user'].get('full_name', 'Admin')}")

st.write("")

# Quick Stats
try:
    supabase = get_supabase()
    orders = supabase.table("orders").select("id", count="exact").execute()
    riders = supabase.table("riders").select("id", count="exact").eq("is_active", True).execute()
    stores = supabase.table("stores").select("id", count="exact").eq("is_active", True).execute()

    col1, col2, col3 = st.columns(3)
    col1.metric("Orders", orders.count or 0)
    col2.metric("Riders", riders.count or 0)
    col3.metric("Stores", stores.count or 0)
except:
    st.info("Stats unavailable.")

st.write("")
st.subheader("Management")

if st.button("📦  Manage Stores"):
    st.switch_page("pages/23_Admin_Stores.py")

if st.button("🛵  Manage Riders"):
    st.switch_page("pages/25_Admin_Riders.py")

if st.button("📋  Manage Orders"):
    st.switch_page("pages/22_Admin_Orders.py")

if st.button("🛍️  Manage Items"):
    st.switch_page("pages/24_Admin_Items.py")

st.write("")
if st.button("🔒 Logout"):
    st.session_state.clear()
    st.switch_page("app.py")