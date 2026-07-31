import streamlit as st
from utils.supabase_client import get_supabase

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="Stores • MarksUp",
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
        max-width: 500px;
        margin: auto;
    }

    h1 {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #1a1a2e !important;
        margin-bottom: 0.3rem !important;
    }

    .store-card {
        background: #ffffff;
        border: 1px solid #eee;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }

    .store-name {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }

    .store-category {
        font-size: 0.9rem;
        color: #777;
    }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 2.7rem;
        font-weight: 600;
        background-color: #FF6B00;
        color: white;
        border: none;
    }

    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("### Pumili ng Tindahan")
st.caption("Choose a store to start your order")

# --------------------------------------------------
# Back Button
# --------------------------------------------------
if st.button("← Back to Home"):
    st.switch_page("app.py")

st.write("")

# --------------------------------------------------
# Fetch Stores (Cached)
# --------------------------------------------------
@st.cache_data(ttl=60)
def get_active_stores():
    supabase = get_supabase()
    response = supabase.table("stores")\
        .select("id, name, description, category, logo_url")\
        .eq("is_active", True)\
        .order("name")\
        .execute()
    return response.data

# --------------------------------------------------
# Display Stores
# --------------------------------------------------
try:
    stores = get_active_stores()

    if not stores:
        st.info("Walang available na store ngayon.\nPakihintay o subukan ulit mamaya.")
    else:
        for store in stores:
            with st.container():
                st.markdown(f"""
                <div class="store-card">
                    <div class="store-name">{store['name']}</div>
                    <div class="store-category">{store.get('category') or store.get('description') or 'Store'}</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"Pumili • {store['name']}", key=store['id']):
                    st.session_state['selected_store_id'] = store['id']
                    st.session_state['selected_store_name'] = store['name']
                    st.switch_page("pages/3_Store_Menu.py")

except Exception as e:
    st.error("May problema sa pag-load ng stores. Subukan ulit.")
    st.caption(str(e))