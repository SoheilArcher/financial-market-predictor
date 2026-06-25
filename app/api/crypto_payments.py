from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.crypto_payment import CryptoPaymentInvoice
from app.models.user import User
from app.services.crypto_payments import (
    create_crypto_invoice,
    list_user_invoices,
    serialize_invoice,
    submit_payment_proof,
)

router = APIRouter(prefix="/crypto-payments", tags=["crypto-payments"])


@router.post("/invoices")
async def create_invoice(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        invoice = await create_crypto_invoice(
            session=session,
            user=current_user,
            amount=float(payload.get("amount") or 0),
            currency=payload.get("currency") or "USDT",
            network=payload.get("network") or "TRC20",
            purpose=payload.get("purpose") or "managed_portfolio",
            managed_request_id=payload.get("managed_request_id"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_invoice(invoice)


@router.get("/invoices")
async def my_invoices(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    invoices = await list_user_invoices(session=session, user_id=current_user.id, limit=limit)
    return {
        "items": [serialize_invoice(invoice) for invoice in invoices],
        "count": len(invoices),
        "summary_fa": "لیست پرداخت‌های کریپتویی شما.",
    }


@router.post("/invoices/{invoice_id}/proof")
async def submit_proof(
    invoice_id: int,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    invoice = await session.get(CryptoPaymentInvoice, invoice_id)
    if not invoice or invoice.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    tx_hash = str(payload.get("tx_hash") or "").strip()
    if len(tx_hash) < 10:
        raise HTTPException(status_code=400, detail="tx_hash is required")
    updated = await submit_payment_proof(
        session=session,
        invoice=invoice,
        tx_hash=tx_hash,
        payer_wallet=payload.get("payer_wallet"),
        note=payload.get("note"),
    )
    return serialize_invoice(updated)
