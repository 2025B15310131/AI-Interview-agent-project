from fastapi import FastAPI
from dotenv import load_dotenv
from openai import OpenAI
import os

# 1. Load Keys
load_dotenv()
BREETH_API_KEY = os.getenv("BREETH_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 2. Initialize OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# 3. Setup App
app = FastAPI(title="AI Interview Agent")

@app.get("/")
def read_root():
    return {"message": "Server is running! OpenAI is connected and ready to interview."}