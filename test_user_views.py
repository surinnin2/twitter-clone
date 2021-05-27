"""User views tests."""

import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes, connect_db
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewsTestCase(TestCase):
    """Test user views."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.test = User.signup(username='test', email='test@test.com', password='password', image_url=None)
        self.test.id = 1
        
        self.test.id = 1234

        self.t1 = User.signup('test1', '1@test.com', 'password', None)
        self.t1.id = 1111
        self.t2 = User.signup('test2', '2@test.com', 'password', None)
        self.t2.id = 2222

        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        return super().tearDown()

    def test_users_page(self):
        """test user list page"""

        with self.client as c:
            resp = c.get('/users')

        self.assertIn('@test1', str(resp.data))
        self.assertIn('@test2', str(resp.data))

    def test_users_search(self):
        """test search page"""

        with self.client as c:
            resp = c.get('/users?q=test1')

            self.assertIn('@test1', str(resp.data))
            self.assertNotIn('@test2', str(resp.data))

    def test_user_show(self):
        """test a user page"""

        with self.client as c:
            resp = c.get('/users/1234')
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@test', str(resp.data))

    def setup_likes(self):
        """setup messages for testing likes"""

        m1 = Message(text="trending warble", user_id=1234)
        m2 = Message(text="Eating some lunch", user_id=1234)
        m3 = Message(id=9876, text="likable warble", user_id=1111)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=1234, message_id=9876)

        db.session.add(l1)
        db.session.commit()

    def test_user_show_with_likes(self):
        """test if user page shows info correctly"""
        self.setup_likes()

        with self.client as c:
            resp = c.get("/users/1234")
    
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@test', str(resp.data))

            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all('li', {'class': 'stat'})

            self.assertEqual(len(found), 4)
            self.assertIn('2', found[0].text)
            self.assertIn("0", found[1].text)
            self.assertIn("0", found[2].text)
            self.assertIn('1', found[3].text)

    def test_add_like(self):
        """test add like functionality"""
        m = Message(id=1984, text="The earth is round", user_id=1111)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1234

            resp = c.post("/users/toggle_like/1984", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==1984).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, 1234)

    def test_remove_like(self):
        """test remove like functionality"""
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, 1234)

        l = Likes.query.filter(
            Likes.user_id==1234 and Likes.message_id==m.id
        ).one()

        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1234

            resp = c.post(f"/users/toggle_like/{m.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            
            self.assertEqual(len(likes), 0)
        
    def setup_followers(self):
        """setup for testing follows"""
        f1 = Follows(user_being_followed_id=1111, user_following_id=1234)
        f2 = Follows(user_being_followed_id=2222, user_following_id=1234)
        f3 = Follows(user_being_followed_id=1234, user_following_id=1111)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

    def test_user_show_with_follows(self):

        self.setup_followers()

        with self.client as c:
            resp = c.get("/users/1234")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 0 messages
            self.assertIn("0", found[0].text)

            # Test for a count of 2 following
            self.assertIn("2", found[1].text)

            # Test for a count of 1 follower
            self.assertIn("1", found[2].text)

            # Test for a count of 0 likes
            self.assertIn("0", found[3].text)

    def test_show_following(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1234

            resp = c.get(f"/users/{1234}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))

    def test_show_followers(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1234

            resp = c.get(f"/users/{1234}/followers")

            self.assertIn("@test1", str(resp.data))
            self.assertNotIn("@test2", str(resp.data))