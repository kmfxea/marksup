import streamlit as st
from utils.supabase_client import get_supabase
from datetime import datetime

st.set_page_config(
    page_title="Checkout • MarksUp",
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
    .summary-box {
        background: #f8f9fa;
        border-radius: 14px;
        padding: 1.2rem;
        margin-top: 1rem;
        border: 1px solid #eee;
    }
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3rem;
        font-weight: 600;
        background-color: #FF6B00;
        color: white;
        border: none;
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Validate Cart
# --------------------------------------------------
if "cart" not in st.session_state or not st.session_state.cart:
    st.warning("Your cart is empty.")
    if st.button("Go to Stores"):
        st.switch_page("pages/2_Stores.py")
    st.stop()

if "selected_store_id" not in st.session_state:
    st.warning("No store selected.")
    st.stop()

cart = st.session_state.cart
store_id = st.session_state["selected_store_id"]
store_name = st.session_state.get("selected_store_name", "Store")

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("### Checkout")
st.caption("Please fill in your delivery details")

if st.button("← Back to Cart"):
    st.switch_page("pages/4_Cart.py")

st.write("")

# --------------------------------------------------
# Customer Details
# --------------------------------------------------
st.subheader("Delivery Details")

customer_name = st.text_input("Full Name*")
customer_contact = st.text_input("Contact Number*")
delivery_address = st.text_area(
    "Complete Delivery Address*",
    placeholder="Building name, Floor, Unit No., Street..."
)
landmark = st.text_input("Landmark (optional)")

st.write("")

# Preferred Time
preferred_time = st.radio(
    "Preferred Time",
    ["ASAP", "Schedule for later"],
    horizontal=True
)

scheduled_time = None
if preferred_time == "Schedule for later":
    scheduled_time = st.time_input("Select time")

st.write("")

# --------------------------------------------------
# Extra Fees
# --------------------------------------------------
st.subheader("Additional Options")

needs_floor = st.checkbox("Deliver to 2nd floor or higher? (+₱15 Floor Fee)")
is_heavy = st.checkbox("Heavy / Grocery order? (+₱50 Handling Fee)")

st.write("")

# --------------------------------------------------
# Payment Method
# --------------------------------------------------
st.subheader("Payment Method")

payment_method = st.radio(
    "Choose payment method",
    ["Cash", "GCash"],
    horizontal=True
)

if payment_method == "GCash":
    st.info("After a rider accepts your order, you will see the rider’s GCash number and QR code.")

st.write("")

# --------------------------------------------------
# Order Summary
# --------------------------------------------------
subtotal = sum(item["price"] * item["quantity"] for item in cart)
delivery_fee = 25.00
floor_fee = 15.00 if needs_floor else 0.00
handling_fee = 50.00 if is_heavy else 0.00
total = subtotal + delivery_fee + floor_fee + handling_fee

st.markdown("### Order Summary")

st.markdown(f"""
<div class="summary-box">
    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
        <span>Store</span>
        <span>{store_name}</span>
    </div>
    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
        <span>Subtotal</span>
        <span>₱{subtotal:.2f}</span>
    </div>
    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
        <span>Delivery Fee</span>
        <span>₱{delivery_fee:.2f}</span>
    </div>
    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
        <span>Floor Fee</span>
        <span>₱{floor_fee:.2f}</span>
    </div>
    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
        <span>Handling Fee</span>
        <span>₱{handling_fee:.2f}</span>
    </div>
    <hr style="margin: 0.6rem 0;">
    <div style="display:flex; justify-content:space-between; font-weight:700; font-size:1.15rem;">
        <span>Total</span>
        <span>₱{total:.2f}</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.write("")

# --------------------------------------------------
# Place Order
# --------------------------------------------------
if st.button("Place Order"):
    # Validation
    if not customer_name or not customer_contact or not delivery_address:
        st.error("Please fill in Name, Contact Number, and Delivery Address.")
    else:
        try:
            with st.spinner("Placing your order..."):
                supabase = get_supabase()

                # Create Order
                order_data = {
                    "customer_name": customer_name,
                    "customer_contact": customer_contact,
                    "delivery_address": delivery_address,
                    "landmark": landmark,
                    "store_id": store_id,
                    "status": "Order Placed",
                    "payment_method": payment_method,
                    "items_total": subtotal,
                    "delivery_fee": delivery_fee,
                    "floor_fee": floor_fee,
                    "handling_fee": handling_fee,
                    "total_amount": total,
                    "preferred_time": "ASAP" if preferred_time == "ASAP" else str(scheduled_time),
                    "notes": None
                }

                order_response = supabase.table("orders").insert(order_data).execute()
                order_id = order_response.data[0]["id"]
                order_number = order_response.data[0]["order_number"]

                # Insert Order Items
                for item in cart:
                    supabase.table("order_items").insert({
                        "order_id": order_id,
                        "item_id": item["id"],
                        "item_name": item["name"],
                        "item_price": item["price"],
                        "quantity": item["quantity"],
                        "subtotal": item["price"] * item["quantity"]
                    }).execute()

                # Clear cart
                st.session_state.cart = []
                st.session_state["last_order_number"] = order_number
                st.session_state["last_order_id"] = order_id

            st.success("Order placed successfully!")
            st.balloons()
            st.switch_page("pages/6_Order_Tracking.py")

        except Exception as e:
            st.error(f"Failed to place order: {e}")