import streamlit as st
from utils.supabase_client import get_supabase

st.set_page_config(
    page_title="Cart • MarksUp",
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
    .item-name {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1a1a2e;
    }
    .item-price {
        font-size: 0.95rem;
        color: #FF6B00;
        font-weight: 600;
    }
    .summary-box {
        background: #f8f9fa;
        border-radius: 14px;
        padding: 1.2rem;
        margin-top: 1rem;
        border: 1px solid #eee;
    }
    .grocery-box {
        background: #fff8f0;
        border: 1px solid #ffe0c2;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-top: 0.6rem;
        font-size: 0.9rem;
        white-space: pre-wrap;
    }
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 2.8rem;
        font-weight: 600;
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("### Your Cart")
st.caption("Review your items before checkout")

if st.button("← Back to Menu"):
    st.switch_page("pages/3_Store_Menu.py")

st.write("")

# --------------------------------------------------
# Initialize Cart
# --------------------------------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []

cart = st.session_state.cart

# --------------------------------------------------
# Empty Cart State
# --------------------------------------------------
if not cart:
    st.info("Your cart is empty.")
    if st.button("Browse Stores"):
        st.switch_page("pages/2_Stores.py")
    st.stop()

# --------------------------------------------------
# Cart Items
# --------------------------------------------------
for index, item in enumerate(cart):
    with st.container():
        col1, col2 = st.columns([1, 3])

        with col1:
            if item.get("image_url"):
                st.image(item["image_url"], width=70)
            else:
                st.markdown("### 🛒" if item.get("is_grocery") else "### 📦")

        with col2:
            st.markdown(f"<div class='item-name'>{item['name']}</div>", unsafe_allow_html=True)
            
            if item.get("is_grocery") and item.get("estimated_budget", 0) > 0:
                st.markdown(f"<div class='item-price'>Est. Budget: ₱{item['price']:.2f}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='item-price'>₱{item['price']:.2f}</div>", unsafe_allow_html=True)

            # Show grocery list if exists
            if item.get("is_grocery") and item.get("grocery_list"):
                st.markdown(f"""
                <div class="grocery-box">
                    <strong>Shopping List:</strong><br>
                    {item['grocery_list']}
                </div>
                """, unsafe_allow_html=True)

            # Quantity controls (hide for grocery custom list)
            if not item.get("is_grocery"):
                q1, q2, q3, q4 = st.columns([1, 1, 1, 2])

                with q1:
                    if st.button("−", key=f"minus_{index}"):
                        if item["quantity"] > 1:
                            item["quantity"] -= 1
                        else:
                            cart.pop(index)
                        st.rerun()

                with q2:
                    st.markdown(f"<div style='text-align:center; font-weight:600; padding-top:0.4rem'>{item['quantity']}</div>", unsafe_allow_html=True)

                with q3:
                    if st.button("+", key=f"plus_{index}"):
                        item["quantity"] += 1
                        st.rerun()

                with q4:
                    if st.button("Remove", key=f"remove_{index}"):
                        cart.pop(index)
                        st.rerun()
            else:
                if st.button("Remove", key=f"remove_{index}"):
                    cart.pop(index)
                    st.rerun()

        st.markdown("---")

# --------------------------------------------------
# Order Summary
# --------------------------------------------------
subtotal = sum(item["price"] * item["quantity"] for item in cart)
delivery_fee = 25.00
total = subtotal + delivery_fee

st.markdown("### Order Summary")

st.markdown(f"""
<div class="summary-box">
    <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
        <span>Subtotal</span>
        <span>₱{subtotal:.2f}</span>
    </div>
    <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
        <span>Delivery Fee</span>
        <span>₱{delivery_fee:.2f}</span>
    </div>
    <hr style="margin: 0.6rem 0;">
    <div style="display:flex; justify-content:space-between; font-weight:700; font-size:1.1rem;">
        <span>Total</span>
        <span>₱{total:.2f}</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.write("")

# --------------------------------------------------
# Checkout Button
# --------------------------------------------------
if st.button("Proceed to Checkout", use_container_width=True):
    st.session_state["cart_subtotal"] = subtotal
    st.session_state["delivery_fee"] = delivery_fee
    st.session_state["cart_total"] = total
    st.switch_page("pages/5_Checkout.py")