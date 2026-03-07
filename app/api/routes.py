from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.schemas.ticket import TicketIn, TicketOut
from app.services.inference_service import classify_ticket

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.post("/classify", response_model=TicketOut)
def classify(ticket: TicketIn):
    result = classify_ticket(ticket.text)
    return result