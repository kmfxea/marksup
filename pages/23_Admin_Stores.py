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

    st.write("**Categories * (check all that apply)**")
    selected_categories = []
    c1, c2 = st.columns(2)
    with c1:
        if st.checkbox("Umagahan", key="add_umagahan"):
            selected_categories.append("Umagahan")
        if st.checkbox("Tanghalian", key="add_tanghalian"):
            selected_categories.append("Tanghalian")
        if st.checkbox("Meryenda", key="add_meryenda"):
            selected_categories.append("Meryenda")
    with c2:
        if st.checkbox("Hapunan", key="add_hapunan"):
            selected_categories.append("Hapunan")
        if st.checkbox("Grocery", key="add_grocery"):
            selected_categories.append("Grocery")
        if st.checkbox("Pharmacy", key="add_pharmacy"):
            selected_categories.append("Pharmacy")

    description = st.text_input("Description (optional)")

    st.write("**Location (for distance calculation)**")
    address = st.text_input(
        "Store Address *",
        placeholder="e.g. Dali Fairview, Commonwealth Ave, QC"
    )

    col_lat, col_lng = st.columns(2)
    with col_lat:
        latitude = st.number_input("Latitude", value=14.6960, format="%.6f", help="Example Fairview: 14.6960")
    with col_lng:
        longitude = st.number_input("Longitude", value=121.0880, format="%.6f", help="Example Fairview: 121.0880")

    st.caption("Tip: Open Google Maps → right-click location → copy coordinates")

    st.write("**Store Logo**")
    logo_file = st.file_uploader(
        "Upload Store Logo",
        type=["png", "jpg", "jpeg", "webp"],
        key="store_logo"
    )

    if st.button("Save Store"):
        if not name:
            st.error("Store Name is required.")
        elif not selected_categories:
            st.error("Please select at least one category.")
        elif not address:
            st.error("Store Address is required.")
        else:
            try:
                with st.spinner("Saving store..."):
                    logo_url = upload_logo(logo_file)
                    supabase = get_supabase()
                    supabase.table("stores").insert({
                        "name": name,
                        "category": selected_categories[0],
                        "categories": selected_categories,
                        "description": description,
                        "address": address,
                        "latitude": latitude,
                        "longitude": longitude,
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
# List + Edit
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
                cats = store.get("categories") or []
                if not cats and store.get("category"):
                    cats = [store["category"]]

                st.markdown(f"**{store['name']}**")
                st.caption(f"{', '.join(cats) if cats else 'No category'} • {status}")
                if store.get("address"):
                    st.caption(f"📍 {store['address']}")

            with st.expander(f"✏️ Edit • {store['name']}"):
                new_name = st.text_input("Store Name", value=store["name"], key=f"name_{store['id']}")

                current_cats = store.get("categories") or []
                if not current_cats and store.get("category"):
                    current_cats = [store["category"]]

                st.write("**Categories (check all that apply)**")
                new_categories = []
                ec1, ec2 = st.columns(2)
                with ec1:
                    if st.checkbox("Umagahan", value="Umagahan" in current_cats, key=f"e_uma_{store['id']}"):
                        new_categories.append("Umagahan")
                    if st.checkbox("Tanghalian", value="Tanghalian" in current_cats, key=f"e_tang_{store['id']}"):
                        new_categories.append("Tanghalian")
                    if st.checkbox("Meryenda", value="Meryenda" in current_cats, key=f"e_mer_{store['id']}"):
                        new_categories.append("Meryenda")
                with ec2:
                    if st.checkbox("Hapunan", value="Hapunan" in current_cats, key=f"e_hap_{store['id']}"):
                        new_categories.append("Hapunan")
                    if st.checkbox("Grocery", value="Grocery" in current_cats, key=f"e_gro_{store['id']}"):
                        new_categories.append("Grocery")
                    if st.checkbox("Pharmacy", value="Pharmacy" in current_cats, key=f"e_pha_{store['id']}"):
                        new_categories.append("Pharmacy")

                new_description = st.text_input("Description", value=store.get("description") or "", key=f"desc_{store['id']}")
                new_address = st.text_input("Store Address", value=store.get("address") or "", key=f"addr_{store['id']}")

                elat, elng = st.columns(2)
                with elat:
                    new_lat = st.number_input(
                        "Latitude",
                        value=float(store.get("latitude") or 14.6960),
                        format="%.6f",
                        key=f"lat_{store['id']}"
                    )
                with elng:
                    new_lng = st.number_input(
                        "Longitude",
                        value=float(store.get("longitude") or 121.0880),
                        format="%.6f",
                        key=f"lng_{store['id']}"
                    )

                st.write("**Replace Logo (optional)**")
                new_logo_file = st.file_uploader(
                    "Upload new logo",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"logo_{store['id']}"
                )

                if st.button("Save Changes", key=f"save_{store['id']}"):
                    if not new_categories:
                        st.error("Please select at least one category.")
                    elif not new_address:
                        st.error("Store Address is required.")
                    else:
                        try:
                            update_data = {
                                "name": new_name,
                                "category": new_categories[0],
                                "categories": new_categories,
                                "description": new_description,
                                "address": new_address,
                                "latitude": new_lat,
                                "longitude": new_lng
                            }
                            if new_logo_file:
                                update_data["logo_url"] = upload_logo(new_logo_file)

                            supabase.table("stores").update(update_data).eq("id", store["id"]).execute()
                            st.success("Store updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Update failed: {e}")

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