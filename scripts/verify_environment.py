#!/usr/bin/env python3
"""
RazorGrow Production Environment & Health Verification Script (Day 14)

Verifies:
1. Python runtime >= 3.11
2. Core dependencies
3. Database connectivity and schema tables
4. Merchant 1 and Policy configuration
5. Catalog inventory
6. FastAPI Health, Readiness, and Liveness endpoints
"""

import os
import sys
from pathlib import Path

# Ensure UTF-8 output if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add backend directory to path
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Default DATABASE_URL to backend/razorgrow.db if not specified
if "DATABASE_URL" not in os.environ:
    db_file = BACKEND_DIR / "razorgrow.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file.as_posix()}"


def check_python_version() -> bool:
    print("\n[1/6] Checking Python Runtime...")
    version = sys.version_info
    print(f"  Detected Python: {version.major}.{version.minor}.{version.micro}")
    if version.major == 3 and version.minor >= 11:
        print("  [OK] Python version compatible (>= 3.11)")
        return True
    print("  [FAIL] Python 3.11 or higher is required.")
    return False


def check_dependencies() -> bool:
    print("\n[2/6] Checking Core Dependencies...")
    required = [
        ("fastapi", "FastAPI"),
        ("sqlalchemy", "SQLAlchemy"),
        ("alembic", "Alembic"),
        ("pydantic", "Pydantic"),
        ("email_validator", "email-validator"),
        ("jwt", "PyJWT"),
        ("argon2", "Argon2-cffi"),
        ("razorpay", "Razorpay SDK"),
        ("groq", "Groq SDK"),
        ("pytest", "Pytest"),
    ]
    all_ok = True
    for module_name, display_name in required:
        try:
            __import__(module_name)
            print(f"  [OK] {display_name} installed")
        except ImportError:
            print(f"  [FAIL] {display_name} missing ({module_name})")
            all_ok = False
    return all_ok


def check_database_schema() -> bool:
    print("\n[3/6] Checking Database Connection & Schema...")
    try:
        from app.db.database import SessionLocal
        from sqlalchemy import inspect

        db = SessionLocal()
        inspector = inspect(db.bind)
        tables = set(inspector.get_table_names())
        db.close()

        required_tables = {
            "users",
            "merchants",
            "merchant_memberships",
            "products",
            "carts",
            "cart_items",
            "orders",
            "policies",
            "approval_requests",
            "webhook_events",
            "refresh_tokens",
            "agent_executions",
            "tool_calls",
            "audit_logs",
            "campaigns",
        }

        missing = required_tables - tables
        if missing:
            print(f"  [FAIL] Missing tables: {missing}")
            print("  Run 'alembic upgrade head' to apply migrations.")
            return False

        print(f"  [OK] All {len(required_tables)} production tables verified")
        return True
    except Exception as exc:
        print(f"  [FAIL] Database check failed: {exc}")
        return False


def check_merchant_and_policy() -> bool:
    print("\n[4/6] Verifying Merchant & Commerce Policy...")
    try:
        from app.db.database import SessionLocal
        from app.models.models import Merchant, Policy

        db = SessionLocal()
        merchant = db.query(Merchant).filter(Merchant.id == 1).first()
        policy = db.query(Policy).filter(Policy.merchant_id == 1).order_by(Policy.id.desc()).first()
        db.close()

        if not merchant:
            print("  [FAIL] Merchant #1 not found in database.")
            return False
        print(f"  [OK] Merchant #1: '{merchant.name}' (Status: {merchant.status})")

        if not policy:
            print("  [FAIL] Policy for Merchant #1 not found.")
            return False
        print(
            f"  [OK] Policy v{policy.version}: Max Transaction: INR {policy.max_order_amount:,.0f} | "
            f"Approval Threshold: INR {policy.approval_threshold or 0:,.0f}"
        )
        return True
    except Exception as exc:
        print(f"  [FAIL] Merchant/Policy check failed: {exc}")
        return False


def check_catalog_inventory() -> bool:
    print("\n[5/6] Verifying Catalog Inventory...")
    try:
        from app.db.database import SessionLocal
        from app.models.models import Product

        db = SessionLocal()
        count = db.query(Product).filter(Product.merchant_id == 1).count()
        in_stock = db.query(Product).filter(Product.merchant_id == 1, Product.inventory > 0).count()
        db.close()

        if count == 0:
            print("  [FAIL] No products found for Merchant #1.")
            return False
        print(f"  [OK] Discovered {count} catalog products ({in_stock} in stock)")
        return True
    except Exception as exc:
        print(f"  [FAIL] Catalog check failed: {exc}")
        return False


def check_api_endpoints() -> bool:
    print("\n[6/6] Verifying FastAPI Health & Probes...")
    try:
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        h_resp = client.get("/health")
        r_resp = client.get("/health/ready")
        l_resp = client.get("/health/live")

        if h_resp.status_code != 200 or h_resp.json().get("database") != "connected":
            print(f"  [FAIL] /health failed: {h_resp.status_code} {h_resp.text}")
            return False
        print(f"  [OK] /health: 200 OK (DB: {h_resp.json().get('database')})")

        if r_resp.status_code != 200:
            print(f"  [FAIL] /health/ready failed: {r_resp.status_code}")
            return False
        print("  [OK] /health/ready: 200 Ready")

        if l_resp.status_code != 200:
            print(f"  [FAIL] /health/live failed: {l_resp.status_code}")
            return False
        print("  [OK] /health/live: 200 Alive")

        return True
    except Exception as exc:
        print(f"  ✗ API verification failed: {exc}")
        return False


def main():
    print("=" * 60)
    print("   RAZORGROW PRODUCTION ENVIRONMENT VERIFICATION (DAY 14)")
    print("=" * 60)

    checks = [
        check_python_version,
        check_dependencies,
        check_database_schema,
        check_merchant_and_policy,
        check_catalog_inventory,
        check_api_endpoints,
    ]

    all_passed = True
    for check in checks:
        if not check():
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("   STATUS: ALL CHECKS PASSED (PRODUCTION READY)")
        print("   Backend is healthy, policies loaded, and ready to serve.")
        print("=" * 60 + "\n")
        sys.exit(0)
    else:
        print("   STATUS: ONE OR MORE CHECKS FAILED")
        print("   Please review the diagnostics above.")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
