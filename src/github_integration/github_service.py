import os
from pathlib import Path
from dotenv import load_dotenv
from github import Github
import base64
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def push_to_github(project_repo, file_path, code_snippet):
    token = os.getenv("GITHUB_TOKEN", "")
    g = Github(token)
    repo = g.get_repo(f"{os.getenv("GITHUB_ACCOUNT_USERNAME", "")}/{project_repo}")
    path = file_path
    try:
        contents = repo.get_contents(path, ref="main")
        # update existing
        repo.update_file(
            path=path,
            message="Update generated code",
            content=code_snippet,
            sha=contents.sha,
            branch="main"
        )
    except:
        # create new
        repo.create_file(
            path=path,
            message="Add generated code",
            content=code_snippet,
            branch="main"
        )
