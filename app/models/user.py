from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from passlib.hash import bcrypt
from app.models.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")  # Roles: "user", "admin"

    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password)

    def hash_password(self):
        self.password = bcrypt.hash(self.password)
