# coding=utf-8
import configparser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .sqlalchemy_declaractions import Base


# Get config
config = configparser.ConfigParser()
config.read("../data/config.ini")


# Get postgreSQL config and instantiate engine
user = config.get("PostgreSQL", "user", fallback="postgres")
password = config.get("PostgreSQL", "password", fallback=None)
host = config.get("PostgreSQL", "host", fallback="localhost")
port = config.get("PostgreSQL", "port", fallback=5432)
db = config.get("PostgreSQL", "db", fallback="postgres")

# ":" needs to be added, hence this complex thing
if password is not None:
    parsed_password = ":{}".format(password)
else:
    parsed_password = ""

engine = create_engine("postgresql://{user}{passw}@{host}:{port}/{db}".format(user=user, passw=parsed_password, host=host, port=port, db=db))

# Create missing tables
Base.metadata.create_all(engine)

# Configure session class
Session = sessionmaker()
Session.configure(bind=engine)
# Make an actual session
session = Session()

# Example of how to create a test user
# testuser = User(nickname="testuser", fullname="John Doe")
# session.commit()

