import os
from unittest import TestCase
from sqlalchemy import exc
from werkzeug import test

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test message model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        test = User.signup('test', '1@test.com', 'password', None)
        self.uid = 9876
        test.id = self.uid
        db.session.commit()

        self.test = User.query.get(self.uid)

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()
        return super().tearDown()

    def test_message_model(self):
        """Does basic model work?"""

        m = Message(text='test message', user_id=self.uid)

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.test.messages), 1)
        self.assertEqual(self.test.messages[0].text, 'test message')

    def test_message_likes(self):
        """Does the likes functionality work as intended?"""

        m1 = Message(text='message1', user_id=self.uid)
        m2 = Message(text='message2', user_id=self.uid)

        u = User.signup('test2', '2@test.com', 'password', None)
        u.id = 5555
        db.session.add_all([m1, m2, u])
        db.session.commit()

        u.likes.append(m1)
        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == 5555).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, m1.id)

        u.likes.remove(m1)
        db.session.add(u)
        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == 5555).all()
        self.assertEqual(len(likes), 0)
