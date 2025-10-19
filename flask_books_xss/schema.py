def init_db():
    from .db import engine
    from .models.user import Base
    Base.metadata.create_all(bind=engine)