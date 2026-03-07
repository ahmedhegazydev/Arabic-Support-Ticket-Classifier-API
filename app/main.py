from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Arabic Ticket AI API",
    version="1.0.0"
)

app.include_router(router)