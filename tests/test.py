import unittest
from unittest.mock import Mock, patch
from src.main import (
    share_phone_number_handler,
    registration_handler,
    search_for_tickets_handler,
    select_tickets_handler,
    admin_search_handler
)
from src.Redis import RedisClient
from src.CouchDB import CouchDBClient
from src.PostgreSQL import PostgreSQLDatabase


class TestTelegramBot(unittest.TestCase):
    @patch('main.usersDB.execute_read_query')
    @patch('main.sessionDB.set_hash')
    async def test_share_phone_number_handler(self, mock_set_hash, mock_execute_read_query):
        # Mocking the necessary objects and functions
        mock_message = Mock()
        mock_message.contact.phone_number = '+1234567890'
        mock_message.from_user.id = 123

        mock_execute_read_query.return_value = [(True,)]  # Assuming the phone number exists in the database

        mock_state = Mock()

        # Running the function
        await share_phone_number_handler(mock_message, mock_state)

        # Asserting that the correct functions were called
        mock_set_hash.assert_called_once_with(123, 'phone', '+1234567890')
        mock_execute_read_query.assert_called_once_with(
            "SELECT EXISTS (SELECT 1 FROM users WHERE phone = '+1234567890')")

    @patch('main.usersDB.execute_query')
    @patch('main.sessionDB.set_hash')
    async def test_registration_handler(self, mock_set_hash, mock_execute_query):
        # Mocking the necessary objects and functions
        mock_message = Mock()
        mock_message.text = 'password'

        mock_state = Mock()
        mock_state.from_user.id = 123

        # Running the function
        await registration_handler(mock_message, mock_state)

        # Asserting that the correct functions were called
        mock_set_hash.assert_called_once_with(123, 'phone', mock_state.get_hash.return_value)
        mock_execute_query.assert_called_once_with(
            "UPDATE users SET password = 'password' WHERE phone = '" + mock_state.get_hash.return_value + "'")

    @patch('main.sessionDB.set_hash')
    @patch('main.usersDB.execute_read_query')
    async def test_share_phone_number_handler_existing_number(self, mock_execute_read_query, mock_set_hash):
        # Mocking the necessary objects and functions
        mock_message = Mock()
        mock_message.contact.phone_number = '+1234567890'
        mock_message.from_user.id = 123

        # Simulate an existing phone number in the database
        mock_execute_read_query.return_value = [(True,)]

        mock_state = Mock()

        # Running the function
        await share_phone_number_handler(mock_message, mock_state)

        # Asserting that the correct functions were called
        mock_set_hash.assert_called_once_with(123, 'phone', '+1234567890')
        mock_execute_read_query.assert_called_once_with(
            "SELECT EXISTS (SELECT 1 FROM users WHERE phone = '+1234567890')")

    @patch('main.usersDB.execute_read_query')
    @patch('main.sessionDB.get_hash')
    async def test_admin_search_handler_no_data(self, mock_get_hash, mock_execute_read_query):
        # Mocking the necessary objects and functions
        mock_message = Mock()
        mock_message.text = '+1234567890'

        # Simulate no data for the given phone number
        mock_get_hash.return_value = '+1234567890'
        mock_execute_read_query.return_value = ""

        mock_state = Mock()

        # Running the function
        await admin_search_handler(mock_message, mock_state)

        # Asserting that the correct functions were called
        mock_get_hash.assert_called_once_with(mock_message.text)
        mock_execute_read_query.assert_called_once_with("SELECT tickets FROM users WHERE phone = '+1234567890'")

    @patch('main.usersDB.execute_read_query')
    @patch('main.sessionDB.set_hash')
    async def test_share_phone_number_handler_nonexistent_number(self, mock_set_hash, mock_execute_read_query):
        # Mocking the necessary objects and functions
        mock_message = Mock()
        mock_message.contact.phone_number = '+9876543210'  # Assuming the phone number doesn't exist in the database
        mock_message.from_user.id = 456

        mock_execute_read_query.return_value = [(False,)]  # Simulating a non-existent phone number in the database

        mock_state = Mock()

        # Running the function
        await share_phone_number_handler(mock_message, mock_state)

        # Asserting that the correct functions were called
        mock_set_hash.assert_called_once_with(456, 'phone', '+9876543210')
        mock_execute_read_query.assert_called_once_with(
            "SELECT EXISTS (SELECT 1 FROM users WHERE phone = '+9876543210')")

    @patch('main.usersDB.execute_read_query')
    @patch('main.sessionDB.set_hash')
    async def test_share_phone_number_handler_exception(self, mock_set_hash, mock_execute_read_query):
        # Mocking the necessary objects and functions
        mock_message = Mock()
        mock_message.contact.phone_number = '+1234567890'
        mock_message.from_user.id = 123

        mock_execute_read_query.side_effect = Exception("Database error")  # Simulating a database exception

        mock_state = Mock()

        # Running the function
        await share_phone_number_handler(mock_message, mock_state)

        # Asserting that the correct functions were called
        mock_set_hash.assert_called_once_with(123, 'phone', '+1234567890')
        mock_execute_read_query.assert_called_once_with(
            "SELECT EXISTS (SELECT 1 FROM users WHERE phone = '+1234567890')")

    @patch('main.usersDB.execute_query')
    @patch('main.sessionDB.set_hash')
    async def test_registration_handler_invalid_message(self, mock_set_hash, mock_execute_query):
        # Mocking the necessary objects and functions
        mock_message = Mock()
        mock_message.text = None  # Simulating an invalid message with no text

        mock_state = Mock()
        mock_state.from_user.id = 789

        # Running the function
        await registration_handler(mock_message, mock_state)

        # Asserting that the functions should not be called with invalid input
        mock_set_hash.assert_not_called()
        mock_execute_query.assert_not_called()

    @patch('main.sessionDB.get_hash')
    @patch('main.sessionDB.set_hash')
    @patch('main.usersDB.execute_read_query')
    @patch('main.flightsDB.get_document')
    async def test_search_for_tickets_handler(self, mock_get_document, mock_execute_read_query, mock_set_hash,
                                              mock_get_hash):
        # Mocking the necessary objects and functions
        mock_message = Mock()
        mock_state = Mock()
        mock_state.from_user.id = 123

        mock_get_hash.return_value = 'departure'
        mock_message.text = 'arrival'

        # Set up the mock data for flights
        mock_get_document.return_value = {'flights': [{'departure': 'departure', 'arrival': 'arrival'}]}

        # Running the function
        await search_for_tickets_handler(mock_message, mock_state)

        # Asserting that the correct functions were called
        mock_set_hash.assert_called_once_with(123, 'data', 'departure')
        mock_get_document.assert_called_once_with('flights', mock_set_hash.return_value)
        mock_execute_read_query.assert_not_called()  # Modify this based on your actual implementation

    @patch('main.sessionDB.set_hash')
    @patch('main.usersDB.execute_query')
    @patch('main.flightsDB.get_document')
    async def test_select_tickets_handler(self, mock_get_document, mock_execute_query, mock_set_hash):
        # Mocking the necessary objects and functions
        mock_message = Mock()
        mock_state = Mock()
        mock_state.from_user.id = 123
        mock_message.text = '1'  # Assuming the user selects the first ticket

        # Set up the mock data for flights
        mock_get_document.return_value = {'flights': [{'departure': 'departure', 'arrival': 'arrival'}]}

        # Running the function
        await select_tickets_handler(mock_message, mock_state)

        # Asserting that the correct functions were called
        mock_set_hash.assert_called_once_with(123, 'data', 'departure')
        mock_set_hash.assert_called_once_with(123, 'data1', 'arrival')
        mock_execute_query.assert_called_once()  # Modify this based on your actual implementation


class TestRedisClient(unittest.TestCase):
    def setUp(self):
        self.redis_client = RedisClient()

    def test_set_get_delete(self):
        key = "test_key"
        value = "test_value"

        # Test set
        self.redis_client.set(key, value)
        self.assertEqual(self.redis_client.get(key), value)

        # Test delete
        self.redis_client.delete(key)
        self.assertIsNone(self.redis_client.get(key))

    def test_set_hash_get_hash_delete_hash(self):
        hash_name = "test_hash"
        key = "test_key"
        value = "test_value"

        # Test set_hash
        self.redis_client.set_hash(hash_name, key, value)
        self.assertEqual(self.redis_client.get_hash(hash_name, key), value)

        # Test delete_hash_key
        self.redis_client.delete_hash_key(hash_name, key)
        self.assertIsNone(self.redis_client.get_hash(hash_name, key))

        # Test delete_hash
        self.redis_client.set_hash(hash_name, key, value)
        self.redis_client.delete_hash(hash_name)
        self.assertIsNone(self.redis_client.get_hash(hash_name, key))

    @patch('redis.Redis')
    def test_init_with_custom_host_and_port(self, mock_redis):
        host = 'custom_host'
        port = 1234

        RedisClient(host=host, port=port)

        # Assert that the Redis client is initialized with the correct host and port
        mock_redis.assert_called_once_with(host=host, port=port, decode_responses=True)


class TestCouchDBClient(unittest.TestCase):
    def setUp(self):
        self.couchdb_client = CouchDBClient()

    def test_create_and_delete_database(self):
        db_name = "test_database"

        # Test create_database
        create_response = self.couchdb_client.create_database(db_name)
        self.assertTrue(create_response.get('ok'))

        # Test delete_database
        delete_response = self.couchdb_client.delete_database(db_name)
        self.assertTrue(delete_response.get('ok'))

    @patch('requests.Session.post')
    def test_create_document_with_mocked_response(self, mock_post):
        db_name = "test_database"
        document = {"key": "value"}

        # Mock the post method to return a specific response
        mock_post.return_value.json.return_value = {"ok": True}

        # Test create_document
        create_response = self.couchdb_client.create_document(db_name, document)
        self.assertTrue(create_response.get('ok'))


class TestPostgreSQLDatabase(unittest.TestCase):
    def setUp(self):
        self.postgres = PostgreSQLDatabase(db_name='users', db_user='postgres', db_password='postgres')
        self.postgres.connect()

    def tearDown(self):
        self.postgres.execute_query("DROP TABLE IF EXISTS users")
        self.postgres.conn.close()

    def test_connection(self):
        self.assertIsNotNone(self.postgres.conn)

    def test_create_table(self):
        # Assuming connect() also creates the table, you can add a check for the table existence.
        table_check = self.postgres.execute_read_query(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')")
        self.assertTrue(table_check[0][0])

    def test_insert_and_select_data(self):
        # Insert a record
        self.postgres.execute_query("INSERT INTO users (phone, password) VALUES ('123456789', 'test123')")

        # Select the inserted record
        result = self.postgres.execute_read_query("SELECT * FROM users WHERE phone = '123456789'")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], '123456789')  # Assuming phone is in the second column


if __name__ == '__main__':
    unittest.main()