                    ┌──────────────────────┐
                    │      Customer        │
                    │ Natural Language     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     Next.js UI       │
                    │ Catalog + Dashboard  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     FastAPI API      │
                    │    Agent Gateway     │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ Revenue Agent│  │ Policy Engine │  │ Audit Service│
     │ Recommend    │  │ Amount limit  │  │ Decisions    │
     │ Upsell       │  │ Confirmation  │  │ Payments     │
     │ Checkout     │  │ Inventory     │  │ Recovery     │
     └──────┬───────┘  └──────────────┘  └──────────────┘
            │
            ▼
     ┌──────────────┐
     │   Database   │
     │ SQLite       │
     │ Products     │
     │ Carts        │
     │ Orders       │
     │ Audit Logs   │
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │   Razorpay   │
     │  Test Mode   │
     └──────────────┘