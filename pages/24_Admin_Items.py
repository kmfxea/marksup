import streamlit as st
from utils.supabase_client import get_supabase
import uuid

st.set_page_config(
    page_title="Manage Items • MarksUp",
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
    .item-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        border: 1px solid #eee;
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("Manage Items")

if st.button("← Back to Dashboard"):
    st.switch_page("pages/21_Admin_Dashboard.py")

st.write("")

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def upload_file(file, bucket_name: str = "item-photos"):
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
# Select Store
# --------------------------------------------------
supabase = get_supabase()
stores = supabase.table("stores").select("id, name").eq("is_active", True).order("name").execute().data

if not stores:
    st.warning("No active stores found. Please add a store first.")
    st.stop()

store_options = {store["name"]: store["id"] for store in stores}
selected_store_name = st.selectbox("Select Store", list(store_options.keys()))
selected_store_id = store_options[selected_store_name]

st.markdown(f"**Selected:** {selected_store_name}")
st.write("")

# --------------------------------------------------
# Add New Item
# --------------------------------------------------
with st.expander("➕ Add New Item", expanded=True):
    item_name = st.text_input("Item Name*")
    price = st.number_input("Price (₱)*", min_value=0.0, value=0.0, step=1.0)
    description = st.text_input("Description (optional)")
    
    st.write("**Item Photo**")
    item_photo = st.file_uploader(
        "Upload Item Photo",
        type=["png", "jpg", "jpeg", "webp"],
        key="item_photo"
    )

    is_available = st.checkbox("Available", value=True)

    if st.button("Save Item"):
        if not item_name:
            st.error("Item Name is required.")
        elif price <= 0:
            st.error("Price must be greater than 0.")
        else:
            try:
                with st.spinner("Saving item..."):
                    image_url = upload_file(item_photo) if item_photo else None

                    supabase.table("items").insert({
                        "store_id": selected_store_id,
                        "name": item_name,
                        "price": price,
                        "description": description,
                        "image_url": image_url,
                        "is_available": is_available
                    }).execute()

                st.success(f"Item '{item_name}' added to {selected_store_name}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

st.write("")

# --------------------------------------------------
# Current Items of Selected Store
# --------------------------------------------------
st.subheader(f"Items in {selected_store_name}")

try:
    items = supabase.table("items")\
        .select("*")\
        .eq("store_id", selected_store_id)\
        .order("name")\
        .execute().data

    if not items:
        st.info("No items yet for this store.")
    else:
        for item in items:
            with st.container():
                col1, col2 = st.columns([1, 3])

                with col1:
                    if item.get("image_url"):
                        st.image(item["image_url"], width=70)
                    else:
                        st.markdown("📦")

                with col2:
                    status = "✅ Available" if item["is_available"] else "❌ Not Available"
                    st.markdown(f"**{item['name']}**")
                    st.caption(f"₱{item['price']:.2f} • {status}")
                    if item.get("description"):
                        st.caption(item["description"])

                c1, c2, c3 = st.columns(3)

                with c1:
                    if st.button("Toggle", key=f"toggle_{item['id']}"):
                        supabase.table("items").update({
                            "is_available": not item["is_available"]
                        }).eq("id", item["id"]).execute()
                        st.rerun()

                with c2:
                    if st.button("Delete", key=f"delete_{item['id']}"):
                        supabase.table("items").delete().eq("id", item["id"]).execute()
                        st.rerun()

                st.markdown("---")

except Exception as e:
    st.error(f"Failed to load items: {e}")