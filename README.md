# RazorGrow — Autonomous AI Revenue Agent

RazorGrow is an autonomous AI revenue agent for merchant commerce.

It turns a customer's shopping intent into a bounded commerce workflow:

**Customer intent → Product recommendation → Upsell → Customer approval → Policy check → Razorpay test payment → Failure recovery → Audit trail**

The system is designed to increase conversion opportunities and average order value while keeping financial actions controlled by deterministic backend policies.

---

## Problem

Merchants can lose revenue when product discovery, upselling, checkout and payment recovery are disconnected.

A customer may find a product but miss a relevant complementary item, abandon checkout after a payment failure, or encounter a commerce workflow without clear financial controls.

RazorGrow connects these stages into one controlled workflow.

---

## Solution

RazorGrow uses one Revenue Agent with explicit backend tools and deterministic services.

The agent can:

* Understand customer shopping intent
* Search the merchant catalog
* Recommend relevant products
* Suggest compatible upsells
* Add products to the cart
* Request explicit checkout confirmation
* Trigger policy evaluation
* Create Razorpay test-mode orders
* Handle controlled payment failures
* Allow safe payment retry
* Record important decisions in an audit trail
* Provide merchant-facing revenue and activity metrics

The agent does not directly control transaction amounts or bypass financial policies.

---

## Architecture

```text
Customer
   |
   v
Next.js UI
Catalog + Dashboard
   |
   v
FastAPI API / Agent Gateway
   |
   +-------------------+-------------------+
   |                   |                   |
   v                   v                   v
Revenue Agent     Policy Engine      Audit Service
   |                   |                   |
   |                   |                   |
   +-------------------+-------------------+
                       |
              +--------+--------+
              |                 |
              v                 v
          Razorpay          SQLite DB
          Test Mode         Products
          Orders            Carts
          Payments          Orders
                            Audit Logs
```

The architecture uses one Revenue Agent with explicit services rather than a complex multi-agent system.

---

## Tech Stack

| Layer         | Technology                             |
| ------------- | -------------------------------------- |
| Frontend      | Next.js + TypeScript                   |
| Backend       | FastAPI + Python                       |
| Database      | SQLite                                 |
| Payments      | Razorpay test mode                     |
| Validation    | Pydantic + deterministic Policy Engine |
| Observability | Structured logs + AuditLog             |
| UI            | Next.js frontend                       |

The buildathon plan recommends Next.js/TypeScript, FastAPI/Python, SQLite for speed, Razorpay test APIs, Pydantic validation and a deterministic Policy Engine.

---

## Core Features

### 1. Product Discovery

Customers can search the merchant catalog.

Products contain structured information including:

* Name
* Price
* Category
* Tags
* Use cases
* Compatible products
* Upsell products
* Inventory

Recommendations are grounded in catalog data.

---

### 2. AI Recommendation

The agent can identify a suitable product from the customer's requirements.

Example:

```text
Customer:
"I need a laptop for programming under ₹70,000."

Intent:
category = laptop
budget = ₹70,000
use_case = programming

Recommendation:
ProBook 14 Laptop
Price = ₹62,000
```

The recommendation flow is designed so that product price and inventory come from the backend rather than being invented by the model.

---

### 3. Upsell

RazorGrow can identify relevant complementary products.

Example:

```text
Laptop: ₹62,000
Compatible mouse: ₹1,200

Original cart: ₹62,000
Upsell: ₹1,200
Final cart: ₹63,200
```

The customer must explicitly accept the upsell.

---

### 4. Cart & Checkout

Cart totals are calculated server-side.

The checkout flow requires explicit customer confirmation before payment-related actions.

---

### 5. Policy Engine

Every financial action is checked by the deterministic Policy Engine.

The engine can evaluate:

* Maximum transaction amount
* Discount limits
* Customer confirmation
* Approval requirements

Possible outcomes include:

```text
APPROVED
BLOCKED
NEEDS_APPROVAL
```

Example policy block:

```text
Policy blocked checkout:
Order amount exceeds the maximum allowed transaction amount.
```

Another verified scenario:

```text
Policy blocked checkout:
Customer confirmation is required before proceeding.
```

The LLM cannot bypass the Policy Engine.

---

### 6. Razorpay Test Payments

Approved checkout actions can create Razorpay test-mode orders.

The system persists:

* Local order ID
* Cart ID
* Amount
* Amount in paise
* Currency
* Razorpay order ID
* Payment status

Payment amounts are verified against server-side order data.

---

### 7. Payment Failure Recovery

RazorGrow supports a controlled payment failure and retry flow.

Example:

```text
Payment attempt
      |
      v
FAILED
      |
      v
retry_available
      |
      v
Customer retries
      |
      v
PAID
```

The system prevents uncontrolled repeated payment actions.

Verified audit events include:

```text
payment_status_updated
failed
retry_available
```

followed by:

```text
payment_status_updated
paid
```

---

## Safety & Financial Controls

RazorGrow follows several non-negotiable safety rules:

* The LLM never controls the final transaction amount.
* Prices come from the backend/database.
* Inventory comes from the backend/database.
* Cart totals are calculated server-side.
* Every money action passes through the Policy Engine.
* Customer confirmation is required before payment initiation.
* Merchant transaction limits cannot be bypassed by the agent.
* Payment failures cannot trigger uncontrolled repeated retries.
* Raw payment credentials are not stored in the application database.
* Razorpay credentials remain in environment variables/secrets.
* Financial decisions receive audit events.
* When the agent cannot safely determine an action, it should stop or request clarification.

These controls are part of the buildathon's required safety rules.

---

## Audit Trail

RazorGrow records important agent and payment events in `AuditLog`.

Audit events can include:

* Policy evaluation
* Razorpay order creation
* Payment amount verification
* Payment status updates
* Failure recovery
* Policy blocks

Example:

```text
payment_amount_verification
policy_result: APPROVED
external_result: amount_mismatch
recovery: checkout_blocked
```

Payment recovery example:

```text
payment_status_updated
external_result: failed
recovery: retry_available

payment_status_updated
external_result: paid
```

The Agent Activity dashboard makes these decisions visible to the merchant.

---

## Merchant Dashboard

The dashboard provides merchant-facing operational metrics including:

* Total orders
* Created orders
* Successful payments
* Failed payments
* Recovered payments
* Revenue
* Recovered revenue
* Average order value
* Payment conversion rate
* Policy blocks
* Recent agent activity

Example verified metrics during development:

```text
Total Orders:          11
Successful Payments:    5
Recovered Payments:     3
Revenue:            ₹310,000
Recovered Revenue:  ₹186,000
Average Order:       ₹62,000
Conversion:            45.45%
Policy Blocks:           3
```

These figures represent the local development/test database at the time of testing and are not production business results.

---

## Demo Flow

The recommended demo follows the buildathon's golden scenario.

### Step 1 — Customer Intent

```text
"I need a laptop for programming under ₹70,000."
```

### Step 2 — Recommendation

RazorGrow identifies:

```text
Laptop
Budget: ₹70,000
Use case: Programming
```

and recommends a grounded catalog product.

### Step 3 — Upsell

The agent identifies a relevant complementary product.

### Step 4 — Customer Approval

The customer accepts the upsell and confirms checkout.

### Step 5 — Policy

The deterministic Policy Engine evaluates the transaction.

```text
APPROVED
```

### Step 6 — Razorpay

The backend creates a Razorpay test-mode order.

### Step 7 — Payment Failure

A controlled payment failure is demonstrated.

### Step 8 — Recovery

The customer retries and payment succeeds without uncontrolled duplicate financial actions.

### Step 9 — Dashboard

The merchant dashboard shows the resulting revenue, payment recovery and agent activity.

### Step 10 — Audit Trail

The Agent Activity section shows the sequence of decisions and payment events.

---

## Three Judge Scenarios

### Happy Path

Demonstrates:

* AI recommendation
* Upsell
* Customer approval
* Policy approval
* Razorpay transaction

### Policy Violation

Demonstrates:

* Financial controls
* Deterministic policy enforcement
* Bounded agent autonomy

### Payment Failure

Demonstrates:

* Controlled failure
* Retry availability
* Successful recovery
* Avoidance of uncontrolled duplicate payment actions

These are the three judge scenarios defined in the buildathon plan.

---

## Setup

### Backend

Open a terminal:

```bash
cd backend
```

Create/activate the Python virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The API should then be available locally at:

```text
http://127.0.0.1:8000
```

---

### Frontend

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start Next.js:

```bash
npm run dev
```

The frontend can then be opened at the local development address shown by Next.js.

---

## Environment Variables

Razorpay credentials should be stored in environment variables rather than committed to source control.

Example:

```env
RAZORPAY_KEY_ID=your_test_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
```

Do not commit real credentials to Git.

Use `.env.example` as the template for required environment variables.

---

## Testing

The project was tested across the major required scenarios:

### Payment Status

```text
created → failed → paid
```

### Payment Recovery

```text
failed
recovery = retry_available

paid
```

### Amount Verification

Valid amount:

```text
amount_verified
```

Mismatch:

```text
amount_mismatch
recovery = checkout_blocked
```

### Policy Protection

Examples tested include:

```text
Order amount exceeds the maximum allowed transaction amount.
```

and:

```text
Customer confirmation is required before proceeding.
```

### Inventory Protection

Unavailable inventory produces a blocked operation rather than allowing checkout.

Example:

```text
Insufficient inventory for CodeMaster 15 Laptop
```

### Audit Logging

Financial and policy events are persisted in the `audit_logs` table.

---

## Project Structure

```text
razorgrow/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agents/
│   │   ├── models/
│   │   ├── services/
│   │   ├── schemas/
│   │   ├── db/
│   │   └── main.py
│   │
│   └── tests/
│
├── frontend/
│   └── Next.js application
│
├── docs/
│   └── architecture.md
│
├── .env.example
└── README.md
```

---

## Limitations

This project is an MVP built for the Razorpay AI Buildathon.

Current limitations include:

* Razorpay integration is intended for test/demo mode.
* SQLite is used as the initial database.
* The system is not designed as production-scale infrastructure.
* The recommendation system is intentionally bounded by merchant catalog data.
* The payment recovery scenario is controlled for demonstration.
* Advanced multi-agent orchestration is intentionally outside the MVP scope.
* Production merchant onboarding is outside the current scope.

The buildathon plan explicitly prioritizes a small, reliable MVP rather than production-scale infrastructure or a complex multi-agent system.

---

## Project Goal

RazorGrow demonstrates how an AI agent can create legitimate revenue opportunities while remaining bounded by merchant-defined financial controls.

The core principle is:

> **The agent can recommend and orchestrate commerce, but deterministic backend systems remain in control of money.**

---

## Final Demo Story

```text
Customer Intent
      ↓
AI Recommendation
      ↓
Relevant Upsell
      ↓
Customer Approval
      ↓
Policy Gate
      ↓
Razorpay Test Order
      ↓
Payment Failure
      ↓
Safe Retry
      ↓
Payment Success
      ↓
Revenue Dashboard
      ↓
Audit Trail
```
