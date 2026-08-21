from app.db.database import Base, engine
from app.models.models import Order, Product


Base.metadata.create_all(bind=engine)

print("Database tables created successfully.")