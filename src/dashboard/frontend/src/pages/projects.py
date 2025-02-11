# src/dashboard/frontend/src/pages/projects.py
import streamlit as st

def main():
    st.title("Projects Page")

    # For demonstration, let's define sample data
    projects = [
        {"id": 1, "name": "Project Alpha", "domain": "Finance", "description": "Personal finance tracker", "logs": "Alpha logs..."},
        {"id": 2, "name": "Project Beta", "domain": "E-commerce", "description": "Online store platform", "logs": "Beta logs..."},
    ]

    st.write("Below is a table of projects from the system:")
    st.table(projects)  # streamlit can display a list of dicts as a table

if __name__ == "__main__":
    main()
