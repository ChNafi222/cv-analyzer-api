from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__= "users"

    id = Column(Integer, primary_key=True , index = True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    analyses = relationship("Analysis",back_populates="owner")


class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer)
    matching_skills = Column(String)
    missing_skills = Column(String)
    summary = Column(String)


    owner = relationship("User", back_populates="analyses")



