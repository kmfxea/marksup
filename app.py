import streamlit as st
from utils.supabase_client import get_supabase

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="MarksUp",
    page_icon="🛵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# PWA Meta Tags
# --------------------------------------------------
st.markdown("""
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#FF6B00">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="MarksUp">
<link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/2972/2972186.png">
<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(reg => console.log('SW registered'))
    .catch(err => console.log('SW failed', err));
}
</script>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Advanced CSS
# --------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        max-width: 430px;
        margin: auto;
        padding: 1.2rem 1rem 2rem 1rem;
        background: #fafafa;
    }

    /* Tablet */
    @media (min-width: 768px) {
        .stApp {
            max-width: 600px;
        }
    }

    /* Laptop */
    @media (min-width: 1024px) {
        .stApp {
            max-width: 720px;
        }
    }

    /* Header */
    .header {
        text-align: center;
        margin-bottom: 1.8rem;
        padding-top: 0.5rem;
    }
    .logo-text {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1a1a2e;
        letter-spacing: -0.5px;
        margin-bottom: 0.15rem;
    }
    .tagline {
        font-size: 0.95rem;
        color: #888;
        font-weight: 400;
    }

    /* Status Card */
    .status-card {
        border-radius: 16px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1.8rem;
        font-size: 0.95rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.7rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .available {
        background: linear-gradient(135deg, #e8faf0, #d1f5e0);
        color: #0a7a43;
        border: 1px solid #b6e9cc;
    }
    .unavailable {
        background: linear-gradient(135deg, #fdecea, #fce4e2);
        color: #c0392b;
        border: 1px solid #f5c6cb;
    }

    /* Main CTA Button - Orange */
    .stButton > button {
        width: 100%;
        border-radius: 14px;
        height: 3.4rem;
        font-size: 1.1rem;
        font-weight: 600;
        border: none;
        background-color: #FF6B00 !important;
        color: white !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255,107,0,0.25);
        background-color: #e65c00 !important;
        color: white !important;
    }

    /* Secondary Buttons */
    div[data-testid="column"] .stButton > button {
        height: 3rem;
        font-size: 0.95rem;
        background: white !important;
        color: #1a1a2e !important;
        border: 1px solid #e5e5e5 !important;
    }
    div[data-testid="column"] .stButton > button:hover {
        background: #f5f5f5 !important;
        box-shadow: none !important;
        transform: none !important;
    }

    /* Footer */
    .footer {
        text-align: center;
        margin-top: 2.5rem;
        padding-top: 1.2rem;
        border-top: 1px solid #eee;
        font-size: 0.8rem;
        color: #aaa;
    }

    /* Hide Streamlit Branding */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("""
<div class="header">
    <div class="logo-text">MarksUp</div>
    <div class="tagline">Your everyday assistant</div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Rider Availability
# --------------------------------------------------
try:
    supabase = get_supabase()
    response = supabase.table("riders")\
        .select("id")\
        .eq("is_active", True)\
        .eq("is_online", True)\
        .eq("is_busy", False)\
        .gte("wallet_balance", -50)\
        .execute()

    available_riders = response.data

    if available_riders and len(available_riders) > 0:
        st.markdown("""
        <div class="status-card available">
            🟢 &nbsp; Rider Available — You can place an order
        </div>
        """, unsafe_allow_html=True)
        rider_available = True
    else:
        st.markdown("""
        <div class="status-card unavailable">
            🔴 &nbsp; No Rider Available right now
        </div>
        """, unsafe_allow_html=True)
        rider_available = False

except Exception as e:
    st.warning("Unable to check rider availability.")
    rider_available = False

# --------------------------------------------------
# Main CTA
# --------------------------------------------------
if st.button("🛒  Mag-Pabili Ngayon", use_container_width=True):
    if rider_available:
        st.switch_page("pages/2_Stores.py")
    else:
        st.error("Walang available na rider ngayon. Subukan ulit mamaya.")

st.write("")

# --------------------------------------------------
# Secondary Actions
# --------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("📋  My Orders", use_container_width=True):
        st.switch_page("pages/7_Order_History.py")

with col2:
    if st.button("ℹ️  About", use_container_width=True):
        st.info(
            "**MarksUp – Your everyday assistant**\n\n"
            "MarksUp helps you with everyday errands in Fairview — especially **Pabili**.\n\n"
            "Just choose a store, select your items, and we’ll handle the rest.  \n"
            "A rider will buy and deliver them straight to your door.\n\n"
            "**What we offer:**\n"
            "- Pabili from local stores\n"
            "- Fast delivery within Fairview\n"
            "- Cash or GCash payment\n"
            "- Real-time order tracking\n\n"
            "**Service Hours:**  \n"
            "7:00 AM – 9:00 PM daily\n\n"
            "**Simple. Reliable. Local.**"
        )

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.markdown("""
<div class="footer">
    MarksUp • Fairview<br>
    7:00 AM – 9:00 PM
</div>
""", unsafe_allow_html=True)

st.write("")
if st.button("🔒 Rider / Admin Login", use_container_width=True):
    st.switch_page("pages/10_Login.py")