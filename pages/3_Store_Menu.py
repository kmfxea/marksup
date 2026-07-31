import streamlit as st
from utils.supabase_client import get_supabase
import uuid

st.set_page_config(
    page_title="Store Menu • MarksUp",
    page_icon="🛵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# CSS - Orange buttons + clean UI
# --------------------------------------------------
st.markdown("""
<style>
    .stApp {
        max-width: 500px;
        margin: auto;
        padding-bottom: 120px;
    }
    h1, h2, h3 {
        color: #1a1a2e !important;
    }
    .item-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.15rem;
    }
    .item-price {
        font-size: 1rem;
        font-weight: 600;
        color: #FF6B00;
    }
    .item-desc {
        font-size: 0.85rem;
        color: #777;
        margin-top: 0.2rem;
    }
    .cart-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #FF6B00;
        color: white;
        padding: 1rem 1.2rem;
        text-align: center;
        font-weight: 600;
        font-size: 1.05rem;
        z-index: 999;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.12);
    }
    /* Orange buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 2.8rem;
        font-weight: 600;
        border: none !important;
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
# Check selected store
# --------------------------------------------------
if "selected_store_id" not in st.session_state:
    st.warning("No store selected.")
    if st.button("← Back to Stores"):
        st.switch_page("pages/2_Stores.py")
    st.stop()

store_id = st.session_state["selected_store_id"]
store_name = st.session_state.get("selected_store_name", "Store")

# --------------------------------------------------
# Initialize Cart
# --------------------------------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown(f"### {store_name}")
st.caption("Select items or create a custom list")

if st.button("← Back to Stores"):
    st.switch_page("pages/2_Stores.py")

st.write("")

# --------------------------------------------------
# Fetch Store + Items
# --------------------------------------------------
supabase = get_supabase()

try:
    store_data = supabase.table("stores")\
        .select("id, name, category, categories")\
        .eq("id", store_id)\
        .single()\
        .execute().data

    cats = store_data.get("categories") or []
    if not cats and store_data.get("category"):
        cats = [store_data.get("category")]
    store_category = " ".join(cats).lower()
except:
    store_category = ""

@st.cache_data(ttl=30)
def get_store_items(store_id):
    supabase = get_supabase()
    response = supabase.table("items")\
        .select("*")\
        .eq("store_id", store_id)\
        .eq("is_available", True)\
        .order("name")\
        .execute()
    return response.data

# --------------------------------------------------
# Helper: Upload Reseta
# --------------------------------------------------
def upload_reseta(file):
    if file is None:
        return None
    try:
        file_ext = file.name.split(".")[-1]
        file_name = f"reseta_{uuid.uuid4()}.{file_ext}"
        supabase.storage.from_("item-photos").upload(
            file_name,
            file.getvalue(),
            {"content-type": file.type}
        )
        return supabase.storage.from_("item-photos").get_public_url(file_name)
    except Exception as e:
        st.error(f"Failed to upload reseta: {e}")
        return None

# --------------------------------------------------
# CUSTOM LIST (Grocery / Pharmacy)
# --------------------------------------------------
is_grocery = "grocery" in store_category
is_pharmacy = "pharmacy" in store_category

if is_grocery or is_pharmacy:
    st.markdown("#### Custom List")

    if is_pharmacy:
        st.caption("Ilista ang gamot / items. Pwede ding mag-upload ng reseta.")
    else:
        st.caption("Ilista ang mga items na gusto mong ipabili.")

    shopping_list = st.text_area(
        "Your shopping list *",
        placeholder="Example:\n- 2kg rice\n- 1 tray egg\n- 3 canned tuna\n- Neozep 1 box",
        height=140,
        key="shopping_list"
    )

    reseta_file = None
    if is_pharmacy:
        st.write("**Reseta (Optional)**")
        reseta_file = st.file_uploader(
            "Upload prescription / reseta photo",
            type=["png", "jpg", "jpeg", "webp"],
            key="reseta_upload"
        )
        if reseta_file:
            st.image(reseta_file, width=180, caption="Reseta preview")

    estimated_budget = st.number_input(
        "Estimated Budget (₱)",
        min_value=50.0,
        value=200.0,
        step=50.0
    )

    if st.button("🛒 Add List to Cart", use_container_width=True):
        if not shopping_list.strip():
            st.error("Please type your shopping list first.")
        else:
            reseta_url = None
            if is_pharmacy and reseta_file:
                with st.spinner("Uploading reseta..."):
                    reseta_url = upload_reseta(reseta_file)

            list_type = "Custom Pharmacy List" if is_pharmacy else "Custom Grocery List"
            notes = shopping_list.strip()
            if reseta_url:
                notes += f"\n\n📄 Reseta: {reseta_url}"

            st.session_state.cart.append({
                "id": f"custom_{uuid.uuid4()}",
                "name": list_type,
                "price": float(estimated_budget),
                "quantity": 1,
                "image_url": None,
                "notes": notes,
                "is_custom": True,
                "reseta_url": reseta_url
            })

            st.success(f"{list_type} added to cart!")
            st.rerun()

    st.markdown("---")

# --------------------------------------------------
# Regular Items
# --------------------------------------------------
st.markdown("#### Available Items")

try:
    items = get_store_items(store_id)

    if not items:
        if not (is_grocery or is_pharmacy):
            st.info("No available items in this store right now.")
        else:
            st.caption("No preset items. You can use the Custom List above.")
    else:
        for item in items:
            col1, col2 = st.columns([1, 3])

            with col1:
                if item.get("image_url"):
                    st.image(item["image_url"], width=80)
                else:
                    st.markdown("### 📦")

            with col2:
                st.markdown(f"<div class='item-name'>{item['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='item-price'>₱{item['price']:.2f}</div>", unsafe_allow_html=True)
                if item.get("description"):
                    st.markdown(f"<div class='item-desc'>{item['description']}</div>", unsafe_allow_html=True)

            if st.button(f"Add to Cart • ₱{item['price']:.2f}", key=f"add_{item['id']}"):
                found = False
                for cart_item in st.session_state.cart:
                    if cart_item["id"] == item["id"]:
                        cart_item["quantity"] += 1
                        found = True
                        break
                if not found:
                    st.session_state.cart.append({
                        "id": item["id"],
                        "name": item["name"],
                        "price": float(item["price"]),
                        "quantity": 1,
                        "image_url": item.get("image_url"),
                        "notes": None,
                        "is_custom": False
                    })
                st.toast(f"Added {item['name']}!")
                st.rerun()

            st.markdown("---")

except Exception as e:
    st.error("Failed to load items.")
    st.caption(str(e))

# --------------------------------------------------
# Sticky Cart Bar
# --------------------------------------------------
cart = st.session_state.get("cart", [])
total_items = sum(item["quantity"] for item in cart)
total_amount = sum(item["price"] * item["quantity"] for item in cart)

if total_items > 0:
    st.markdown(f"""
    <div class="cart-bar">
        🛒 Cart ({total_items}) • ₱{total_amount:.2f}
    </div>
    """, unsafe_allow_html=True)

    if st.button("View Cart & Checkout", use_container_width=True):
        st.switch_page("pages/4_Cart.py")