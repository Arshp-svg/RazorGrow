from app.db.database import SessionLocal
from app.services.dashboard_service import get_dashboard_metrics


db = SessionLocal()

try:
    result = get_dashboard_metrics(db)
    print(result)

finally:
    db.close()