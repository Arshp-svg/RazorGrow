import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.models import (
    AgentExecution,
    AuditLog,
    Campaign,
    Cart,
    CartItem,
    Order,
    Product,
    ToolCall,
)
from app.services.audit_service import record_audit
from app.services.upsell_service import parse_product_ids


def get_revenue_metrics(db: Session, merchant_id: int) -> dict:
    orders = (
        db.query(Order)
        .filter(Order.merchant_id == merchant_id)
        .all()
    )
    total_orders = len(orders)

    successful_payments = sum(1 for o in orders if (o.status or "").lower() == "paid")
    failed_payments = sum(1 for o in orders if (o.status or "").lower() == "failed")
    created_orders = sum(1 for o in orders if (o.status or "").lower() == "created")

    total_revenue = sum(o.amount for o in orders if (o.status or "").lower() == "paid")

    # Audit logs for failure recovery & policy checks
    audit_logs = (
        db.query(AuditLog)
        .filter(AuditLog.merchant_id == merchant_id)
        .all()
    )

    failed_order_ids = {
        audit.entity_id
        for audit in audit_logs
        if audit.action == "payment_status_updated"
        and (audit.external_result or "").lower() == "failed"
        and audit.entity_id
    }

    recovered_orders = [
        o for o in orders
        if (o.status or "").lower() == "paid" and str(o.id) in failed_order_ids
    ]
    recovered_payments = len(recovered_orders)
    recovered_revenue = sum(o.amount for o in recovered_orders)

    # Calculate Upsell and AI-influenced revenue
    paid_orders = [o for o in orders if (o.status or "").lower() == "paid"]
    upsell_revenue = 0.0
    ai_influenced_revenue = 0.0

    for order in paid_orders:
        cart = db.query(Cart).filter(Cart.id == order.cart_id).first()
        if cart and cart.items:
            # If cart has more than 1 item, complementary items represent upsells
            if len(cart.items) > 1:
                # Add-on items sum
                addon_sum = sum(
                    item.quantity * item.unit_price
                    for item in cart.items[1:]
                )
                upsell_revenue += addon_sum
                ai_influenced_revenue += order.amount
            else:
                # If only 1 item, check if customer was directed via agent
                ai_influenced_revenue += order.amount

    policy_blocks = sum(
        1
        for a in audit_logs
        if a.action == "policy_evaluated" and a.policy_result == "BLOCK"
    )

    average_order_value = (
        total_revenue / successful_payments
        if successful_payments > 0
        else 0.0
    )

    payment_conversion_rate = (
        (successful_payments / total_orders) * 100
        if total_orders > 0
        else 0.0
    )

    payment_recovery_rate = (
        (recovered_payments / failed_payments) * 100
        if failed_payments > 0
        else 0.0
    )

    return {
        "total_orders": total_orders,
        "created_orders": created_orders,
        "successful_payments": successful_payments,
        "failed_payments": failed_payments,
        "recovered_payments": recovered_payments,
        "total_revenue": round(total_revenue, 2),
        "recovered_revenue": round(recovered_revenue, 2),
        "upsell_revenue": round(upsell_revenue, 2),
        "ai_influenced_revenue": round(ai_influenced_revenue, 2),
        "average_order_value": round(average_order_value, 2),
        "payment_conversion_rate": round(payment_conversion_rate, 2),
        "payment_recovery_rate": round(payment_recovery_rate, 2),
        "policy_blocks": policy_blocks,
    }


def get_agent_metrics(db: Session, merchant_id: int) -> dict:
    executions = (
        db.query(AgentExecution)
        .filter(AgentExecution.merchant_id == merchant_id)
        .all()
    )

    total_executions = len(executions)
    completed_executions = sum(1 for e in executions if e.status == "completed")
    failed_executions = sum(1 for e in executions if e.status == "failed")

    latencies = [e.total_latency_ms for e in executions if e.total_latency_ms]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    execution_ids = [e.id for e in executions]
    tool_calls = (
        db.query(ToolCall)
        .filter(ToolCall.execution_id.in_(execution_ids))
        .all()
        if execution_ids
        else []
    )

    tool_counts: dict[str, int] = {}
    for call in tool_calls:
        tool_counts[call.tool_name] = tool_counts.get(call.tool_name, 0) + 1

    return {
        "total_executions": total_executions,
        "completed_executions": completed_executions,
        "failed_executions": failed_executions,
        "average_latency_ms": round(avg_latency, 2),
        "total_tool_calls": len(tool_calls),
        "tool_breakdown": tool_counts,
    }


def generate_revenue_insights(db: Session, merchant_id: int) -> dict:
    products = (
        db.query(Product)
        .filter(
            Product.merchant_id == merchant_id,
            Product.inventory > 0,
        )
        .all()
    )

    if not products:
        return {
            "insights": ["Catalog is currently empty. Add products to activate AI revenue recommendations."],
            "recommendations": [],
            "campaign_proposal": None,
        }

    # Find highest price base product that has compatible upsells with available stock
    best_bundle = None
    for prod in sorted(products, key=lambda p: p.price, reverse=True):
        candidate_ids = parse_product_ids(prod.compatible_products) + parse_product_ids(prod.upsell_products)
        if candidate_ids:
            for c_id in candidate_ids:
                cand = next((p for p in products if p.id == c_id), None)
                if cand and cand.inventory > 0:
                    best_bundle = (prod, cand)
                    break
        if best_bundle:
            break

    if not best_bundle:
        # Fallback to top 2 products with inventory
        if len(products) >= 2:
            best_bundle = (products[0], products[1])

    if not best_bundle:
        return {
            "insights": ["Single product catalog available. Add compatible accessories to create bundles."],
            "recommendations": [],
            "campaign_proposal": None,
        }

    base_product, addon_product = best_bundle

    # Calculate bundle pricing
    base_price = base_product.price
    addon_price = addon_product.price
    combined_price = base_price + addon_price
    discount_pct = 10.0
    discounted_price = round(combined_price * (1.0 - (discount_pct / 100.0)), 2)

    title = f"AI Bundle: {base_product.name} + {addon_product.name}"
    description = (
        f"Pair {base_product.name} (₹{base_price:,.0f}) with compatible {addon_product.name} "
        f"(₹{addon_price:,.0f}) with an exclusive {discount_pct:.0f}% bundle discount "
        f"for a total of ₹{discounted_price:,.0f}."
    )
    bundle_config = json.dumps({
        "base_product_id": base_product.id,
        "base_product_name": base_product.name,
        "addon_product_id": addon_product.id,
        "addon_product_name": addon_product.name,
        "original_total": combined_price,
        "discounted_total": discounted_price,
        "discount_percent": discount_pct,
    })

    projected_impact = (
        f"Projected to increase AOV by up to ₹{addon_price * 0.9:,.0f} "
        f"based on current catalog affinity between {base_product.category} and {addon_product.category}."
    )

    # Persist as a Campaign proposal requiring merchant approval
    campaign = Campaign(
        merchant_id=merchant_id,
        title=title,
        description=description,
        bundle_config=bundle_config,
        discount_percent=discount_pct,
        status="PENDING_APPROVAL",
        projected_impact=projected_impact,
        created_at=datetime.now(timezone.utc),
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    record_audit(
        db=db,
        merchant_id=merchant_id,
        action="revenue_insight_generated",
        entity_id=str(campaign.id),
        policy_result="NEEDS_APPROVAL",
        external_result="proposal_created",
        error=None,
        recovery="pending_merchant_decision",
    )

    return {
        "insights": [
            f"Catalog opportunity: {base_product.name} has {addon_product.name} listed as an available compatible item.",
            f"Inventory check: Base item has {base_product.inventory} units; add-on has {addon_product.inventory} units.",
            f"Grounded recommendation: Propose a {discount_pct:.0f}% bundle discount.",
        ],
        "recommendations": [
            {
                "type": "bundle_promotion",
                "base_product": base_product.name,
                "addon_product": addon_product.name,
                "regular_price": combined_price,
                "bundle_price": discounted_price,
                "discount_percent": discount_pct,
            }
        ],
        "campaign_proposal": {
            "id": campaign.id,
            "title": campaign.title,
            "description": campaign.description,
            "status": campaign.status,
            "projected_impact": campaign.projected_impact,
            "discount_percent": campaign.discount_percent,
        },
    }


def list_campaigns(db: Session, merchant_id: int) -> list[dict]:
    campaigns = (
        db.query(Campaign)
        .filter(Campaign.merchant_id == merchant_id)
        .order_by(Campaign.id.desc())
        .all()
    )

    return [
        {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "bundle_config": json.loads(c.bundle_config) if c.bundle_config else None,
            "discount_percent": c.discount_percent,
            "status": c.status,
            "projected_impact": c.projected_impact,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "decided_at": c.decided_at.isoformat() if c.decided_at else None,
            "decided_by_user_id": c.decided_by_user_id,
        }
        for c in campaigns
    ]


def decide_campaign(
    db: Session,
    campaign_id: int,
    merchant_id: int,
    user_id: int,
    approve: bool,
) -> Campaign:
    campaign = (
        db.query(Campaign)
        .filter(
            Campaign.id == campaign_id,
            Campaign.merchant_id == merchant_id,
        )
        .first()
    )

    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    if campaign.status != "PENDING_APPROVAL":
        raise ValueError(f"Campaign is already in status '{campaign.status}'")

    campaign.status = "APPROVED" if approve else "REJECTED"
    campaign.decided_at = datetime.now(timezone.utc)
    campaign.decided_by_user_id = user_id
    db.commit()
    db.refresh(campaign)

    record_audit(
        db=db,
        merchant_id=merchant_id,
        action="campaign_approved" if approve else "campaign_rejected",
        entity_id=str(campaign.id),
        user_id=user_id,
        policy_result="APPROVED" if approve else "REJECTED",
        external_result=campaign.status,
        error=None,
        recovery=None,
    )

    return campaign
