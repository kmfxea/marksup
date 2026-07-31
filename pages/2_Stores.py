import streamlit as st
from utils.supabase_client import get_supabase
from utils.helpers import haversine_km, delivery_fee_from_km

try:
    from streamlit_js_eval import get_geolocation
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

st.set_page_config(
    page_title="Stores • MarksUp",
    page_icon="🛵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# CSS (same style)
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
    .store-distance {
        font-size: 0.88rem;
        color: #FF6B00;
        font-weight: 600;
        margin-top: 0.15rem;
    }
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
# Customer Location (for distance)
# --------------------------------------------------
if "customer_lat" not in st.session_state:
    st.session_state.customer_lat = None
if "customer_lng" not in st.session_state:
    st.session_state.customer_lng = None

customer_lat = st.session_state.get("customer_lat")
customer_lng = st.session_state.get("customer_lng")

if not (customer_lat and customer_lng):
    if HAS_GEO:
        if st.button("📍 Use my location to see distance", use_container_width=True):
            with st.spinner("Getting your location..."):
                loc = get_geolocation()
                if loc and loc.get("coords"):
                    st.session_state.customer_lat = loc["coords"]["latitude"]
                    st.session_state.customer_lng = loc["coords"]["longitude"]
                    st.success("Location set!")
                    st.rerun()
                else:
                    st.warning("Could not get location. Please allow GPS access.")
    else:
        st.caption("Install streamlit-js-eval to enable distance.")
else:
    st.caption(f"📍 Location on • distances shown below")

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
# Category Dropdown
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
        .select("id, name, description, category, categories, logo_url, latitude, longitude, address")\
        .eq("is_active", True)\
        .order("name")\
        .execute()
    return response.data

def get_store_categories(store):
    cats = store.get("categories") or []
    if not cats and store.get("category"):
        cats = [store["category"]]
    return cats

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
            if selected_category in get_store_categories(s)
        ]

    # Search filter
    if search:
        search_lower = search.lower()
        filtered = [
            s for s in filtered
            if search_lower in s.get("name", "").lower()
            or search_lower in (s.get("description") or "").lower()
            or any(search_lower in c.lower() for c in get_store_categories(s))
        ]

    # Sort by distance if location available
    if customer_lat and customer_lng:
        def sort_key(s):
            if s.get("latitude") and s.get("longitude"):
                return haversine_km(customer_lat, customer_lng, s["latitude"], s["longitude"]) or 999
            return 999
        filtered = sorted(filtered, key=sort_key)

    if not filtered:
        st.info("Walang store na tumugma sa search/filter mo.")
    else:
        st.caption(f"{len(filtered)} store(s) found")

        for store in filtered:
            cats = get_store_categories(store)
            cat_label = ", ".join(cats) if cats else (store.get("description") or "Store")

            # Distance line
            distance_label = ""
            if customer_lat and customer_lng and store.get("latitude") and store.get("longitude"):
                km = haversine_km(customer_lat, customer_lng, store["latitude"], store["longitude"])
                fee = delivery_fee_from_km(km)
                distance_label = f"📍 {km} km • ₱{fee:.0f} delivery"

            col1, col2 = st.columns([1, 3])

            with col1:
                if store.get("logo_url"):
                    st.image(store["logo_url"], width=70)
                else:
                    st.markdown("### 🏪")

            with col2:
                st.markdown(f"<div class='store-name'>{store['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='store-category'>{cat_label}</div>", unsafe_allow_html=True)
                if distance_label:
                    st.markdown(f"<div class='store-distance'>{distance_label}</div>", unsafe_allow_html=True)

            if st.button(f"Pumili • {store['name']}", key=store["id"]):
                st.session_state["selected_store_id"] = store["id"]
                st.session_state["selected_store_name"] = store["name"]
                st.switch_page("pages/3_Store_Menu.py")

            st.markdown("---")

except Exception as e:
    st.error("May problema sa pag-load ng stores.")
    st.caption(str(e))