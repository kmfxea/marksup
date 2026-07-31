import streamlit as st
from utils.supabase_client import get_supabase

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
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1a1a2e !important;
    }
    .store-name {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.15rem;
    }
    .store-category {
        font-size: 0.88rem;
        color: #777;
    }
    /* Orange primary buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 2.8rem;
        font-weight: 600;
        border: none;
        background-color: #FF6B00 !important;
        color: white !important;
    }
    .stButton > button:hover {
        background-color: #e65c00 !important;
        color: white !important;
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("### Pumili ng Tindahan")
st.caption("Choose a store to start your order")

if st.button("← Back to Home"):
    st.switch_page("app.py")

st.write("")

# --------------------------------------------------
# Search
# --------------------------------------------------
search = st.text_input(
    "🔍 Search store",
    placeholder="Type store name..."
)

st.write("")

# --------------------------------------------------
# Category Dropdown (cleaner)
# --------------------------------------------------
CATEGORIES = [
    "All",
    "Umagahan",
    "Tanghalian",
    "Meryenda",
    "Hapunan",
    "Grocery",
    "Pharmacy"
]

selected_category = st.selectbox(
    "📂 Category",
    CATEGORIES,
    index=0
)

st.write("")

# --------------------------------------------------
# Fetch Stores
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
    filtered = stores

    # Category filter
    if selected_category != "All":
        filtered = [
            s for s in filtered
            if s.get("category") and selected_category.lower() in s.get("category", "").lower()
        ]

    # Search filter
    if search:
        search_lower = search.lower()
        filtered = [
            s for s in filtered
            if search_lower in s.get("name", "").lower()
            or search_lower in (s.get("category") or "").lower()
            or search_lower in (s.get("description") or "").lower()
        ]

    if not filtered:
        st.info("Walang store na tumugma sa search/filter mo.")
    else:
        st.caption(f"{len(filtered)} store(s) found")

        for store in filtered:
            col1, col2 = st.columns([1, 3])

            with col1:
                if store.get("logo_url"):
                    st.image(store["logo_url"], width=70)
                else:
                    st.markdown("### 🏪")

            with col2:
                st.markdown(f"<div class='store-name'>{store['name']}</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='store-category'>{store.get('category') or store.get('description') or 'Store'}</div>",
                    unsafe_allow_html=True
                )

            if st.button(f"Pumili • {store['name']}", key=store["id"]):
                st.session_state["selected_store_id"] = store["id"]
                st.session_state["selected_store_name"] = store["name"]
                st.switch_page("pages/3_Store_Menu.py")

            st.markdown("---")

except Exception as e:
    st.error("May problema sa pag-load ng stores.")
    st.caption(str(e))