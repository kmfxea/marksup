import streamlit as st
from utils.supabase_client import get_supabase
import uuid

st.set_page_config(
    page_title="Order Details • MarksUp",
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

rider_id = st.session_state["user"].get("rider_id")
order_id = st.session_state.get("selected_order_id")

if not order_id:
    st.warning("No order selected.")
    if st.button("← Back to Dashboard"):
        st.switch_page("pages/11_Rider_Dashboard.py")
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
    .address-box {
        background: #fff8f0;
        border: 1px solid #ffe0c2;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.8rem 0;
        font-size: 1.05rem;
        font-weight: 600;
    }
    .info-box {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        border: 1px solid #eee;
    }
    .msg-rider {
        background: #e3f2fd;
        padding: 0.7rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
        text-align: right;
    }
    .msg-customer {
        background: #f1f1f1;
        padding: 0.7rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
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
# Fetch Order
# --------------------------------------------------
supabase = get_supabase()

try:
    order = supabase.table("orders")\
        .select("*, stores(name), order_items(*)")\
        .eq("id", order_id)\
        .single()\
        .execute().data
except Exception as e:
    st.error(f"Failed to load order: {e}")
    st.stop()

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown(f"### {order['order_number']}")
st.caption(f"Status: **{order['status']}**")

if st.button("← Back to Dashboard"):
    st.switch_page("pages/11_Rider_Dashboard.py")

st.write("")

# --------------------------------------------------
# Customer & Address
# --------------------------------------------------
st.markdown("#### Delivery Details")

st.markdown(f"""
<div class="address-box">
    📍 {order['delivery_address']}
</div>
""", unsafe_allow_html=True)

if order.get("landmark"):
    st.caption(f"Landmark: {order['landmark']}")

st.write(f"**Customer:** {order['customer_name']}")
st.write(f"**Contact:** {order['customer_contact']}")

col1, col2 = st.columns(2)
with col1:
    st.link_button("📞 Call", f"tel:{order['customer_contact']}")
with col2:
    st.link_button("💬 SMS", f"sms:{order['customer_contact']}")

st.write("")

maps_url = f"https://www.google.com/maps/search/?api=1&query={order['delivery_address'].replace(' ', '+')}"
st.link_button("🗺️ Open in Google Maps", maps_url)

st.write("")

# --------------------------------------------------
# Store & Items
# --------------------------------------------------
store_name = order["stores"]["name"] if order.get("stores") else "Store"
st.markdown(f"#### Store: {store_name}")

items = order.get("order_items", [])
if items:
    for item in items:
        st.write(f"• {item['quantity']}× {item['item_name']} — ₱{item['subtotal']:.2f}")
else:
    st.caption("No items found.")

st.write("")

# --------------------------------------------------
# Fees Summary
# --------------------------------------------------
st.markdown("#### Fees")

st.markdown(f"""
<div class="info-box">
    Items Total: ₱{order['items_total']:.2f}<br>
    Delivery Fee: ₱{order['delivery_fee']:.2f}<br>
    Floor Fee: ₱{order['floor_fee']:.2f}<br>
    Handling Fee: ₱{order['handling_fee']:.2f}<br>
    <strong>Total to Collect: ₱{order['total_amount']:.2f}</strong><br>
    Payment: {order['payment_method']}
</div>
""", unsafe_allow_html=True)

if order["items_total"] > 100:
    st.warning("⚠️ High value order (above ₱100). Confirm GCash payment first before buying.")

st.write("")

# --------------------------------------------------
# In-App Messaging (Rider ↔ Customer)
# --------------------------------------------------
st.markdown("#### Message Customer")

try:
    messages = supabase.table("messages")\
        .select("*")\
        .eq("order_id", order_id)\
        .order("created_at")\
        .execute().data

    if messages:
        for msg in messages:
            if msg["sender_type"] == "rider":
                st.markdown(f"""
                <div class="msg-rider">
                    <small>You</small><br>
                    {msg['message']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-customer">
                    <small>Customer</small><br>
                    {msg['message']}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.caption("No messages yet.")

    new_msg = st.text_input("Type a message", key="rider_msg", placeholder="Type your message...")
    if st.button("Send Message", key="rider_send"):
        if new_msg.strip():
            supabase.table("messages").insert({
                "order_id": order_id,
                "sender_type": "rider",
                "sender_name": st.session_state["user"].get("full_name", "Rider"),
                "receiver_type": "customer",
                "message": new_msg.strip()
            }).execute()
            st.success("Message sent!")
            st.rerun()
        else:
            st.warning("Please type a message.")
except Exception as e:
    st.error(f"Messaging error: {e}")

st.write("")

# --------------------------------------------------
# Actions based on Status
# --------------------------------------------------
status = order["status"]

if status == "Order Placed" and order.get("rider_id") is None:
    st.markdown("#### Actions")
    c1, c2 = st.columns(2)

    with c1:
        if st.button("✅ Accept Order"):
            try:
                rider = supabase.table("riders").select("wallet_balance").eq("id", rider_id).single().execute().data
                if rider["wallet_balance"] < -50:
                    st.error("Your wallet balance is too low. Please top up first.")
                else:
                    supabase.table("orders").update({
                        "rider_id": rider_id,
                        "status": "Confirmed"
                    }).eq("id", order_id).execute()

                    supabase.table("riders").update({"is_busy": True}).eq("id", rider_id).execute()
                    st.success("Order accepted!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with c2:
        if st.button("❌ Reject"):
            st.info("Order skipped.")
            st.switch_page("pages/11_Rider_Dashboard.py")

elif order.get("rider_id") == rider_id:
    st.markdown("#### Update Status")

    if status == "Confirmed":
        if st.button("🛒 Start Buying Items"):
            supabase.table("orders").update({"status": "Buying Items"}).eq("id", order_id).execute()
            st.rerun()

    elif status == "Buying Items":
        if st.button("🛵 On the Way"):
            supabase.table("orders").update({"status": "On the Way"}).eq("id", order_id).execute()
            st.rerun()

    elif status == "On the Way":
        st.write("**Proof of Delivery (Required)**")
        proof_file = st.file_uploader("Upload photo of delivered items", type=["png", "jpg", "jpeg"])

        if st.button("✅ Mark as Delivered"):
            if proof_file is None:
                st.error("Proof of Delivery photo is required.")
            else:
                try:
                    file_ext = proof_file.name.split(".")[-1]
                    file_name = f"proof_{uuid.uuid4()}.{file_ext}"

                    supabase.storage.from_("item-photos").upload(
                        file_name,
                        proof_file.getvalue(),
                        {"content-type": proof_file.type}
                    )
                    proof_url = supabase.storage.from_("item-photos").get_public_url(file_name)

                    service_fees = (order["delivery_fee"] or 0) + (order["floor_fee"] or 0) + (order["handling_fee"] or 0)
                    commission = round(service_fees * 0.05, 2)

                    supabase.table("orders").update({
                        "status": "Delivered",
                        "proof_of_delivery_url": proof_url,
                        "commission_amount": commission
                    }).eq("id", order_id).execute()

                    rider = supabase.table("riders").select("wallet_balance").eq("id", rider_id).single().execute().data
                    new_balance = float(rider["wallet_balance"]) - commission

                    supabase.table("riders").update({
                        "wallet_balance": new_balance,
                        "is_busy": False
                    }).eq("id", rider_id).execute()

                    supabase.table("wallet_transactions").insert({
                        "rider_id": rider_id,
                        "type": "commission",
                        "amount": -commission,
                        "balance_after": new_balance,
                        "order_id": order_id,
                        "notes": f"Commission for {order['order_number']}"
                    }).execute()

                    st.success("Order marked as Delivered!")
                    st.balloons()
                    st.switch_page("pages/11_Rider_Dashboard.py")
                except Exception as e:
                    st.error(f"Error: {e}")

else:
    st.info("This order is already assigned to another rider.")