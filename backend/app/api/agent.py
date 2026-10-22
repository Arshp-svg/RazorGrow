import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.agents.intent_agent import IntentAgent
from app.api.auth_dependencies import get_current_merchant_context
from app.db.database import SessionLocal
from app.schemas.agent_trace import (
    AgentChatRequest,
    AgentChatResponse,
    ExecutionTraceResponse,
)
from app.services.recommendation_service import recommend_products
from app.services.trace_service import (
    complete_execution,
    get_execution_trace,
    list_merchant_executions,
    record_tool_call,
    start_execution,
)
from app.services.upsell_service import recommend_upsell

router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)

intent_agent = IntentAgent()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    merchant = merchant_context[0]
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    execution = start_execution(
        db=db,
        merchant_id=merchant.id,
        session_id=session_id,
        intent=request.message,
    )

    recommended_product = None
    upsell_product = None
    intent_data = None

    try:
        # Step 1: Tool call - Extract Intent
        t0 = time.perf_counter()
        intent = intent_agent.extract(request.message)
        latency_intent = (time.perf_counter() - t0) * 1000
        intent_data = intent.model_dump()

        record_tool_call(
            db=db,
            execution_id=execution.id,
            tool_name="extract_intent",
            input_data={"message": request.message},
            output_data=intent_data,
            status="success",
            latency_ms=latency_intent,
        )

        # Step 2: Tool call - Search Trusted Catalog
        t0 = time.perf_counter()
        recs = recommend_products(
            db=db,
            intent=intent,
            merchant_id=merchant.id,
        )
        latency_catalog = (time.perf_counter() - t0) * 1000

        record_tool_call(
            db=db,
            execution_id=execution.id,
            tool_name="search_catalog",
            input_data={"intent": intent_data, "merchant_id": merchant.id},
            output_data={"candidates_count": len(recs.recommendations)},
            status="success",
            latency_ms=latency_catalog,
        )

        reply_parts = []
        if recs.recommendations:
            top_rec = recs.recommendations[0]
            recommended_product = {
                "id": top_rec.product_id,
                "name": top_rec.name,
                "price": top_rec.price,
                "category": top_rec.category,
                "inventory": top_rec.inventory,
            }
            reply_parts.append(
                f"I recommend the {top_rec.name} for ₹{top_rec.price:,.0f}."
            )

            # Step 3: Tool call - Find Compatible Upsell
            t0 = time.perf_counter()
            upsell_resp = recommend_upsell(
                db=db,
                product_id=top_rec.product_id,
                merchant_id=merchant.id,
            )
            latency_upsell = (time.perf_counter() - t0) * 1000

            top_upsell = (
                upsell_resp.upsells[0] if upsell_resp.upsells else None
            )
            if top_upsell:
                upsell_product = {
                    "id": top_upsell.product_id,
                    "name": top_upsell.name,
                    "price": top_upsell.price,
                }
                reply_parts.append(
                    f"A great compatible add-on is {top_upsell.name} for ₹{top_upsell.price:,.0f}."
                )

            record_tool_call(
                db=db,
                execution_id=execution.id,
                tool_name="find_upsell",
                input_data={"product_id": top_rec.product_id},
                output_data=(
                    upsell_product
                    if upsell_product
                    else {"upsell": None}
                ),
                status="success",
                latency_ms=latency_upsell,
            )
        else:
            reply_parts.append(
                "I couldn't find an exact match in the catalog, but please let me know if you'd like to adjust your budget or requirements."
            )

        execution = complete_execution(
            db=db,
            execution_id=execution.id,
            status="completed",
        )

        return AgentChatResponse(
            reply=" ".join(reply_parts),
            execution_id=execution.id,
            correlation_id=execution.correlation_id,
            session_id=execution.session_id,
            intent=intent_data,
            recommended_product=recommended_product,
            upsell_product=upsell_product,
            total_latency_ms=execution.total_latency_ms or 0.0,
        )

    except Exception as exc:
        record_tool_call(
            db=db,
            execution_id=execution.id,
            tool_name="error_handler",
            input_data={"error": str(exc)},
            output_data=None,
            status="failed",
            latency_ms=0.0,
        )
        complete_execution(
            db=db,
            execution_id=execution.id,
            status="failed",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(exc)}",
        ) from exc


@router.get("/executions")
def get_executions(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    merchant = merchant_context[0]
    return list_merchant_executions(
        db=db,
        merchant_id=merchant.id,
        limit=limit,
    )


@router.get("/executions/{execution_id}", response_model=ExecutionTraceResponse)
def get_execution_by_id(
    execution_id: int,
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    merchant = merchant_context[0]
    trace = get_execution_trace(
        db=db,
        execution_id=execution_id,
        merchant_id=merchant.id,
    )
    if not trace:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found",
        )
    return trace


@router.get("/executions/{execution_id}/trace", response_model=ExecutionTraceResponse)
def get_execution_full_trace(
    execution_id: int,
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    merchant = merchant_context[0]
    trace = get_execution_trace(
        db=db,
        execution_id=execution_id,
        merchant_id=merchant.id,
    )
    if not trace:
        raise HTTPException(
            status_code=404,
            detail=f"Execution trace {execution_id} not found",
        )
    return trace
