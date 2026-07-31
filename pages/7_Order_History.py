import streamlit as st
from utils.supabase_client import get_supabase

st.set_page_config(
    page_title="Order History • MarksUp",
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
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 0.4rem;
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
# Header
# --------------------------------------------------
st.markdown("### My Orders")
st.caption("View your past and current orders")

if st.button("← Back to Home"):
    st.switch_page("app.py")

st.write("")

# --------------------------------------------------
# Contact Number Lookup
# --------------------------------------------------
st.markdown("#### Find Your Orders")
contact = st.text_input("Enter your Contact Number", placeholder="09XXXXXXXXX")

if st.button("Search Orders"):
    if not contact:
        st.error("Please enter your contact number.")
    else:
        st.session_state["history_contact"] = contact

# --------------------------------------------------
# Fetch Orders
# --------------------------------------------------
contact_number = st.session_state.get("history_contact")

if contact_number:
    try:
        supabase = get_supabase()
        orders = supabase.table("orders")\
            .select("id, order_number, status, total_amount, created_at, store_id, stores(name)")\
            .eq("customer_contact", contact_number)\
            .order("created_at", desc=True)\
            .execute().data

        st.write("")
        st.markdown(f"**Orders for:** `{contact_number}`")

        if not orders:
            st.info("No orders found for this number.")
        else:
            for order in orders:
                store_name = order["stores"]["name"] if order.get("stores") else "Store"
                created = order["created_at"][:16].replace("T", " ")
                status = order["status"]

                # Status color
                if status == "Delivered":
                    badge_color = "#e6f9f0"
                    text_color = "#0a7a43"
                elif status in ["Cancelled", "Failed Delivery"]:
                    badge_color = "#fdecea"
                    text_color = "#c0392b"
                else:
                    badge_color = "#fff4e6"
                    text_color = "#e67e22"

                st.markdown(f"""
                <div class="order-card">
                    <div class="order-number">{order['order_number']}</div>
                    <div class="order-meta">
                        🏪 {store_name}<br>
                        📅 {created}<br>
                        ₱{order['total_amount']:.2f}
                    </div>
                    <div class="status-badge" style="background:{badge_color}; color:{text_color};">
                        {status}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns(2)

                with c1:
                    if st.button("Track", key=f"track_{order['id']}"):
                        st.session_state["last_order_id"] = order["id"]
                        st.switch_page("pages/6_Order_Tracking.py")

                with c2:
                    if status == "Delivered":
                        if st.button("Order Again", key=f"again_{order['id']}"):
                            try:
                                # 1. Get order items
                                items = supabase.table("order_items")\
                                    .select("*")\
                                    .eq("order_id", order["id"])\
                                    .execute().data

                                if not items:
                                    st.error("No items found in this order.")
                                else:
                                    # 2. Rebuild cart
                                    new_cart = []
                                    for item in items:
                                        new_cart.append({
                                            "id": item["item_id"],
                                            "name": item["item_name"],
                                            "price": float(item["item_price"]),
                                            "quantity": item["quantity"],
                                            "image_url": None
                                        })

                                    # 3. Set session state
                                    st.session_state.cart = new_cart
                                    st.session_state["selected_store_id"] = order["store_id"]
                                    st.session_state["selected_store_name"] = store_name

                                    st.success("Items added to cart!")
                                    st.switch_page("pages/4_Cart.py")

                            except Exception as e:
                                st.error(f"Failed to load order items: {e}")

                st.markdown("---")

    except Exception as e:
        st.error(f"Failed to load orders: {e}")
else:
    st.info("Enter your contact number to view your order history.")