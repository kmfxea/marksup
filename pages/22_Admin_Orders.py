import streamlit as st
from utils.supabase_client import get_supabase

st.set_page_config(
    page_title="Manage Orders • MarksUp",
    page_icon="🛵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# Auth Check
# --------------------------------------------------
if "user" not in st.session_state or st.session_state["user"].get("role") != "admin":
    st.warning("Admin access only.")
    st.stop()

# --------------------------------------------------
# CSS
# --------------------------------------------------
st.markdown("""
<style>
    .stApp {
        max-width: 520px;
        margin: auto;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1a1a2e !important;
    }
    .order-card {
        background: #ffffff;
        border: 1px solid #eee;
        border-radius: 14px;
        padding: 1.1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .order-number {
        font-weight: 700;
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
        height: 2.5rem;
        font-weight: 600;
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("Manage Orders")

if st.button("← Back to Dashboard"):
    st.switch_page("pages/21_Admin_Dashboard.py")

st.write("")

# --------------------------------------------------
# Filters
# --------------------------------------------------
status_filter = st.selectbox(
    "Filter by Status",
    [
        "All",
        "Order Placed",
        "Confirmed",
        "Buying Items",
        "On the Way",
        "Delivered",
        "Cancelled",
        "Failed Delivery",
        "Under Review"
    ]
)

search = st.text_input("Search Order Number or Customer Name")

st.write("")

# --------------------------------------------------
# Fetch Orders
# --------------------------------------------------
try:
    supabase = get_supabase()

    query = supabase.table("orders")\
        .select("id, order_number, customer_name, customer_contact, delivery_address, status, total_amount, payment_method, created_at, rider_id, stores(name), riders(full_name)")\
        .order("created_at", desc=True)\
        .limit(50)

    if status_filter != "All":
        query = query.eq("status", status_filter)

    orders = query.execute().data

    # Client-side search
    if search:
        search = search.lower()
        orders = [
            o for o in orders
            if search in (o.get("order_number") or "").lower()
            or search in (o.get("customer_name") or "").lower()
        ]

    if not orders:
        st.info("No orders found.")
    else:
        st.caption(f"Showing {len(orders)} orders")

        for order in orders:
            store_name = order["stores"]["name"] if order.get("stores") else "N/A"
            rider_name = order["riders"]["full_name"] if order.get("riders") else "Unassigned"
            created = order["created_at"][:16].replace("T", " ")

            st.markdown(f"""
            <div class="order-card">
                <div class="order-number">{order['order_number']}</div>
                <div class="order-meta">
                    👤 {order['customer_name']} • {order['customer_contact']}<br>
                    🏪 {store_name}<br>
                    🛵 {rider_name}<br>
                    📅 {created}<br>
                    💰 ₱{order['total_amount']:.2f} • {order['payment_method']}<br>
                    <strong>Status: {order['status']}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Actions
            with st.expander("Manage this order"):
                new_status = st.selectbox(
                    "Update Status",
                    [
                        "Order Placed",
                        "Confirmed",
                        "Buying Items",
                        "On the Way",
                        "Delivered",
                        "Cancelled",
                        "Failed Delivery",
                        "Under Review"
                    ],
                    index=[
                        "Order Placed", "Confirmed", "Buying Items", "On the Way",
                        "Delivered", "Cancelled", "Failed Delivery", "Under Review"
                    ].index(order["status"]) if order["status"] in [
                        "Order Placed", "Confirmed", "Buying Items", "On the Way",
                        "Delivered", "Cancelled", "Failed Delivery", "Under Review"
                    ] else 0,
                    key=f"status_{order['id']}"
                )

                # Load riders for assignment
                riders = supabase.table("riders").select("id, full_name").eq("is_active", True).execute().data
                rider_options = {"Unassigned": None}
                rider_options.update({r["full_name"]: r["id"] for r in riders})

                current_rider = "Unassigned"
                if order.get("riders"):
                    current_rider = order["riders"]["full_name"]

                selected_rider_name = st.selectbox(
                    "Assign Rider",
                    list(rider_options.keys()),
                    index=list(rider_options.keys()).index(current_rider) if current_rider in rider_options else 0,
                    key=f"rider_{order['id']}"
                )

                if st.button("Save Changes", key=f"save_{order['id']}"):
                    update_data = {
                        "status": new_status,
                        "rider_id": rider_options[selected_rider_name]
                    }
                    supabase.table("orders").update(update_data).eq("id", order["id"]).execute()
                    st.success("Order updated!")
                    st.rerun()

                st.write("")
                st.write(f"**Address:** {order['delivery_address']}")
                st.link_button("📞 Call Customer", f"tel:{order['customer_contact']}")

            st.markdown("---")

except Exception as e:
    st.error(f"Failed to load orders: {e}")