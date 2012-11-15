import unittest
import transaction

from pyramid import testing

from .models import DBSession


class TestMyView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        from sqlalchemy import create_engine
        engine = create_engine('sqlite://')
        from .models import Base, Message
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            pass

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()
