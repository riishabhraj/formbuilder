from sqlalchemy import Column, Integer, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"))
    data = Column(JSON, nullable=False)
    submitted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=func.now()
    )

    form = relationship("Form", back_populates="submissions") 