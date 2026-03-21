from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from .database import Base
from sqlalchemy.orm import relationship
from datetime import date

print("DEBUG Boolean: ", Boolean, type(Boolean))

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, index = True)
    username = Column(String, unique = True, index = True, nullable = False)
    password_hash = Column(String, nullable = False)
    is_admin = Column(Boolean, default = True)

class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    date = Column(Date, nullable = False)
    profession = Column(String, nullable = False)
    section = Column(String, nullable = False)
    salon = Column(String, nullable = False)

    user = relationship("User", backref="observations")

class Page2Check(Base):
    __tablename__ = "live_checks"

    id = Column(Integer, primary_key = True, index = True)
    observation_id = Column(Integer, ForeignKey("observations.id", ondelete = "CASCADE"), nullable = False)

    apa_curenta = Column(String, nullable = False)
    sapun_lichid = Column(String, nullable = False)
    prosop_hartie = Column(String, nullable = False)
    dezinfectant = Column(String, nullable = False)
    pictograme = Column(String, nullable = False)
    pregatire_maini = Column(String, nullable = False)

    observation = relationship("Observation", backref = "page2")

class FinalStep(Base):
    __tablename__ = "final_steps"

    id = Column(Integer, primary_key = True, index = True)
    observation_id = Column(Integer, ForeignKey("observations.id", ondelete="CASCADE"), nullable = False)
    step_number = Column(Integer, nullable = False)
    is_mandatory = Column(Boolean, nullable = False)
    method = Column(String, nullable = True)
    rating = Column(String, nullable = True)

    observation = relationship("Observation", backref = "page3")

class HandwashSurvey(Base):
    __tablename__ = "handwash_surveys"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    date = Column(Date, nullable = False)

    step1 = Column(Boolean, nullable = False)
    step2 = Column(Boolean, nullable = False)
    step3 = Column(Boolean, nullable = False)
    step4 = Column(Boolean, nullable = False)
    step5 = Column(Boolean, nullable = False)
    step6 = Column(Boolean, nullable = False)
    step7 = Column(Boolean, nullable = False)

    user = relationship("User", backref = "handwash_surveys")

