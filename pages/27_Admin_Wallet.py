import streamlit as st
from utils.supabase_client import get_supabase

st.set_page_config(
    page_title="Wallet Top-up • MarksUp",
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
        max-width: 500px;
        margin: auto;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1a1a2e !important;
    }
    .balance-card {
        background: #fff8f0;
        border: 1px solid #ffe0c2;
        border-radius: 14px;
        padding: 1.3rem;
        text-align: center;
        margin-bottom: 1.2rem;
    }
    .balance-amount {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FF6B00;
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

st.title("Wallet Top-up")

if st.button("← Back to Dashboard"):
    st.switch_page("pages/21_Admin_Dashboard.py")

st.write("")

# --------------------------------------------------
# Select Rider
# --------------------------------------------------
supabase = get_supabase()

riders = supabase.table("riders")\
    .select("id, full_name, wallet_balance, contact_number")\
    .eq("is_active", True)\
    .order("full_name")\
    .execute().data

if not riders:
    st.warning("No active riders found.")
    st.stop()

rider_options = {f"{r['full_name']} (₱{r['wallet_balance']:.2f})": r for r in riders}
selected_label = st.selectbox("Select Rider", list(rider_options.keys()))
selected_rider = rider_options[selected_label]

st.write("")

# --------------------------------------------------
# Current Balance
# --------------------------------------------------
st.markdown(f"""
<div class="balance-card">
    <div style="font-size:0.95rem; color:#666;">Current Wallet Balance</div>
    <div class="balance-amount">₱{selected_rider['wallet_balance']:.2f}</div>
    <div style="font-size:0.9rem; color:#666; margin-top:0.3rem;">{selected_rider['full_name']}</div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Top-up Form
# --------------------------------------------------
st.subheader("Top-up Amount")

amount = st.number_input(
    "Amount to Top-up (₱)",
    min_value=10.0,
    value=100.0,
    step=10.0
)

notes = st.text_input("Notes (optional)", placeholder="e.g. Cash received, GCash transfer, etc.")

st.write("")

if st.button("Confirm Top-up"):
    if amount < 10:
        st.error("Minimum top-up is ₱10.")
    else:
        try:
            with st.spinner("Processing top-up..."):
                new_balance = float(selected_rider["wallet_balance"]) + amount

                # Update rider wallet
                supabase.table("riders").update({
                    "wallet_balance": new_balance
                }).eq("id", selected_rider["id"]).execute()

                # Record transaction
                supabase.table("wallet_transactions").insert({
                    "rider_id": selected_rider["id"],
                    "type": "topup",
                    "amount": amount,
                    "balance_after": new_balance,
                    "notes": notes or "Admin top-up",
                    "created_by": st.session_state["user"].get("full_name", "Admin")
                }).execute()

            st.success(f"Successfully topped up ₱{amount:.2f} to {selected_rider['full_name']}!")
            st.balloons()
            st.rerun()

        except Exception as e:
            st.error(f"Top-up failed: {e}")

st.write("")

# --------------------------------------------------
# Recent Transactions
# --------------------------------------------------
st.subheader("Recent Top-ups")

try:
    transactions = supabase.table("wallet_transactions")\
        .select("*, riders(full_name)")\
        .eq("type", "topup")\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute().data

    if not transactions:
        st.info("No top-up transactions yet.")
    else:
        for tx in transactions:
            rider_name = tx["riders"]["full_name"] if tx.get("riders") else "Unknown"
            created = tx["created_at"][:16].replace("T", " ")

            st.markdown(f"""
            **{rider_name}** — +₱{tx['amount']:.2f}  
            Balance after: ₱{tx['balance_after']:.2f}  
            {created}  
            {tx.get('notes') or ''}
            """)
            st.markdown("---")

except Exception as e:
    st.error(f"Failed to load transactions: {e}")