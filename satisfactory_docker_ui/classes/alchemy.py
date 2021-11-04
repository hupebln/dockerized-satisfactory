import os

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class User(UserMixin, Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    hashed_password = Column(String)

    def __init__(self, username, password):
        self.name = username
        self.hashed_password = generate_password_hash(password)

    def verify_password(self, pwd):
        return check_password_hash(self.hashed_password, pwd)


def get_session():
    username = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("HOSTNAME_POSTGRES")
    engine = create_engine(f"postgresql://{username}:{password}@{db_host}/{username}")

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)

    return Session


def ensure_admin_user():
    password = os.getenv("ADMIN_PASSWORD")
    Session = get_session()
    session = Session()

    try:
        if password and not session.query(User).filter_by(name="admin").first():
            admin = User(username="admin", password=password)
            session.add(admin)
            session.commit()

        user = session.query(User).filter_by(name="admin").first()
    finally:
        session.close()

    if user:
        return True

    return False
