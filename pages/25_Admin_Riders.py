import streamlit as st
from utils.supabase_client import get_supabase
from supabase import create_client
import uuid

st.set_page_config(
    page_title="Manage Riders • MarksUp",
    page_icon="🛵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

if "user" not in st.session_state or st.session_state["user"].get("role") != "admin":
    st.warning("Admin access only.")
    st.stop()

st.markdown("""
<style>
    .stApp { max-width: 520px; margin: auto; }
    .stButton > button { 
        width: 100%; 
        border-radius: 10px; 
        height: 2.6rem; 
        font-weight: 600; 
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("Manage Riders")

if st.button("← Back to Dashboard"):
    st.switch_page("pages/21_Admin_Dashboard.py")

st.write("")

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def get_admin_supabase():
    """Client with service_role key for admin actions"""
    url = st.secrets["supabase"]["url"]
    service_key = st.secrets["supabase"]["service_role_key"]
    return create_client(url, service_key)

def upload_file(file, bucket_name: str):
    if file is None:
        return None

    supabase = get_supabase()
    file_ext = file.name.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"

    supabase.storage.from_(bucket_name).upload(
        file_name,
        file.getvalue(),
        {"content-type": file.type}
    )

    return supabase.storage.from_(bucket_name).get_public_url(file_name)

# --------------------------------------------------
# 1. ADD NEW RIDER
# --------------------------------------------------
with st.expander("➕ Add New Rider", expanded=True):
    full_name = st.text_input("Full Name*")
    contact_number = st.text_input("Contact Number*")
    gcash_number = st.text_input("GCash Number*")
    bio = st.text_area("Short Bio*")
    wallet_balance = st.number_input("Initial Wallet Balance", value=0.0)

    st.write("**Profile Picture***")
    profile_pic_file = st.file_uploader(
        "Upload Profile Picture", 
        type=["png", "jpg", "jpeg", "webp"], 
        key="profile_pic"
    )

    st.write("**GCash QR Code***")
    gcash_qr_file = st.file_uploader(
        "Upload GCash QR Code", 
        type=["png", "jpg", "jpeg", "webp"], 
        key="gcash_qr"
    )

    if st.button("Save Rider"):
        if not all([full_name, contact_number, gcash_number, bio]):
            st.error("Please fill in all required fields.")
        elif profile_pic_file is None or gcash_qr_file is None:
            st.error("Profile Picture and GCash QR Code are required.")
        else:
            try:
                with st.spinner("Saving rider..."):
                    profile_picture_url = upload_file(profile_pic_file, "rider-photos")
                    gcash_qr_url = upload_file(gcash_qr_file, "gcash-qr")

                    supabase = get_supabase()
                    supabase.table("riders").insert({
                        "full_name": full_name,
                        "contact_number": contact_number,
                        "gcash_number": gcash_number,
                        "gcash_qr_url": gcash_qr_url,
                        "profile_picture_url": profile_picture_url,
                        "bio": bio,
                        "wallet_balance": wallet_balance,
                        "is_active": True,
                        "is_online": False,
                        "is_busy": False
                    }).execute()

                st.success(f"Rider '{full_name}' added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

st.write("")

# --------------------------------------------------
# 2. CREATE LOGIN FOR RIDER
# --------------------------------------------------
with st.expander("🔐 Create Login for Rider", expanded=False):
    st.info("Select a rider who still has no login, then create an account for them.")

    try:
        supabase = get_supabase()
        riders = supabase.table("riders").select("id, full_name, contact_number").order("full_name").execute().data

        if not riders:
            st.warning("No riders available.")
        else:
            rider_options = {f"{r['full_name']}": r for r in riders}
            selected_name = st.selectbox("Select Rider", list(rider_options.keys()))
            selected_rider = rider_options[selected_name]

            login_email = st.text_input("Email for Login*")
            login_password = st.text_input("Password for Login*", type="password")

            if st.button("Create Login Account"):
                if not login_email or not login_password:
                    st.error("Email and Password are required.")
                elif len(login_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        with st.spinner("Creating login account..."):
                            admin_supabase = get_admin_supabase()

                            # 1. Create Auth user
                            auth_response = admin_supabase.auth.admin.create_user({
                                "email": login_email,
                                "password": login_password,
                                "email_confirm": True
                            })

                            user_id = auth_response.user.id

                            # 2. Create profile linked to rider
                            admin_supabase.table("profiles").insert({
                                "id": user_id,
                                "full_name": selected_rider["full_name"],
                                "role": "rider",
                                "rider_id": selected_rider["id"],
                                "contact_number": selected_rider.get("contact_number")
                            }).execute()

                        st.success(f"Login created for {selected_rider['full_name']}!")
                        st.info(f"Email: {login_email}")
                    except Exception as e:
                        st.error(f"Error creating login: {e}")

    except Exception as e:
        st.error(f"Error loading riders: {e}")

st.write("")

# --------------------------------------------------
# 3. CURRENT RIDERS
# --------------------------------------------------
st.subheader("Current Riders")

try:
    supabase = get_supabase()
    riders = supabase.table("riders").select("*").order("full_name").execute().data

    if not riders:
        st.info("No riders yet.")
    else:
        for rider in riders:
            col1, col2 = st.columns([1, 3])

            with col1:
                if rider.get("profile_picture_url"):
                    st.image(rider["profile_picture_url"], width=70)

            with col2:
                st.markdown(f"**{rider['full_name']}**")
                st.caption(
                    f"Wallet: ₱{rider['wallet_balance']} • "
                    f"{'Online' if rider['is_online'] else 'Offline'} • "
                    f"{'Busy' if rider['is_busy'] else 'Available'}"
                )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Toggle Online", key=f"online_{rider['id']}"):
                    supabase.table("riders").update(
                        {"is_online": not rider["is_online"]}
                    ).eq("id", rider["id"]).execute()
                    st.rerun()
            with c2:
                if st.button("Delete", key=f"delr_{rider['id']}"):
                    supabase.table("riders").delete().eq("id", rider["id"]).execute()
                    st.rerun()

            st.markdown("---")

except Exception as e:
    st.error(f"Failed to load riders: {e}")