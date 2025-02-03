import os

PROJECTS_ROOT = "./../projects"

def ensure_project_directory(project_name: str):
    """
    Ensures the project directory exists. Creates it if necessary.
    """
    project_path = os.path.join(PROJECTS_ROOT, project_name)
    if not os.path.exists(project_path):
        os.makedirs(project_path)
        print(f"Created project directory: {project_path}")
    return project_path

def create_or_update_file(project_name: str, filename: str, content: str):
    """
    Creates or updates a file in the project directory.
    """
    project_path = ensure_project_directory(project_name)
    file_path = os.path.join(project_path, filename)
    
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    
    print(f"File {filename} updated in project {project_name}.")
    return file_path

def delete_file(project_name: str, filename: str):
    """
    Deletes a file in the project directory if it exists.
    """
    project_path = ensure_project_directory(project_name)
    file_path = os.path.join(project_path, filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File {filename} deleted in project {project_name}.")
        return True
    return False
