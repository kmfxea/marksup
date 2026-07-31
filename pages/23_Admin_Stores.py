import streamlit as st
from utils.supabase_client import get_supabase
import uuid

st.set_page_config(
    page_title="Manage Stores • MarksUp",
    page_icon="🛵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

if "user" not in st.session_state or st.session_state["user"].get("role") != "admin":
    st.warning("Admin access only.")
    st.stop()

st.markdown("""
<style>
    .stApp { max-width: 500px; margin: auto; }
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 2.6rem;
        font-weight: 600;
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("Manage Stores")

if st.button("← Back to Dashboard"):
    st.switch_page("pages/21_Admin_Dashboard.py")

st.write("")

# --------------------------------------------------
# Categories (fixed list)
# --------------------------------------------------
CATEGORIES = [
    "Umagahan",
    "Tanghalian",
    "Meryenda",
    "Hapunan",
    "Grocery",
    "Pharmacy"
]

# --------------------------------------------------
# Helper: Upload Logo
# --------------------------------------------------
def upload_logo(file):
    if file is None:
        return None

    supabase = get_supabase()
    file_ext = file.name.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"

    supabase.storage.from_("item-photos").upload(
        file_name,
        file.getvalue(),
        {"content-type": file.type}
    )
    return supabase.storage.from_("item-photos").get_public_url(file_name)

# --------------------------------------------------
# Add New Store
# --------------------------------------------------
with st.expander("➕ Add New Store", expanded=True):
    name = st.text_input("Store Name*")
    category = st.selectbox("Category*", CATEGORIES)
    description = st.text_input("Description (optional)")

    st.write("**Store Logo**")
    logo_file = st.file_uploader(
        "Upload Store Logo",
        type=["png", "jpg", "jpeg", "webp"],
        key="store_logo"
    )

    if st.button("Save Store"):
        if not name:
            st.error("Store Name is required.")
        else:
            try:
                with st.spinner("Saving store..."):
                    logo_url = upload_logo(logo_file)

                    supabase = get_supabase()
                    supabase.table("stores").insert({
                        "name": name,
                        "category": category,
                        "description": description,
                        "logo_url": logo_url,
                        "is_active": True
                    }).execute()

                st.success(f"Store '{name}' added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

st.write("")
st.subheader("Current Stores")

# --------------------------------------------------
# List + Edit Stores
# --------------------------------------------------
try:
    supabase = get_supabase()
    stores = supabase.table("stores").select("*").order("name").execute().data

    if not stores:
        st.info("No stores yet.")
    else:
        for store in stores:
            col1, col2 = st.columns([1, 3])

            with col1:
                if store.get("logo_url"):
                    st.image(store["logo_url"], width=65)
                else:
                    st.markdown("### 🏪")

            with col2:
                status = "Active" if store["is_active"] else "Inactive"
                st.markdown(f"**{store['name']}**")
                st.caption(f"{store.get('category') or 'No category'} • {status}")

            # Edit section
            with st.expander(f"✏️ Edit • {store['name']}"):
                new_name = st.text_input(
                    "Store Name",
                    value=store["name"],
                    key=f"name_{store['id']}"
                )

                # Category dropdown with current value
                current_cat = store.get("category") if store.get("category") in CATEGORIES else CATEGORIES[0]
                new_category = st.selectbox(
                    "Category",
                    CATEGORIES,
                    index=CATEGORIES.index(current_cat),
                    key=f"cat_{store['id']}"
                )

                new_description = st.text_input(
                    "Description",
                    value=store.get("description") or "",
                    key=f"desc_{store['id']}"
                )

                st.write("**Replace Logo (optional)**")
                new_logo_file = st.file_uploader(
                    "Upload new logo",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"logo_{store['id']}"
                )

                if st.button("Save Changes", key=f"save_{store['id']}"):
                    try:
                        update_data = {
                            "name": new_name,
                            "category": new_category,
                            "description": new_description
                        }

                        if new_logo_file:
                            update_data["logo_url"] = upload_logo(new_logo_file)

                        supabase.table("stores").update(update_data).eq("id", store["id"]).execute()
                        st.success("Store updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Update failed: {e}")

            # Toggle + Delete
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Toggle Active", key=f"toggle_{store['id']}"):
                    supabase.table("stores").update({
                        "is_active": not store["is_active"]
                    }).eq("id", store["id"]).execute()
                    st.rerun()
            with c2:
                if st.button("Delete", key=f"del_{store['id']}"):
                    supabase.table("stores").delete().eq("id", store["id"]).execute()
                    st.rerun()

            st.markdown("---")

except Exception as e:
    st.error(f"Failed to load stores: {e}")