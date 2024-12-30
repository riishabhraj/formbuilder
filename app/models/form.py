from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Form(Base):
    __tablename__ = "forms"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    fields = Column(JSON, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"))
    
    creator = relationship("User", back_populates="forms")
    submissions = relationship("Submission", back_populates="form") 