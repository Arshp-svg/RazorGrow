from app.db.database import Base, engine
from app.models.models import Policy


Base.metadata.create_all(bind=engine)

print("Policy table:", Policy.__tablename__)
print("Policy model OK")