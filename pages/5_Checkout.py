import streamlit as st
from utils.supabase_client import get_supabase
from utils.helpers import haversine_km, delivery_fee_from_km

try:
    from streamlit_js_eval import get_geolocation
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

st.set_page_config(
    page_title="Checkout • MarksUp",
    page_icon="🛵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { max-width: 500px; margin: auto; padding-bottom: 2rem; }
    h1, h2, h3 { color: #1a1a2e !important; }
    .summary-box {
        background: #f8f9fa;
        border-radius: 14px;
        padding: 1.2rem;
        margin-top: 1rem;
        border: 1px solid #eee;
    }
    .distance-box {
        background: #fff8f0;
        border: 1px solid #ffe0c2;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin: 0.8rem 0;
        font-weight: 600;
    }
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3rem;
        font-weight: 600;
        background-color: #FF6B00 !important;
        color: white !important;
        border: none !important;
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Validate
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

supabase = get_supabase()
store = None
try:
    store = supabase.table("stores")\
        .select("id, name, address, latitude, longitude")\
        .eq("id", store_id)\
        .single()\
        .execute().data
except Exception:
    pass

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

# --------------------------------------------------
# GPS One-Tap (Primary)
# --------------------------------------------------
st.subheader("Your Location")
st.caption("Para makalkula ang distance at delivery fee.")

if "customer_lat" not in st.session_state:
    st.session_state.customer_lat = None
if "customer_lng" not in st.session_state:
    st.session_state.customer_lng = None

if HAS_GEO:
    if st.button("📍 Use my current location", use_container_width=True):
        with st.spinner("Getting your location..."):
            loc = get_geolocation()
            if loc and loc.get("coords"):
                st.session_state.customer_lat = loc["coords"]["latitude"]
                st.session_state.customer_lng = loc["coords"]["longitude"]
                st.success("Location detected!")
                st.rerun()
            else:
                st.warning("Could not get location. Please allow location access or use manual fallback.")
else:
    st.info("GPS helper not installed yet. Using manual fallback.")

# Show current detected location
customer_lat = st.session_state.get("customer_lat")
customer_lng = st.session_state.get("customer_lng")

if customer_lat and customer_lng:
    st.success(f"📍 Location set: {customer_lat:.5f}, {customer_lng:.5f}")
else:
    st.caption("No location yet. Tap the button above (recommended).")

# Manual fallback (collapsed)
with st.expander("Manual location (only if GPS fails)"):
    m_lat = st.number_input("Latitude", value=float(customer_lat or 14.7000), format="%.6f", key="manual_lat")
    m_lng = st.number_input("Longitude", value=float(customer_lng or 121.0700), format="%.6f", key="manual_lng")
    if st.button("Use manual coordinates"):
        st.session_state.customer_lat = m_lat
        st.session_state.customer_lng = m_lng
        st.success("Manual location saved.")
        st.rerun()

# --------------------------------------------------
# Distance + Fee
# --------------------------------------------------
distance_km = None
delivery_fee = 25.0

if store and store.get("latitude") and store.get("longitude") and customer_lat and customer_lng:
    distance_km = haversine_km(
        store["latitude"], store["longitude"],
        customer_lat, customer_lng
    )
    delivery_fee = delivery_fee_from_km(distance_km)

    st.markdown(f"""
    <div class="distance-box">
        📍 {store_name}<br>
        About <b>{distance_km} km</b> from your location<br>
        Delivery fee: <b>₱{delivery_fee:.0f}</b>
    </div>
    """, unsafe_allow_html=True)
elif not (customer_lat and customer_lng):
    st.info("Set your location to see distance and exact delivery fee. Default fee ₱25 if skipped.")
else:
    st.info("Store has no coordinates yet. Default delivery fee ₱25.")

st.write("")

# Preferred Time
preferred_time = st.radio("Preferred Time", ["ASAP", "Schedule for later"], horizontal=True)
scheduled_time = None
if preferred_time == "Schedule for later":
    scheduled_time = st.time_input("Select time")

st.write("")

# Extra fees
st.subheader("Additional Options")
needs_floor = st.checkbox("Deliver to 2nd floor or higher? (+₱15 Floor Fee)")
is_heavy = st.checkbox("Heavy / Grocery order? (+₱50 Handling Fee)")

st.write("")

# Payment
st.subheader("Payment Method")
payment_method = st.radio("Choose payment method", ["Cash", "GCash"], horizontal=True)
if payment_method == "GCash":
    st.info("After a rider accepts, you will see the rider’s GCash number and QR.")

st.write("")

# --------------------------------------------------
# Summary
# --------------------------------------------------
subtotal = sum(item["price"] * item["quantity"] for item in cart)
floor_fee = 15.0 if needs_floor else 0.0
handling_fee = 50.0 if is_heavy else 0.0
total = subtotal + delivery_fee + floor_fee + handling_fee

custom_notes = []
for item in cart:
    if item.get("notes"):
        custom_notes.append(f"{item['name']}:\n{item['notes']}")
notes_combined = "\n\n".join(custom_notes) if custom_notes else None

st.markdown("### Order Summary")
st.markdown(f"""
<div class="summary-box">
    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
        <span>Store</span><span>{store_name}</span>
    </div>
    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
        <span>Distance</span><span>{f'{distance_km} km' if distance_km is not None else 'N/A'}</span>
    </div>
    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
        <span>Subtotal</span><span>₱{subtotal:.2f}</span>
    </div>
    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
        <span>Delivery Fee</span><span>₱{delivery_fee:.2f}</span>
    </div>
    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
        <span>Floor Fee</span><span>₱{floor_fee:.2f}</span>
    </div>
    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
        <span>Handling Fee</span><span>₱{handling_fee:.2f}</span>
    </div>
    <hr style="margin: 0.6rem 0;">
    <div style="display:flex; justify-content:space-between; font-weight:700; font-size:1.15rem;">
        <span>Total</span><span>₱{total:.2f}</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.write("")

# --------------------------------------------------
# Place Order
# --------------------------------------------------
if st.button("Place Order"):
    if not customer_name or not customer_contact or not delivery_address:
        st.error("Please fill in Name, Contact Number, and Delivery Address.")
    else:
        try:
            with st.spinner("Placing your order..."):
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
                    "distance_km": distance_km,
                    "preferred_time": "ASAP" if preferred_time == "ASAP" else str(scheduled_time),
                    "notes": notes_combined
                }

                order_response = supabase.table("orders").insert(order_data).execute()
                order_id = order_response.data[0]["id"]
                order_number = order_response.data[0]["order_number"]

                for item in cart:
                    item_id = item["id"] if not str(item["id"]).startswith("custom_") else None
                    supabase.table("order_items").insert({
                        "order_id": order_id,
                        "item_id": item_id,
                        "item_name": item["name"],
                        "item_price": item["price"],
                        "quantity": item["quantity"],
                        "subtotal": item["price"] * item["quantity"]
                    }).execute()

                st.session_state.cart = []
                st.session_state["last_order_number"] = order_number
                st.session_state["last_order_id"] = order_id

            st.success("Order placed successfully!")
            st.balloons()
            st.switch_page("pages/6_Order_Tracking.py")
        except Exception as e:
            st.error(f"Failed to place order: {e}")