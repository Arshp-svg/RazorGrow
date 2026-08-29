from app.db.database import engine
from app.models.models import Base


Base.metadata.create_all(engine)

print("Database tables created/updated")