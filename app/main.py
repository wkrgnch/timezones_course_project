from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Online Defense Priority", version="0.1.0")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
