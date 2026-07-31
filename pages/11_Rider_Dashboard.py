import streamlit as st
from utils.supabase_client import get_supabase
from datetime import datetime, date

st.set_page_config(
    page_title="Rider Dashboard • MarksUp",
    page_icon="🛵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# Auth Check
# --------------------------------------------------
if "user" not in st.session_state or st.session_state["user"].get("role") != "rider":
    st.warning("Rider access only.")
    st.stop()

user = st.session_state["user"]
rider_id = user.get("rider_id")

if not rider_id:
    st.error("No rider profile linked to this account.")
    st.stop()

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
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #eee;
    }
    .order-card {
        background: #ffffff;
        border: 1px solid #eee;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .order-title {
        font-weight: 600;
        font-size: 1.05rem;
        color: #1a1a2e;
    }
    .order-meta {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.3rem;
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
# Fetch Rider Data
# --------------------------------------------------
supabase = get_supabase()

rider = supabase.table("riders").select("*").eq("id", rider_id).single().execute().data

if not rider:
    st.error("Rider record not found.")
    st.stop()

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown(f"### Hello, {rider['full_name']} 👋")
st.caption("Rider Dashboard")

# --------------------------------------------------
# Online / Offline Toggle
# --------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    status_label = "🟢 Online" if rider["is_online"] else "🔴 Offline"
    st.markdown(f"**Status:** {status_label}")

with col2:
    new_status = not rider["is_online"]
    button_label = "Go Online" if not rider["is_online"] else "Go Offline"
    
    if st.button(button_label):
        try:
            supabase.table("riders").update({
                "is_online": new_status
            }).eq("id", rider_id).execute()
            st.success(f"Status updated to {'Online' if new_status else 'Offline'}")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to update status: {e}")

# --------------------------------------------------
# Quick Stats
# --------------------------------------------------
today = str(date.today())

try:
    # Today's completed orders
    completed = supabase.table("orders")\
        .select("id, total_amount, delivery_fee, floor_fee, handling_fee")\
        .eq("rider_id", rider_id)\
        .eq("status", "Delivered")\
        .gte("created_at", today)\
        .execute().data

    today_earnings = sum(
        (o.get("delivery_fee") or 0) + (o.get("floor_fee") or 0) + (o.get("handling_fee") or 0)
        for o in completed
    )
    today_orders = len(completed)
except:
    today_earnings = 0
    today_orders = 0

c1, c2, c3 = st.columns(3)
c1.metric("Wallet", f"₱{rider['wallet_balance']:.2f}")
c2.metric("Today Orders", today_orders)
c3.metric("Today Earnings", f"₱{today_earnings:.2f}")

st.write("")

# --------------------------------------------------
# New Orders (Available to Accept)
# --------------------------------------------------
st.subheader("New Orders")

try:
    new_orders = supabase.table("orders")\
        .select("id, order_number, customer_name, delivery_address, total_amount, delivery_fee, floor_fee, handling_fee, created_at, stores(name)")\
        .eq("status", "Order Placed")\
        .is_("rider_id", "null")\
        .order("created_at", desc=True)\
        .execute().data

    if not new_orders:
        st.info("No new orders available right now.")
    else:
        for order in new_orders:
            store_name = order["stores"]["name"] if order.get("stores") else "Store"
            service_fee = (order.get("delivery_fee") or 0) + (order.get("floor_fee") or 0) + (order.get("handling_fee") or 0)

            st.markdown(f"""
            <div class="order-card">
                <div class="order-title">{order['order_number']}</div>
                <div class="order-meta">
                    📍 {order['delivery_address'][:50]}{'...' if len(order['delivery_address']) > 50 else ''}<br>
                    🏪 {store_name} • ₱{service_fee:.2f} fee
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("View & Accept", key=f"view_{order['id']}"):
                st.session_state["selected_order_id"] = order["id"]
                st.switch_page("pages/12_Rider_Order_Details.py")

except Exception as e:
    st.error(f"Failed to load new orders: {e}")

st.write("")

# --------------------------------------------------
# My Active Orders
# --------------------------------------------------
st.subheader("My Active Orders")

try:
    active_orders = supabase.table("orders")\
        .select("id, order_number, status, delivery_address, total_amount")\
        .eq("rider_id", rider_id)\
        .in_("status", ["Confirmed", "Buying Items", "On the Way"])\
        .order("created_at", desc=True)\
        .execute().data

    if not active_orders:
        st.info("No active orders.")
    else:
        for order in active_orders:
            st.markdown(f"""
            <div class="order-card">
                <div class="order-title">{order['order_number']} • {order['status']}</div>
                <div class="order-meta">📍 {order['delivery_address'][:55]}...</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Open Order", key=f"active_{order['id']}"):
                st.session_state["selected_order_id"] = order["id"]
                st.switch_page("pages/12_Rider_Order_Details.py")

except Exception as e:
    st.error(f"Failed to load active orders: {e}")

st.write("")

# --------------------------------------------------
# Logout
# --------------------------------------------------
if st.button("🔒 Logout"):
    st.session_state.clear()
    st.switch_page("app.py")
# --------------------------------------------------
# Auto Refresh every 10 seconds
# --------------------------------------------------
st.markdown("""
<meta http-equiv="refresh" content="10">
""", unsafe_allow_html=True)

st.caption("🔄 Auto-refreshes every 10 seconds for new orders")