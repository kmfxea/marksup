import streamlit as st
from utils.supabase_client import get_supabase
from datetime import datetime

st.set_page_config(
    page_title="Track Order • MarksUp",
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
    .step {
        display: flex;
        align-items: center;
        margin-bottom: 0.85rem;
        font-size: 1rem;
    }
    .step-done {
        color: #0a7a43;
        font-weight: 600;
    }
    .step-current {
        color: #FF6B00;
        font-weight: 700;
        font-size: 1.05rem;
    }
    .step-pending {
        color: #aaa;
    }
    .rider-card {
        background: #fff8f0;
        border: 1px solid #ffe0c2;
        border-radius: 14px;
        padding: 1.1rem;
        margin-top: 1rem;
    }
    .rating-box {
        background: #f8f9fa;
        border-radius: 14px;
        padding: 1.3rem;
        margin-top: 1.2rem;
        border: 1px solid #eee;
    }
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 2.7rem;
        font-weight: 600;
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Get Order
# --------------------------------------------------
order_id = st.session_state.get("last_order_id")

if not order_id:
    st.warning("No recent order found.")
    if st.button("Go to Home"):
        st.switch_page("app.py")
    st.stop()

@st.cache_data(ttl=8)
def get_order(order_id):
    supabase = get_supabase()
    response = supabase.table("orders")\
        .select("*, riders(full_name, contact_number, profile_picture_url, gcash_number, gcash_qr_url)")\
        .eq("id", order_id)\
        .single()\
        .execute()
    return response.data

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("### Track Your Order")

try:
    order = get_order(order_id)
except Exception as e:
    st.error("Unable to load order.")
    st.caption(str(e))
    st.stop()

st.markdown(f"**Order Number:** `{order['order_number']}`")
st.caption(f"Total: ₱{order['total_amount']:.2f}")

st.write("")

# --------------------------------------------------
# Status Steps
# --------------------------------------------------
status_list = [
    "Order Placed",
    "Confirmed",
    "Buying Items",
    "On the Way",
    "Delivered"
]

current_status = order["status"]

st.markdown("#### Order Status")

for i, status in enumerate(status_list):
    if current_status in status_list:
        current_index = status_list.index(current_status)
        if i < current_index:
            st.markdown(f"<div class='step step-done'>✅ {status}</div>", unsafe_allow_html=True)
        elif i == current_index:
            st.markdown(f"<div class='step step-current'>🟠 {status}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='step step-pending'>○ {status}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='step step-pending'>○ {status}</div>", unsafe_allow_html=True)

if current_status == "Cancelled":
    st.error("This order has been Cancelled.")
elif current_status == "Failed Delivery":
    st.error("Delivery Failed.")
elif current_status == "Under Review":
    st.warning("This order is Under Review.")

st.write("")

# --------------------------------------------------
# Rider Info
# --------------------------------------------------
rider = order.get("riders")

if rider:
    st.markdown("#### Your Rider")
    st.markdown(f"""
    <div class="rider-card">
        <strong>{rider['full_name']}</strong><br>
        📞 {rider['contact_number']}
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.link_button("📞 Call Rider", f"tel:{rider['contact_number']}")
    with c2:
        st.link_button("💬 Message", f"sms:{rider['contact_number']}")

    if order["payment_method"] == "GCash" and current_status not in ["Delivered", "Cancelled"]:
        st.write("")
        st.markdown("#### GCash Payment")
        st.write(f"**Number:** `{rider['gcash_number']}`")
        if rider.get("gcash_qr_url"):
            st.image(rider["gcash_qr_url"], width=180, caption="Scan to Pay")

# --------------------------------------------------
# POST-DELIVERY RATING
# --------------------------------------------------
if current_status == "Delivered":
    st.write("")
    st.markdown("#### Rate Your Experience")

    if order.get("rating"):
        st.success(f"You rated this order {order['rating']} ⭐")
        if order.get("review"):
            st.caption(f"“{order['review']}”")
    else:
        st.markdown("""
        <div class="rating-box">
            How was your experience with this order?
        </div>
        """, unsafe_allow_html=True)

        rating = st.slider("Rating", min_value=1, max_value=5, value=5, format="%d ⭐")
        review = st.text_area("Comment (optional)", placeholder="Mabilis at maganda ang serbisyo...")

        if st.button("Submit Rating"):
            try:
                supabase = get_supabase()
                supabase.table("orders").update({
                    "rating": rating,
                    "review": review,
                    "rated_at": datetime.now().isoformat()
                }).eq("id", order_id).execute()

                st.success("Thank you for your rating!")
                st.balloons()
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to submit rating: {e}")

# --------------------------------------------------
# Actions
# --------------------------------------------------
st.write("")
if st.button("🔄 Refresh Status"):
    st.cache_data.clear()
    st.rerun()

if st.button("Back to Home"):
    st.switch_page("app.py")