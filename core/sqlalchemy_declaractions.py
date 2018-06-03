# coding=utf-8

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    nickname = Column(String(12))
    fullname = Column(String(50))

    password = Column(String(150))

    def __repr__(self):
        return "<User(nickname={}, fullname={}, password={})>".format(self.nickname, self.fullname, self.password)