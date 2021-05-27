"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test user model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        t1 = User.signup('test1', '1@test.com', 'password', None)
        t1.id = 1111
        
        t2 = User.signup('test2', '2@test.com', 'password', None)
        t2.id = 2222

        db.session.commit()

        t1 = User.query.get(1111)
        t2 = User.query.get(2222)

        self.t1 = t1
        self.t2 = t2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    
    def test_repr_method(self):
        """Does the repr method work as expected?"""
        
        repr = self.t1.__repr__()
        self.assertEqual(repr, f'<User #{self.t1.id}: {self.t1.username}, {self.t1.email}>')

    def test_follows(self):
        """Test following and followers column"""

        self.t1.following.append(self.t2)
        db.session.commit()

        self.assertEqual(len(self.t1.following), 1)
        self.assertEqual(len(self.t1.followers), 0)
        self.assertEqual(len(self.t2.following), 0)
        self.assertEqual(len(self.t2.followers), 1)

        self.assertEqual(self.t1.following[0].id, self.t2.id)
        self.assertEqual(self.t2.followers[0].id, self.t1.id)

    def test_is_following(self):
        """
        Does is_following successfully detect when user1 is following user2?
        Does is_following successfully detect when user1 is not following user2?
        """

        self.t1.following.append(self.t2)
        db.session.commit()

        self.assertTrue(self.t1.is_following(self.t2))

        self.t1.following.remove(self.t2)
        db.session.add(self.t1)
        db.session.commit()

        self.assertFalse(self.t1.is_following(self.t2))

    def test_is_followed_by(self):
        """
        Does is_followed_by successfully detect when user1 is followed by user2?
        Does is_followed_by successfully detect when user1 is not followed by user2?
        """

        self.t1.following.append(self.t2)
        db.session.commit()

        self.assertTrue(self.t2.is_followed_by(self.t1))

        self.t1.following.remove(self.t2)
        db.session.add(self.t1)
        db.session.commit()

        self.assertFalse(self.t2.is_followed_by(self.t1))

    def test_valid_signup(self):
        """
        Does User.create successfully create a new user given valid credentials?
        """

        test = User.signup('test', 'test@test.com', 'password', None)
        test.id = 3333
        db.session.commit()

        test = User.query.get(3333)
        
        self.assertIsNotNone(test)
        self.assertEqual(test.username, 'test')
        self.assertEqual(test.email, 'test@test.com')
        self.assertTrue(test.password.startswith('$2b$'))

    def test_invalid_signup(self):
        """
        Does User.create fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?
        """

        test = User.signup('test', None, 'password', None)
        test.id = 4
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
        
    def test_valid_authentication(self):
        """
        Does User.authenticate successfully return a user when given a valid username and password?
        """

        uname = self.t1.username
        pwd = 'password'
        auth = User.authenticate(uname, pwd)

        self.assertIsNotNone(auth)
        self.assertEqual(auth.id, self.t1.id)

    def test_invalid_authentication(self):
        """
        Does User.authenticate fail to return a user when the username is invalid?
        """

        uname = 'fakeuname'
        pwd = 'DNE'
        auth = User.authenticate(uname, pwd)

        self.assertFalse(auth)

    def test_wrong_password(self):
        """
        Does User.authenticate fail to return a user when the password is invalid?
        """

        uname = self.t1.username
        pwd = 'wrongpwd'
        
        self.assertFalse(User.authenticate(uname, pwd))