# v4coppercoreagent/src/dashboard/backend/app.py

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "Core Agent Platform v4 - Dashboard Backend"}
