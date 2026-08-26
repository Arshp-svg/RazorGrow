from app.db.database import Base, engine
from app.models.models import Cart, CartItem


Base.metadata.create_all(bind=engine)

print("Cart table:", Cart.__tablename__)
print("CartItem table:", CartItem.__tablename__)
print("Cart model OK")
print("CartItem model OK") 