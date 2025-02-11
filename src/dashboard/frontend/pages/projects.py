# src/dashboard/frontend/pages/projects.py
import sys
import os

# Get the absolute path of the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
# Ensure the project root is in sys.path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    
import streamlit as st
from sqlalchemy.orm import Session
from src.db.models import Project, get_db

def main():
    st.title("Projects Page")
    
    db: Session = next(get_db())
    
    # Query projects
    projects = db.query(Project).all()

    if not projects:
        st.write("No projects found.")
        return

    # Convert to a list of dicts to show in table
    project_data = []
    for p in projects:
        project_data.append({
            "ID": p.id,
            "Name": p.project_name,
            "Domain": p.domain,
            "Description": p.description
        })

    st.write("Below are the projects in the system:")
    st.table(project_data)

    st.write("Select a project ID to view details:")
    project_ids = [p.id for p in projects]
    selected_id = st.selectbox("Project ID", project_ids)

    # Provide a button to go to project details
    if st.button("Go to Project Details"):
        # We can't directly switch pages in code, but we can show instructions or store in session
        st.session_state["selected_project_id"] = selected_id
        st.write("Please navigate to 'Project Details' in the sidebar.")

if __name__ == "__main__":
    main()
