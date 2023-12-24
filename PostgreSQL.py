import psycopg2
from psycopg2 import OperationalError, DatabaseError

class PostgreSQLDatabase:
    def __init__(self, db_name, db_user, db_password, db_host='localhost', db_port=5432):
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            self.execute_query("CREATE TABLE IF NOT EXISTS users (user_id SERIAL PRIMARY KEY, phone TEXT NOT NULL UNIQUE, password TEXT, is_admin BOOLEAN DEFAULT FALSE, tickets TEXT DEFAULT '-')")
            #self.execute_query("DROP TABLE users")
            print(self.execute_query("SELECT * FROM users"))
            print("aaaaaaaaaa")
        except OperationalError as e:
            print(f"The error '{e}' occurred")

    def insert_param_value(self, db, field, field_value, cond_field, cond_param):
       try:
           with self.conn.cursor() as cursor:
               cursor.execute(("UPDATE "+ db +" SET " + field + " = (?) WHERE " + cond_field + " = " + cond_param), field_value)
               self.conn.commit()
       except (OperationalError, DatabaseError) as e:
           print(f"The error '{e}' occurred")
           self.conn.rollback()

    def execute_query(self, query):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                self.conn.commit()
        except (OperationalError, DatabaseError) as e:
            print(f"The error '{e}' occurred")
            self.conn.rollback()

    def execute_read_query(self, query):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        except (OperationalError, DatabaseError) as e:
            print(f"The error '{e}' occurred")
