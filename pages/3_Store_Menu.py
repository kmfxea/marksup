import streamlit as st
from utils.supabase_client import get_supabase

st.set_page_config(
    page_title="Store Menu • MarksUp",
    page_icon="🛵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 2.8rem;
        font-weight: 600;
        background-color: #FF6B00;
        color: white;
        border: none;
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
st.caption("Select items or type your request")

if st.button("← Back to Stores"):
    st.switch_page("pages/2_Stores.py")

st.write("")

# --------------------------------------------------
# Fetch Store Info
# --------------------------------------------------
supabase = get_supabase()

try:
    store = supabase.table("stores")\
        .select("id, name, category")\
        .eq("id", store_id)\
        .single()\
        .execute().data
except:
    store = {"category": ""}

is_grocery = store.get("category", "").lower() == "grocery"

# --------------------------------------------------
# GROCERY FLOW (Advanced UI)
# --------------------------------------------------
if is_grocery:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fff8f0, #fff3e6); 
                border: 1px solid #ffe0c2; 
                border-radius: 16px; 
                padding: 1.3rem; 
                margin-bottom: 1.5rem;">
        <div style="font-size: 1.2rem; font-weight: 700; color: #1a1a2e; margin-bottom: 0.4rem;">
            🛒 Grocery Request
        </div>
        <div style="font-size: 0.9rem; color: #666;">
            Type the items you want us to buy. Be as specific as possible.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Your Shopping List")
    
    grocery_list = st.text_area(
        "Items to buy*",
        placeholder="Example:\n• 1kg Jasmine Rice\n• 2 dozen Eggs\n• 1L Cooking Oil\n• 3 cans Corned Beef\n• 1.5L Softdrinks",
        height=200,
        label_visibility="collapsed"
    )

    st.markdown("#### Estimated Budget (Optional)")
    st.caption("Para may idea ang rider kung magkano ang expected gastos")
    
    estimated_budget = st.number_input(
        "Budget",
        min_value=0.0,
        value=0.0,
        step=50.0,
        label_visibility="collapsed"
    )

    st.write("")

    with st.expander("💡 Tips for better results"):
        st.markdown("""
        - Maging specific (hal. “1kg Sinandomeng rice” instead of “rice”)
        - Lagyan ng quantity
        - Mention brand kung may preferred ka
        - Kung may alternative, isulat mo rin
        """)

    st.write("")

    if st.button("🛒 Add Grocery List to Cart", use_container_width=True):
        if not grocery_list.strip():
            st.error("Please type the items you want to buy.")
        else:
            st.session_state.cart = [{
                "id": "grocery-custom",
                "name": "Custom Grocery List",
                "price": estimated_budget if estimated_budget > 0 else 0,
                "quantity": 1,
                "image_url": None,
                "is_grocery": True,
                "grocery_list": grocery_list.strip(),
                "estimated_budget": estimated_budget
            }]

            st.success("Grocery list added to cart!")
            st.switch_page("pages/4_Cart.py")

# --------------------------------------------------
# REGULAR STORE FLOW (Menu)
# --------------------------------------------------
else:
    @st.cache_data(ttl=30)
    def get_store_items(store_id):
        response = supabase.table("items")\
            .select("*")\
            .eq("store_id", store_id)\
            .eq("is_available", True)\
            .order("name")\
            .execute()
        return response.data

    try:
        items = get_store_items(store_id)

        if not items:
            st.info("No available items in this store right now.")
        else:
            for item in items:
                col1, col2 = st.columns([1, 3])

                with col1:
                    if item.get("image_url"):
                        st.image(item["image_url"], width=80)
                    else:
                        st.markdown("### 📦")

                with col2:
                    st.markdown(f"**{item['name']}**")
                    st.markdown(f"₱{item['price']:.2f}")
                    if item.get("description"):
                        st.caption(item["description"])

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
                            "is_grocery": False
                        })
                    st.toast(f"Added {item['name']} to cart!")
                    st.rerun()

                st.markdown("---")

    except Exception as e:
        st.error("Failed to load items.")
        st.caption(str(e))

# --------------------------------------------------
# Cart Bar
# --------------------------------------------------
cart = st.session_state.get("cart", [])
total_items = sum(item["quantity"] for item in cart)
total_amount = sum(item["price"] * item["quantity"] for item in cart)

if total_items > 0:
    st.write("")
    st.info(f"🛒 Cart ({total_items}) • ₱{total_amount:.2f}")
    if st.button("View Cart & Checkout"):
        st.switch_page("pages/4_Cart.py")