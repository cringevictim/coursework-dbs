import requests


class CouchDBClient:
    def __init__(self, base_url='http://couchdb:5984', username='couchdb', password='couchdb'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.auth = (username, password)

    def create_database(self, db_name):
        response = self.session.put(f"{self.base_url}/{db_name}")
        return response.json()

    def delete_database(self, db_name):
        response = self.session.delete(f"{self.base_url}/{db_name}")
        return response.json()

    def clear_database(self, db_name):
        response = self.session.get(f"{self.base_url}/{db_name}/_all_docs")
        doc_ids = response.json().get("rows", [])

        for row in doc_ids:
            doc_id = row.get("id")
            rev = row.get("value").get("rev")
            self.delete_document(db_name, doc_id, rev)

    def create_document(self, db_name, document):
        response = self.session.post(f"{self.base_url}/{db_name}", json=document)
        return response.json()

    def get_document(self, db_name, doc_id):
        response = self.session.get(f"{self.base_url}/{db_name}/{doc_id}")
        return response.json()

    def update_document(self, db_name, doc_id, document):
        response = self.session.put(f"{self.base_url}/{db_name}/{doc_id}", json=document)
        return response.json()

    def delete_document(self, db_name, doc_id, rev):
        response = self.session.delete(f"{self.base_url}/{db_name}/{doc_id}", params={"rev": rev})
        return response.json()

    def push_example_data(self, db_name):
        flights = {
            "flights": [
                {
                    "departure": "1",
                    "arrival": "2",
                    "departure_time": "2023.01.01T08:00:00",
                    "arrival_time": "2023.01.01T12:00:00",
                    "seats_total": "100",
                    "seats_left": "50"
                },
                {
                    "departure": "New York",
                    "arrival": "Los Angeles",
                    "departure_time": "2026.01.01T08:00:00",
                    "arrival_time": "2026.01.01T12:00:00",
                    "seats_total": "100",
                    "seats_left": "50"
                },
                {
                    "departure": "New York",
                    "arrival": "Los Angeles",
                    "departure_time": "2025.01.01T08:00:00",
                    "arrival_time": "2025.01.01T12:00:00",
                    "seats_total": "100",
                    "seats_left": "50"
                },
                {
                    "departure": "New York",
                    "arrival": "Los Angeles",
                    "departure_time": "2024.01.01T08:00:00",
                    "arrival_time": "2024.01.01T12:00:00",
                    "seats_total": "100",
                    "seats_left": "50"
                },
                {
                    "departure": "Los Angeles",
                    "arrival": "Chicago",
                    "departure_time": "2023.01.02T10:30:00",
                    "arrival_time": "2023.01.02T15:45:00",
                    "seats_total": "150",
                    "seats_left": "75"
                },
                {
                    "departure": "Chicago",
                    "arrival": "Houston",
                    "departure_time": "2023.01.03T14:15:00",
                    "arrival_time": "2023.01.03T18:30:00",
                    "seats_total": "120",
                    "seats_left": "60"
                },
                {
                    "departure": "Houston",
                    "arrival": "Miami",
                    "departure_time": "2023.01.04T09:45:00",
                    "arrival_time": "2023.01.04T14:00:00",
                    "seats_total": "200",
                    "seats_left": "100"
                },
                {
                    "departure": "Miami",
                    "arrival": "San Francisco",
                    "departure_time": "2023.01.05T12:30:00",
                    "arrival_time": "2023.01.05T16:45:00",
                    "seats_total": "180",
                    "seats_left": "90"
                }
            ]
        }

        return self.create_document(db_name, flights)['id']
