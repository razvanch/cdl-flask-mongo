import json
import unittest

from flask_pymongo import PyMongo

import blog


def safe_object_id(code):
    try:
        return ObjectId(code)
    except:
        return None


def safe_decode(data):
    if isinstance(data, bytes):
        data = data.decode()

    try:
        return json.loads(str(data))
    except:
        return None


class BlogTest(unittest.TestCase):
    def setUp(self):
        del blog.app.extensions['pymongo']
        blog.app.config['MONGO_DBNAME'] = 'test_' + blog.app.name
        blog.mongo = PyMongo(blog.app)
        self.mongo = blog.mongo
        self.app = blog.app

    def assert_code(self, code, correct):
        self.assertEqual(code, correct,
                'Handler should return %d, but returned %d' % (correct, code))

    def default_author(self):
        return {'first_name': 'Foo', 'last_name': 'Bar', 'email': 'foobar@gmail.com'}

    def default_date(self):
        return '03-14-2018'

    def default_post(self, author_id):
        return {'author_id': author_id, 'title': 'Default Title',
                'content': 'Descriptive content.', 'date': self.default_date()}

    def insert_author(self):
        author = self.default_author()

        with self.app.app_context() as c:
            result = self.mongo.db.authors.insert_one(author)
            author_id = str(result.inserted_id)

        author['_id'] = {'$oid': author_id}

        return author

    def insert_post(self):
        author = self.insert_author()
        post = self.default_post(author['_id']['$oid'])

        with self.app.app_context() as c:
            result = self.mongo.db.posts.insert_one(post)
            post_id = str(result.inserted_id)

        post['_id'] = {'$oid': post_id}

        return post

    def test_empty_db(self):
        with self.app.app_context() as c:
            self.assertEqual(self.mongo.db.authors.count(), 0,
                    'Authors should be empty.')
            self.assertEqual(self.mongo.db.posts.count(), 0,
                    'Posts should be empty.')

    def test_authors_post_invalid_data(self):
        with self.app.test_client() as c:
            rv = c.post('/authors', data='somestring')

            self.assert_code(rv.status_code, 400)

    def test_authors_post_missing_field(self):
        with self.app.test_client() as c:
            rv = c.post('/authors', data=json.dumps({'first_name': 'Missing'}))

            self.assert_code(rv.status_code, 400)

    def test_authors_post_extra_field(self):
        with self.app.test_client() as c:
            rv = c.post('/authors', data=json.dumps({'first_name': 'Foo',
                    'last_name': 'Bar', 'email': 'foobar@gmail.com', 'extra': 3}))

            self.assert_code(rv.status_code, 400)

    def test_authors_post_valid(self):
        with self.app.test_client() as c:
            author = self.default_author()

            rv = c.post('/authors', data=json.dumps(author))

            self.assert_code(rv.status_code, 200)

            author = safe_decode(rv.data)

            self.assertIsNotNone(author)
            self.assertIn('first_name', author)
            self.assertIn('last_name', author)
            self.assertIn('email', author)
            self.assertIn('_id', author)
            self.assertIn('$oid', author['_id'])
            self.assertEqual(author['first_name'], 'Foo')
            self.assertEqual(author['last_name'], 'Bar')
            self.assertEqual(author['email'], 'foobar@gmail.com')

    def test_authors_get_one_author_valid(self):
        author = self.insert_author()

        with self.app.test_client() as c:
            rv = c.get('/authors')

            self.assert_code(rv.status_code, 200)

            authors = safe_decode(rv.data)

            self.assertEqual(len(authors), 1)
            self.assertIn('first_name', authors[0])
            self.assertIn('last_name', authors[0])
            self.assertIn('_id', authors[0])
            self.assertIn('$oid', authors[0]['_id'])
            self.assertEqual(authors[0], author)

    def test_author_get_not_found(self):
        with self.app.test_client() as c:
            rv = c.get('/authors/' + 'xyz')

            self.assert_code(rv.status_code, 404)

    def test_author_get_valid(self):
        author = self.insert_author()

        with self.app.test_client() as c:
            rv = c.get('/authors/' + author['_id']['$oid'])

            r_author = safe_decode(rv.data)

            self.assertIsNotNone(r_author)
            self.assertIn('first_name', r_author)
            self.assertIn('last_name', r_author)
            self.assertIn('_id', r_author)
            self.assertIn('$oid', r_author['_id'])
            self.assertEqual(author, r_author)

    def test_author_patch_not_found(self):
        with self.app.test_client() as c:
            rv = c.patch('/authors/' + 'xyz', data=json.dumps(self.default_author()))

            self.assert_code(rv.status_code, 404)

    def test_author_patch_invalid_field(self):
        with self.app.test_client() as c:
            rv = c.patch('/authors/' + 'xyz', data=json.dumps({'extra': 5}))

            self.assert_code(rv.status_code, 400)

    def test_author_patch_valid(self):
        author = self.insert_author()
        author['last_name'] = 'Baz'

        with self.app.test_client() as c:
            rv = c.patch('/authors/' + author['_id']['$oid'],
                    data=json.dumps({'last_name': author['last_name']}))

            self.assert_code(rv.status_code, 200)

            r_author = safe_decode(rv.data)

            self.assertIsNotNone(r_author)
            self.assertIn('first_name', r_author)
            self.assertIn('last_name', r_author)
            self.assertIn('_id', r_author)
            self.assertIn('$oid', r_author['_id'])
            self.assertEqual(author, r_author)

    def test_author_delete_not_found(self):
        with self.app.test_client() as c:
            rv = c.delete('/authors/' + 'xyz')

            self.assert_code(rv.status_code, 404)

    def test_author_delete_found(self):
        author = self.insert_author()

        with self.app.test_client() as c:
            rv = c.delete('/authors/' + author['_id']['$oid'])

            self.assert_code(rv.status_code, 200)

        with self.app.app_context() as c:
            found = self.mongo.db.authors.find_one(
                {'_id': safe_object_id(author['_id']['$oid'])})

            self.assertIsNone(found)

    def test_posts_post_invalid_data(self):
        with self.app.test_client() as c:
            rv = c.post('/posts', data='somestring')

            self.assert_code(rv.status_code, 400)

    def test_posts_post_missing_field(self):
        with self.app.test_client() as c:
            rv = c.post('/posts', data=json.dumps({'author': 'Missing'}))

            self.assert_code(rv.status_code, 400)

    def test_posts_post_extra_field(self):
        with self.app.test_client() as c:
            rv = c.post('/authors', data=json.dumps({'author': self.default_author(),
                    'title': 'Default Title', 'content': 'Descriptive content.',
                    'date': self.default_date(), 'extra': 3}))

            self.assert_code(rv.status_code, 400)

    def test_posts_post_valid(self):
        author = self.insert_author()
        with self.app.test_client() as c:
            post = self.default_post(author['_id']['$oid'])

            rv = c.post('/posts', data=json.dumps(post))

            self.assert_code(rv.status_code, 200)

            post = safe_decode(rv.data)

            self.assertIsNotNone(post)
            self.assertIn('author_id', post)
            self.assertIn('title', post)
            self.assertIn('content', post)
            self.assertIn('date', post)
            self.assertIn('_id', post)
            self.assertIn('$oid', post['_id'])
            self.assertEqual(post['author_id'], author['_id']['$oid'])
            self.assertEqual(post['title'], self.default_post(author['_id'])['title'])
            self.assertEqual(post['content'], self.default_post(author['_id'])['content'])
            self.assertEqual(post['date'], self.default_post(author['_id'])['date'])

    def test_posts_post_no_author(self):
        author = self.insert_author()
        with self.app.test_client() as c:
            post = self.default_post(author['_id'])

            rv = c.post('/posts', data=json.dumps(post))

            self.assert_code(rv.status_code, 400)

    def test_posts_get_one_post_valid(self):
        post = self.insert_post()

        with self.app.test_client() as c:
            rv = c.get('/posts')

            self.assert_code(rv.status_code, 200)

            posts = safe_decode(rv.data)

            self.assertEqual(len(posts), 1)
            self.assertIn('author_id', posts[0])
            self.assertIn('title', posts[0])
            self.assertIn('content', posts[0])
            self.assertIn('date', posts[0])
            self.assertIn('_id', posts[0])
            self.assertIn('$oid', posts[0]['_id'])
            self.assertEqual(posts[0], post)

    def test_post_get_not_found(self):
        with self.app.test_client() as c:
            rv = c.get('/posts/' + 'xyz')

            self.assert_code(rv.status_code, 404)

    def test_post_get_valid(self):
        post = self.insert_post()

        with self.app.test_client() as c:
            rv = c.get('/posts/' + post['_id']['$oid'])

            r_post = safe_decode(rv.data)

            self.assertIsNotNone(r_post)
            self.assertIn('author_id', r_post)
            self.assertIn('title', r_post)
            self.assertIn('content', r_post)
            self.assertIn('date', r_post)
            self.assertIn('_id', r_post)
            self.assertIn('$oid', r_post['_id'])
            self.assertEqual(post, r_post)

    def test_post_patch_not_found(self):
        author = self.insert_author()
        with self.app.test_client() as c:
            rv = c.patch('/posts/' + 'xyz', data=json.dumps(self.default_post(author['_id'])))

            self.assert_code(rv.status_code, 404)

    def test_post_patch_invalid_field(self):
        with self.app.test_client() as c:
            rv = c.patch('/posts/' + 'xyz', data=json.dumps({'extra': 5}))

            self.assert_code(rv.status_code, 400)

    def test_post_patch_valid(self):
        post = self.insert_post()
        post['title'] = 'Updated Title'

        with self.app.test_client() as c:
            rv = c.patch('/posts/' + post['_id']['$oid'],
                    data=json.dumps({'title': post['title']}))

            self.assert_code(rv.status_code, 200)

            r_post = safe_decode(rv.data)

            self.assertIsNotNone(r_post)
            self.assertIn('author_id', r_post)
            self.assertIn('title', r_post)
            self.assertIn('content', r_post)
            self.assertIn('date', r_post)
            self.assertIn('_id', r_post)
            self.assertIn('$oid', r_post['_id'])
            self.assertEqual(post, r_post)

    def test_post_delete_not_found(self):
        with self.app.test_client() as c:
            rv = c.delete('/posts/' + 'xyz')

            self.assert_code(rv.status_code, 404)

    def test_post_delete_found(self):
        post = self.insert_post()

        with self.app.test_client() as c:
            rv = c.delete('/posts/' + post['_id']['$oid'])

            self.assert_code(rv.status_code, 200)

        with self.app.app_context() as c:
            found = self.mongo.db.posts.find_one(
                {'_id': safe_object_id(post['_id']['$oid'])})

            self.assertIsNone(found)

    def test_email_post_valid(self):
        author = self.insert_author()

        with self.app.test_client() as c:
            rv = c.post('/login', data=json.dumps({'email':author ['email']}))

            self.assert_code(rv.status_code, 200)

            r_author = safe_decode(rv.data)

            self.assertIsNotNone(author)
            self.assertIn('first_name', author)
            self.assertIn('last_name', author)
            self.assertIn('email', author)
            self.assertIn('_id', author)
            self.assertIn('$oid', author['_id'])
            self.assertEqual(author['first_name'], 'Foo')
            self.assertEqual(author['last_name'], 'Bar')
            self.assertEqual(author['email'], 'foobar@gmail.com')

    def test_email_post_invalid(self):
        with self.app.test_client() as c:
            rv = c.post('/login', data=json.dumps({'email': 'fake_email@yahoo.com'}))
            self.assert_code(rv.status_code, 404)

    def tearDown(self):
        with self.app.app_context() as c:
            self.mongo.db.posts.delete_many({})
            self.mongo.db.authors.delete_many({})


if __name__ == '__main__':
    unittest.main()
