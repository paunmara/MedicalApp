from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi import Depends, Request
from . import models
from .database import get_db
from .config import settings
import os

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds = 12, deprecated='auto')

def hash_password(password: str) -> str:
    """return a bcrypt hash of the password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """check if plain password matches hash stored in DB"""
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, username: str, password: str, is_admin: bool = True):
    """create a new user with hashed password"""
    user = models.User(
        username = username,
        password_hash = hash_password(password),
        is_admin = is_admin
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def init_admin_user(db):

    admin = get_user_by_username(db, "admin")
    secure_password = settings.ADMIN_PASSWORD

    if not admin:

        create_user(db, "admin", secure_password, is_admin=True)
        print("Admin user created successfully.")
    else:

        from .authentification import hash_password
        admin.password_hash = hash_password(secure_password)
        admin.is_admin = True
        db.add(admin)
        db.commit()
        print("Admin password synchronized with environment variables.")

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    return db.query(models.User).filter(
        models.User.id == user_id
    ).first()
