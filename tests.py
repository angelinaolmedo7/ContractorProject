"""RanchoStop tests."""
from unittest import TestCase, main as unittest_main, mock
from app import app
from datetime import datetime
from bson.objectid import ObjectId

sample_listing_id = ObjectId('5d55cffc4a3d4031f42827a3')
sample_listing = {
    'title': 'Cool listing',
    'description': 'Buy my Rancho.',
    'views': 0,
    'created_at': datetime.now(),
    'author': 'Tahoe',
    'user_id': ObjectId('6d55cffc4a3d4031f42827a4')
}
sample_form_data = {
    'title': 'new title',
    'description': sample_listing['description']
}


class RanchoStopTests(TestCase):
    """Flask tests."""

    def setUp(self):
        """Do before every test."""
        # Get the Flask test client
        self.client = app.test_client()

        # Show Flask errors that happen during tests
        app.config['TESTING'] = True

    def test_index(self):
        """Test the RanchoStop homepage."""
        result = self.client.get('/')
        self.assertEqual(result.status, '200 OK')
        self.assertIn(b'RanchoStop', result.data)

    def test_new_listing(self):
        """Test the new listing creation page."""
        result = self.client.get('/ranchos/new')
        self.assertEqual(result.status, '200 OK')
        self.assertIn(b'New Listing', result.data)

    def test_user_dir(self):
        """Test the RanchoStop user directory."""
        result = self.client.get('/users/directory')
        self.assertEqual(result.status, '200 OK')
        self.assertIn(b'RanchoStop', result.data)

    def test_new_user(self):
        """Test the new user creation page."""
        result = self.client.get('/users/new')
        self.assertEqual(result.status, '200 OK')
        self.assertIn(b'New User', result.data)

    @mock.patch('pymongo.collection.Collection.find_one')
    def test_show_listing(self, mock_find):
        """Test showing a single listing."""
        mock_find.return_value = sample_listing

        result = self.client.get(f'/ranchos/{sample_listing_id}')
        self.assertEqual(result.status, '200 OK')
        self.assertIn(b'Buy my Rancho.', result.data)

    @mock.patch('pymongo.collection.Collection.find_one')
    def test_edit_listing(self, mock_find):
        """Test editing a single listing."""
        mock_find.return_value = sample_listing

        result = self.client.get(f'/ranchos/{sample_listing_id}/edit')
        self.assertEqual(result.status, '200 OK')
        self.assertIn(b'Edit Listing', result.data)

    @mock.patch('pymongo.collection.Collection.insert_one')
    def test_submit_listing(self, mock_insert):
        """Test submitting a new listing."""
        result = self.client.post('/listings', data=sample_form_data)

        # After submitting, should redirect to that listing's page
        self.assertEqual(result.status, '302 FOUND')
        mock_insert.assert_called_with(sample_rancho)

    @mock.patch('pymongo.collection.Collection.update_one')
    def test_update_listing(self, mock_update):
        """Test updating a listing."""
        result = self.client.post(f'/listings/{sample_listing_id}',
                                  data=sample_form_data)

        self.assertEqual(result.status, '302 FOUND')
        mock_update.assert_called_with({'_id': sample_listing_id},
                                       {'$set': sample_listing})

    @mock.patch('pymongo.collection.Collection.delete_one')
    def test_delete_listing(self, mock_delete):
        """Test deleting a listing."""
        form_data = {'_method': 'DELETE'}
        result = self.client.post(f'/listings/{sample_listing_id}/delete',
                                  data=form_data)
        self.assertEqual(result.status, '302 FOUND')
        mock_delete.assert_called_with({'_id': sample_listing_id})


if __name__ == '__main__':
    unittest_main()
