# coding=utf-8
from .redis import Users


class Coordinator:
    def __init__(self):
        self.users = Users()



