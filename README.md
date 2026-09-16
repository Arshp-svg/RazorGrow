# RazorGrow

RazorGrow is a commerce orchestration platform that turns customer intent into a guided shopping and payment workflow.

It combines product discovery, recommendation, upsell suggestions, cart management, checkout confirmation, policy enforcement, payment processing, recovery handling, and audit logging in a single controlled system.

---

## Overview

RazorGrow is designed to help merchants:

- Match customer intent with relevant products
- Recommend complementary items from the catalog
- Build and update carts with server-side totals
- Require explicit customer confirmation before checkout
- Enforce deterministic financial and policy rules
- Create and track Razorpay test-mode orders
- Handle failed payments with a controlled retry flow
- Record decisions and payment events in an audit trail
- Surface operational metrics in a merchant dashboard

The system is intentionally structured so that pricing, inventory, cart totals, and policy decisions remain under backend control.

---

## Core Capabilities

### Product Discovery
Customers can search a structured catalog containing:

- Name
- Category
- Price
- Tags
- Use cases
- Compatible products
- Upsell products
- Inventory

### Recommendation and Upsell
The assistant can interpret customer requirements and suggest products that fit the request. It can also recommend accessories or complementary items when appropriate.

### Cart and Checkout
Cart totals are calculated on the server. Checkout requires explicit customer confirmation before any payment action is started.

### Policy Enforcement
A deterministic policy layer evaluates financial actions before they proceed. Policies can enforce rules such as:

- Maximum order amount
- Discount limits
- Confirmation requirements
- Approval thresholds

### Payment Processing
Approved checkout actions can create Razorpay test-mode orders. Payment amounts are verified against backend order data before status updates are recorded.

### Payment Recovery
If a payment fails, the system supports a controlled retry flow and avoids uncontrolled repeated payment attempts.

### Audit Trail
Important actions are recorded in an audit log, including:

- Policy evaluations
- Order creation
- Payment verification
- Payment status changes
- Failure recovery
- Blocked actions

### Merchant Dashboard
The dashboard presents operational metrics such as:

- Total orders
- Successful payments
- Failed payments
- Recovered payments
- Revenue
- Recovered revenue
- Average order value
- Payment conversion rate
- Policy blocks
- Recent agent activity

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
   +-------------------+-------------------+
                       |
              +--------+--------+
              |                 |
              v                 v
          Razorpay          SQLite Database
          Test Mode         Products
          Orders            Carts
          Payments          Audit Logs
```

---

## Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python |
| Database | SQLite |
| Payments | Razorpay test mode |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| Observability | Structured logs and audit records |

---

## Project Structure

```text
RazorGrow/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agents/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── create_db.py
│   └── seed.py
├── frontend/
│   └── app/
├── docs/
├── .env.example
└── README.md
```

---

## Data Model

The backend includes the following core entities:

- `Product` — catalog records, pricing, inventory, compatibility, and upsell metadata
- `Cart` — shopping cart state and totals
- `CartItem` — items inside a cart
- `Order` — payment and order tracking with Razorpay references
- `Policy` — configurable financial and checkout controls
- `AuditLog` — event history for policy and payment actions

---

## Setup

### Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the database tables:

```bash
python create_db.py
```

Optionally seed the catalog:

```bash
python seed.py
```

Run the API server:

```bash
uvicorn app.main:app --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at the local development URL shown by Next.js.

---

## Environment Variables

Create a `.env` file in the backend project root with the required secrets:

```env
RAZORPAY_KEY_ID=your_test_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
GROQ_API_KEY=your_api_key
```

Do not commit real credentials to source control.

---

## Example Catalog

The seeded catalog includes products such as:

- ProBook 14 Laptop
- CodeMaster 15 Laptop
- UltraBook Air 13
- Ergo Wireless Mouse
- Mechanical Programming Keyboard
- USB-C Laptop Hub
- 27-inch 4K Monitor
- Laptop Cooling Pad
- Noise Cancelling Headphones
- Laptop Backpack

These records support grounded recommendations and upsell suggestions.

---

## Safety and Control Principles

RazorGrow is designed around controlled commerce operations:

- Prices come from the backend database
- Inventory comes from the backend database
- Cart totals are calculated server-side
- The assistant does not directly control final transaction amounts
- Every money-related action passes through policy checks
- Customer confirmation is required before payment initiation
- Payment retries are controlled and bounded
- Razorpay credentials are stored in environment variables
- Audit events capture key financial and policy decisions

---

## Development Notes

The frontend dashboard retrieves data from the backend API and displays product catalog information, activity events, and financial metrics.

The backend uses SQLAlchemy models for commerce objects and audit logging, with configuration loaded from environment variables.

---

## License

Add a license section here if you want to publish the project publicly.

---

## Contact

If you'd like, I can also help you turn this into a stronger product-style README with badges, screenshots, deployment instructions, and API endpoints.
