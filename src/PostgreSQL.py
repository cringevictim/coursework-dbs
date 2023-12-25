import psycopg2
from psycopg2 import sql


class PostgreSQLDatabase:
    def __init__(self, db_name, db_user, db_password, db_host='postgres', db_port=5432):
        self.conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    def fetch_one(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.fetchone()
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error fetching one: {e}")

    def fetch_all(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error fetching all: {e}")

    def create_table(self, table_name, columns):
        try:
            create_table_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(
                    sql.SQL("{} {}").format(sql.Identifier(column_name), sql.SQL(column_type))
                    for column_name, column_type in columns.items()
                )
            )
            self.cursor.execute(create_table_query)
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error creating table '{table_name}': {e}")

    def delete_table(self, table_name):
        try:
            delete_table_query = sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table_name))
            self.cursor.execute(delete_table_query)
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error deleting table '{table_name}': {e}")

    def insert_record(self, table_name, data):
        try:
            insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(sql.Identifier(column_name) for column_name in data.keys()),
                sql.SQL(', ').join(sql.Placeholder() for _ in data.values())
            )
            self.cursor.execute(insert_query, list(data.values()))
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error inserting a record(s): {e}")

    def update_record(self, table_name, data, where_clause):
        try:
            set_statements = [
                sql.SQL("{} = {}").format(sql.Identifier(column_name), sql.Placeholder())
                for column_name in data.keys()
            ]

            set_clause = sql.SQL(', ').join(set_statements)

            update_query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
                sql.Identifier(table_name),
                set_clause,
                sql.SQL(where_clause)  # Assuming 'where_clause' is already a valid SQL condition
            )

            self.cursor.execute(update_query, list(data.values()))
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error updating a record(s): {e}")

    def delete_records(self, table_name, where_clause):
        try:
            delete_query = sql.SQL("DELETE FROM {} WHERE {}").format(
                sql.Identifier(table_name),
                where_clause
            )
            self.cursor.execute(delete_query)
            self.conn.cursor()
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error deleting a record(s): {e}")

    def contains_record(self, table_name, record):
        where_clause = sql.SQL(" AND ").join(
            sql.SQL("{} = {}").format(sql.Identifier(column_name), sql.Placeholder())
            for column_name in record.keys()
        )

        select_query = sql.SQL("SELECT COUNT(*) FROM {} WHERE {}").format(
            sql.Identifier(table_name), where_clause
        )

        result = self.fetch_one(select_query, list(record.values()))

        return result[0] > 0
