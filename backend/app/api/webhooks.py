from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.services.webhook_service import process_webhook_payload

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(
        default=None,
        alias="X-Razorpay-Signature",
    ),
    x_razorpay_event_id: str | None = Header(
        default=None,
        alias="X-Razorpay-Event-Id",
    ),
    db: Session = Depends(get_db),
):
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing X-Razorpay-Signature header",
        )

    raw_body = await request.body()

    try:
        result = process_webhook_payload(
            db=db,
            payload_bytes=raw_body,
            signature=x_razorpay_signature,
            header_event_id=x_razorpay_event_id,
        )
        return {"status": "ok", "data": result}
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
