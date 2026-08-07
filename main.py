from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load keys safely
load_dotenv()
BREETH_API_KEY = os.getenv("BREETH_API_KEY")

app = FastAPI(title="AI Interview Agent")

@app.get("/")
def read_root():
    return {"message": "Server is running! Agent is ready to be built."}