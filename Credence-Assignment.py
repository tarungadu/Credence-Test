import http.server
import socketserver
from typing import Tuple
from http import HTTPStatus
from urllib.parse import urlparse, parse_qs
from pymongo import MongoClient
from bson import json_util

client = MongoClient()
client = MongoClient('mongodb://127.0.0.1:27017/')

db = client.local

movies = db.movies


class Handler(http.server.SimpleHTTPRequestHandler):

    def get_item(self, id):
        item = movies.find_one({"id": id})
        return item

    def add_item(self, item):
        response = movies.insert_one(item)
        return response

    def update_item(self, item):
        response = movies.update_one({"id": item.get("id")}, {"$set": item})
        return response

    def delete_item(self, item):
        response = movies.delete_one({"id": item.get("id")})
        return response

    def do_GET(self):
        path, query, body = self.decode_path()
        if path == '/':
            item = self.get_item(query.get('id')[0])
            self.respond_with_json(item)

    def do_POST(self):
        path, query, body = self.decode_path()
        if path == '/':
            response = self.add_item(body.get('item'))
            self.respond_with_json({"insertedId": str(response.inserted_id)})
        elif path == '/update':
            response = self.update_item(body.get('item'))
            self.respond_with_json({"modifiedCount": response.modified_count})
        elif path == '/delete':
            response = self.delete_item(body.get('item'))
            self.respond_with_json({"deletedCount": response.deleted_count})

    def decode_path(self):
        # Get the path string
        parsed_path = urlparse(self.path)

        # Get query as dict
        query = parse_qs(parsed_path.query)

        # Get body as dict
        content_len = int(self.headers.get('content-length')
                          ) if self.headers.get('content-length') else 0
        post_body = self.rfile.read(content_len)
        parsed_body = json_util.loads(post_body) if post_body else {}

        return parsed_path.path, query, parsed_body

    def respond_with_json(self, item):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            bytes(json_util.dumps(item).encode()))

    def __init__(self, request: bytes, client_address: Tuple[str, int], server: socketserver.BaseServer):
        super().__init__(request, client_address, server)


if __name__ == "__main__":
    PORT = 8000
    # Create an object of the above class
    my_server = socketserver.TCPServer(("0.0.0.0", PORT), Handler)
    # Star the server
    print(f"Server started at {PORT}")
    my_server.serve_forever()