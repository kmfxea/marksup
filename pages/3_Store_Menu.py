import streamlit as st
from utils.supabase_client import get_supabase

st.set_page_config(
    page_title="Store Menu • MarksUp",
    page_icon="🛵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# CSS - Clean & Mobile Friendly
# --------------------------------------------------
st.markdown("""
<style>
    .stApp {
        max-width: 500px;
        margin: auto;
        padding-bottom: 100px;
    }
    h1, h2, h3 {
        color: #1a1a2e !important;
    }
    .item-card {
        background: #ffffff;
        border: 1px solid #eee;
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .item-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
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
        font-size: 1.1rem;
        z-index: 999;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 2.6rem;
        font-weight: 600;
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
st.caption("Select items to add to cart")

if st.button("← Back to Stores"):
    st.switch_page("pages/2_Stores.py")

st.write("")

# --------------------------------------------------
# Fetch Items
# --------------------------------------------------
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
# Display Items
# --------------------------------------------------
try:
    items = get_store_items(store_id)

    if not items:
        st.info("No available items in this store right now.")
    else:
        for item in items:
            with st.container():
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

                # Add to Cart button
                if st.button(f"Add to Cart • ₱{item['price']:.2f}", key=f"add_{item['id']}"):
                    # Check if item already in cart
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
                            "image_url": item.get("image_url")
                        })
                    st.toast(f"Added {item['name']} to cart!")
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