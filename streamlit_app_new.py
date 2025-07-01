# streamlit_app.py
import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.exceptions import SnowparkSQLException
import pandas as pd

# Constants
STAGES_TABLE = 'app_core.registered_stages'
APP_NAME = "AWS_S3_BROWSER_APP"

# Get the current session
session = get_active_session()

@st.cache_data(ttl=300)
def check_if_admin():
    """
    Checks if the current user has the app_admin role by attempting a
    write operation that only an admin can perform.
    """
    try:
        # This DELETE affects 0 rows but tests the DELETE privilege.
        # It will fail for app_viewer, proving they are not an admin.
        session.sql(f"DELETE FROM {STAGES_TABLE} WHERE 1=0").collect()
        return True
    except SnowparkSQLException:
        # If the operation fails due to permissions, the role is not app_admin.
        return False
    except Exception:
        # Default to non-admin for any other unexpected errors.
        return False

def get_registered_stages():
    """Fetches the list of registered stages from the state table."""
    try:
        stages_df = session.table(STAGES_TABLE).to_pandas()
        return stages_df['STAGE_NAME'].tolist()
    except (SnowparkSQLException, pd.errors.EmptyDataError):
        return []

def convert_size(size_bytes):
    """Convert bytes to a human-readable format."""
    if pd.isna(size_bytes):
        return "N/A"
    size_bytes = float(size_bytes)
    if size_bytes == 0: return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {units[i]}"

def render_stage_management():
    """UI for adding and removing stages. Should only be seen by admins."""
    st.subheader("Manage Stages")
    st.info("Add the full name of a stage you have granted this application access to (e.g., {DB_NAME}.{SCHEMA_NAME}.{STAGE_NAME}")
    
    new_stage_name = st.text_input("Enter Fully Qualified Stage Name:")
    if st.button("Add Stage"):
        if new_stage_name:
            try:
                session.call('app_core.add_stage', new_stage_name)
                st.success(f"Stage '{new_stage_name}' registered!")
                st.cache_data.clear() # Clear cache to refetch stages
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error adding stage: {e}")
        else:
            st.warning("Please enter a stage name.")

    st.markdown("---")
    registered_stages = get_registered_stages()
    st.write("Registered Stages:")
    if registered_stages:
        for stage in registered_stages:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(stage)
            with col2:
                if st.button("Remove", key=f"remove_{stage}"):
                    try:
                        session.call('app_core.remove_stage', stage)
                        st.success(f"Stage '{stage}' unregistered!")
                        st.cache_data.clear() # Clear cache to refetch stages
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error removing stage: {e}")
    else:
        st.write("No stages have been registered yet.")

def render_file_browser(stages):
    """UI for selecting a stage and viewing its files."""
    st.header("Stage File Browser")
    
    selected_stage = st.selectbox("Select a stage to browse:", stages)
    
    if st.button("Refresh File List"):
        st.cache_data.clear()

    if selected_stage:
        try:
            file_list_df = session.sql(f"LIST @{selected_stage}").to_pandas()

            if not file_list_df.empty:
                filtered_df = file_list_df.iloc[:, [0, 1, 3]].copy()
                filtered_df.columns = ['Files', 'Size (Bytes)', 'Last Modified']
                
                # Filter out directory entries
                file_list_df_new = filtered_df[filtered_df['Size (Bytes)'] > 0].copy()

                if not file_list_df_new.empty:
                    file_list_df_new['Size'] = file_list_df_new['Size (Bytes)'].apply(convert_size)
                    
                    file_list_df_new['Files'] = file_list_df_new['Files'].astype(str)
                    extensions = file_list_df_new['Files'].str.split('.').str[-1]
                    no_ext_mask = (extensions.str.upper() == file_list_df_new['Files'].str.upper())
                    extensions[no_ext_mask] = 'UNKNOWN'
                    file_list_df_new['File Type'] = extensions.str.upper()

                    st.subheader(f"Metrics for @{selected_stage}")
                    col1, col2 = st.columns(2)
                    col1.metric("Total Files", len(file_list_df_new))
                    col2.metric("Total Size", convert_size(filtered_df['Size (Bytes)'].sum()))

                    st.subheader("File Listing")
                    display_df = file_list_df_new[['Files', 'Size', 'Last Modified', 'File Type']].rename(
                        columns={'Files': 'File Name'}
                    )
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("This stage contains no files (only directories).")
            else:
                st.info("This stage is empty.")
        except Exception as e:
            st.error(f"Could not list files for stage '{selected_stage}'. Please ensure the app has been granted READ access. Error: {e}")

# --- Main App Logic ---
st.title("Snowflake Stage Browser")

is_admin = check_if_admin()
registered_stages = get_registered_stages()

if not registered_stages:
    if is_admin:
        st.warning("No stages are registered. Please add a stage below and ensure you have run the required GRANT scripts.")
        render_stage_management()
    else:
        st.warning("No stages are registered for this application. Please contact an administrator to add a stage.")
else:
    render_file_browser(registered_stages)
    # Only show the "Manage" expander if the user is an admin
    if is_admin:
        with st.expander("Manage Registered Stages"):
            render_stage_management()

# --- Footer ---
st.markdown("---")
st.markdown("© 2025 Snowflake Native App. Visualizing the future of applications.")
st.markdown("Created by <a href='https://www.linkedin.com/in/sadrulalom/' target='_blank'>Sadrul</a>", unsafe_allow_html=True)
