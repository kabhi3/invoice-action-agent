
from fastapi import FastAPI

app = FastAPI(title="Invoice A2A Agent")


@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "invoice-a2a-agent"
    }
