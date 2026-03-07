from fastapi import APIRouter
from app.schemas.ticket import TicketIn, TicketOut
from app.services.inference_service import classify_ticket

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/classify", response_model=TicketOut)
def classify(ticket: TicketIn):
    result = classify_ticket(ticket.text)
    return result