import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path so modules resolve cleanly
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agents.intent_agent import IntentAgent
from app.db.database import SessionLocal
from app.models.models import Cart, Order, Policy, Product
from app.schemas.intent import ShoppingIntent
from app.services.cart_service import add_to_cart, get_or_create_cart
from app.services.checkout_service import create_checkout_order
from app.services.failure_service import can_retry_payment, execute_payment_retry
from app.services.policy_service import evaluate_policy
from app.services.recommendation_service import recommend_products
from app.services.trace_service import get_execution_trace, start_execution
from app.services.upsell_service import parse_product_ids, recommend_upsell


class AgentEvaluationRunner:
    def __init__(self, dataset_path: str | Path | None = None):
        if dataset_path is None:
            dataset_path = Path(__file__).resolve().parent / "eval_dataset_v1.json"
        self.dataset_path = Path(dataset_path)
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)
        self.db = SessionLocal()
        self.intent_agent = IntentAgent()

    def close(self):
        self.db.close()

    def eval_intent(self, tc: dict) -> tuple[bool, str, float]:
        t0 = time.perf_counter()
        message = tc["input"]["message"]
        intent = self.intent_agent.extract(message)
        latency = (time.perf_counter() - t0) * 1000

        expected_cat = tc["expected"]["category"].lower()
        actual_cat = (intent.category or "").lower()

        if expected_cat not in actual_cat and actual_cat not in expected_cat:
            return False, f"Category mismatch: expected '{expected_cat}', got '{actual_cat}'", latency

        if intent.budget and intent.budget > tc["expected"]["max_budget"]:
            return False, f"Budget parsed {intent.budget} exceeds max {tc['expected']['max_budget']}", latency

        return True, f"Parsed intent: category='{actual_cat}', budget={intent.budget}, use_case='{intent.use_case}'", latency

    def eval_grounding(self, tc: dict) -> tuple[bool, str, float]:
        t0 = time.perf_counter()
        intent_data = tc["input"]["intent"]
        intent = ShoppingIntent(
            category=intent_data.get("category"),
            budget=intent_data.get("budget"),
            use_case=intent_data.get("use_case"),
        )
        merchant_id = tc["input"]["merchant_id"]

        recs = recommend_products(self.db, intent, merchant_id=merchant_id)
        latency = (time.perf_counter() - t0) * 1000

        if not recs.recommendations:
            return False, "No recommendations returned for valid intent", latency

        for rec in recs.recommendations:
            db_product = (
                self.db.query(Product)
                .filter(
                    Product.id == rec.product_id,
                    Product.merchant_id == merchant_id,
                )
                .first()
            )
            if not db_product:
                return False, f"Ungrounded recommendation: Product ID {rec.product_id} not in merchant DB", latency

            if db_product.inventory <= 0:
                return False, f"Out-of-stock product recommended: Product ID {rec.product_id}", latency

        return True, f"Verified {len(recs.recommendations)} grounded catalog products", latency

    def eval_price_safety(self, tc: dict) -> tuple[bool, str, float]:
        t0 = time.perf_counter()
        product_id = tc["input"]["product_id"]
        merchant_id = tc["input"]["merchant_id"]
        client_price = tc["input"]["client_suggested_price"]

        db_product = (
            self.db.query(Product)
            .filter(
                Product.id == product_id,
                Product.merchant_id == merchant_id,
            )
            .first()
        )
        latency = (time.perf_counter() - t0) * 1000

        if not db_product:
            return False, f"Base test product {product_id} not found in DB", latency

        # Test cart addition uses server DB unit price, ignoring client-suggested price
        cart = get_or_create_cart(
            self.db,
            merchant_id=merchant_id,
            customer_id=f"eval_price_safety_{uuid.uuid4().hex[:6]}",
        )
        cart = add_to_cart(self.db, cart, product_id=product_id, quantity=1)

        added_item = [i for i in cart.items if i.product_id == product_id][0]
        if added_item.unit_price == client_price and client_price != db_product.price:
            return False, f"Price safety breached! Client price {client_price} applied", latency

        if added_item.unit_price != db_product.price:
            return False, f"Server price mismatch: expected {db_product.price}, got {added_item.unit_price}", latency

        return True, f"Enforced trusted database price of ₹{db_product.price:,.0f} (rejected client price ₹{client_price})", latency

    def eval_upsell_relevance(self, tc: dict) -> tuple[bool, str, float]:
        t0 = time.perf_counter()
        product_id = tc["input"]["product_id"]
        merchant_id = tc["input"]["merchant_id"]

        base_product = (
            self.db.query(Product)
            .filter(
                Product.id == product_id,
                Product.merchant_id == merchant_id,
            )
            .first()
        )
        upsell_resp = recommend_upsell(self.db, product_id=product_id, merchant_id=merchant_id)
        latency = (time.perf_counter() - t0) * 1000

        if not upsell_resp.upsell:
            return False, "No upsell candidates found for base product", latency

        top_upsell = upsell_resp.upsell
        allowed_ids = set(parse_product_ids(base_product.upsell_products) + parse_product_ids(base_product.compatible_products))

        if top_upsell.product_id not in allowed_ids:
            return False, f"Upsell #{top_upsell.product_id} ({top_upsell.name}) not compatible with base product #{product_id}", latency

        return True, f"Recommended compatible upsell: '{top_upsell.name}' (+₹{top_upsell.price:,.0f})", latency

    def eval_policy(self, tc: dict) -> tuple[bool, str, float]:
        t0 = time.perf_counter()
        limits = tc["input"]["policy_limits"]
        policy = Policy(
            version=1,
            max_order_amount=limits["max_order_amount"],
            max_discount=limits["max_discount"],
            confirmation_required=limits["confirmation_required"],
            approval_threshold=None,
        )

        decision = evaluate_policy(
            policy=policy,
            order_amount=tc["input"]["order_amount"],
            discount=0,
            confirmed=tc["input"]["confirmed"],
        )
        latency = (time.perf_counter() - t0) * 1000

        if decision.decision != tc["expected"]["decision"]:
            return False, f"Expected policy decision {tc['expected']['decision']}, got {decision.decision}", latency

        return True, f"Deterministically blocked: '{decision.reason}'", latency

    def eval_approval(self, tc: dict) -> tuple[bool, str, float]:
        t0 = time.perf_counter()
        limits = tc["input"]["policy_limits"]
        policy = Policy(
            version=1,
            max_order_amount=limits["max_order_amount"],
            max_discount=0,
            confirmation_required=limits["confirmation_required"],
            approval_threshold=limits["approval_threshold"],
        )

        decision = evaluate_policy(
            policy=policy,
            order_amount=tc["input"]["order_amount"],
            discount=0,
            confirmed=tc["input"]["confirmed"],
        )
        latency = (time.perf_counter() - t0) * 1000

        if decision.decision != tc["expected"]["decision"]:
            return False, f"Expected {tc['expected']['decision']}, got {decision.decision}", latency

        return True, f"Paused for Human Approval: '{decision.reason}'", latency

    def eval_tool_safety(self, tc: dict) -> tuple[bool, str, float]:
        t0 = time.perf_counter()
        cart = get_or_create_cart(self.db, merchant_id=1, customer_id=f"eval_tool_{uuid.uuid4().hex[:6]}")
        invalid_item = tc["input"]["invalid_cart_item"]

        rejected = False
        try:
            add_to_cart(self.db, cart, product_id=invalid_item["product_id"], quantity=invalid_item["quantity"])
        except ValueError:
            rejected = True
        latency = (time.perf_counter() - t0) * 1000

        if not rejected:
            return False, "Invalid product_id (-999) was unexpectedly accepted by cart tool", latency

        return True, "Deterministic rejection of invalid parameters without crash", latency

    def eval_payment_idempotency(self, tc: dict) -> tuple[bool, str, float]:
        t0 = time.perf_counter()
        key = f"eval_idemp_{uuid.uuid4().hex}"
        merchant_id = tc["input"]["merchant_id"]

        cart = get_or_create_cart(self.db, merchant_id=merchant_id, customer_id=f"eval_idemp_cust_{uuid.uuid4().hex[:6]}")
        cart = add_to_cart(self.db, cart, product_id=1, quantity=1)

        # First checkout attempt
        order1 = create_checkout_order(self.db, cart_id=cart.id, confirmed=True, merchant_id=merchant_id, idempotency_key=key)

        # Second checkout attempt with identical key
        order2 = create_checkout_order(self.db, cart_id=cart.id, confirmed=True, merchant_id=merchant_id, idempotency_key=key)
        latency = (time.perf_counter() - t0) * 1000

        id1 = order1["local_order_id"]
        id2 = order2["local_order_id"]
        if id1 != id2:
            return False, f"Duplicate order created: Order #{id1} != Order #{id2}", latency

        return True, f"Idempotency verified: Order #{id1} safely returned on repeated request", latency

    def eval_failure_recovery(self, tc: dict) -> tuple[bool, str, float]:
        t0 = time.perf_counter()
        cart = Cart(merchant_id=1, customer_id=f"eval_fail_{uuid.uuid4().hex}", status="active", subtotal=50000, total=50000)
        self.db.add(cart)
        self.db.commit()
        self.db.refresh(cart)

        order = Order(
            merchant_id=1,
            cart_id=cart.id,
            idempotency_key=f"eval_fail_order_{uuid.uuid4().hex}",
            amount=50000,
            status="failed",
            razorpay_order_id=f"order_eval_{uuid.uuid4().hex[:10]}",
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        # Exhaust retries up to max 3
        max_retries = tc["input"]["max_allowed_retries"]
        for _ in range(max_retries):
            execute_payment_retry(self.db, order=order, target_status="failed", error_code="PAYMENT_DECLINED", max_retries=max_retries)

        # 4th attempt must be rejected
        allowed, msg, count = can_retry_payment(self.db, order=order, max_retries=max_retries)
        latency = (time.perf_counter() - t0) * 1000

        if allowed:
            return False, f"Retry attempt permitted after reaching max limit ({max_retries})", latency

        return True, f"Bounded recovery verified: halted at attempt {count} with '{msg}'", latency

    def eval_tenant_isolation(self, tc: dict) -> tuple[bool, str, float]:
        t0 = time.perf_counter()
        m1 = tc["input"]["source_merchant_id"]
        m2 = tc["input"]["target_merchant_id"]

        # Create execution under merchant 1
        exec_m1 = start_execution(self.db, merchant_id=m1, session_id="eval_sess_m1", intent="M1 Private Commerce Action")

        # Attempt to read trace using merchant 2
        trace_leak = get_execution_trace(self.db, execution_id=exec_m1.id, merchant_id=m2)
        latency = (time.perf_counter() - t0) * 1000

        if trace_leak is not None:
            return False, f"Tenant isolation breach! Merchant {m2} read trace of Merchant {m1}", latency

        return True, f"Multi-tenant isolation verified: Merchant {m2} cannot inspect Merchant {m1} records", latency

    def run_all(self) -> dict:
        results = []
        handlers = {
            "intent": self.eval_intent,
            "grounding": self.eval_grounding,
            "price_safety": self.eval_price_safety,
            "upsell_relevance": self.eval_upsell_relevance,
            "policy": self.eval_policy,
            "approval": self.eval_approval,
            "tool_safety": self.eval_tool_safety,
            "payment": self.eval_payment_idempotency,
            "failure": self.eval_failure_recovery,
            "tenant_isolation": self.eval_tenant_isolation,
        }

        print("\n" + "=" * 78)
        print("   RAZORGROW AUTONOMOUS AGENT EVALUATION SUITE (DAY 10)")
        print(f"   Benchmark Dataset: {self.dataset['name']} v{self.dataset['version']}")
        print("=" * 78)

        total_cases = len(self.dataset["test_cases"])
        passed_cases = 0

        for tc in self.dataset["test_cases"]:
            cat = tc["category"]
            handler = handlers.get(cat)
            if not handler:
                print(f"[WARN] No handler implemented for category '{cat}'")
                continue

            passed, details, latency = handler(tc)
            status_text = "PASSED" if passed else "FAILED"
            if passed:
                passed_cases += 1

            results.append({
                "id": tc["id"],
                "category": cat,
                "description": tc["description"],
                "status": status_text,
                "passed": passed,
                "latency_ms": round(latency, 2),
                "details": details,
            })

            icon = "PASS" if passed else "FAIL"
            print(f" [{icon:<4}] {tc['id']:<22} | {cat:<18} | {status_text:<6} | {latency:6.1f}ms | {details[:45]}")

        pass_rate = round((passed_cases / total_cases) * 100, 1)

        print("-" * 78)
        print(f"   EVALUATION SUMMARY: {passed_cases}/{total_cases} Passed ({pass_rate}%)")
        print("=" * 78 + "\n")

        summary = {
            "benchmark": self.dataset["name"],
            "version": self.dataset["version"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_tests": total_cases,
            "passed_tests": passed_cases,
            "failed_tests": total_cases - passed_cases,
            "pass_rate_percent": pass_rate,
            "results": results,
        }

        # Save evaluation report artifact
        report_path = Path(__file__).resolve().parent / "eval_results_v1.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary


def main():
    runner = AgentEvaluationRunner()
    try:
        summary = runner.run_all()
        if summary["failed_tests"] > 0:
            sys.exit(1)
        sys.exit(0)
    finally:
        runner.close()


if __name__ == "__main__":
    main()
