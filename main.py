import json
import logging
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
from threading import Thread

Base_DIR = pathlib.Path()
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000
BUFFER = 1024

def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SERVER_IP, SERVER_PORT))
    client_socket.close()

class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-length']))
        send_data_to_socket(body)

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html_file('index.html')
            case '/message':
                self.send_html_file('message.html')
            case _:
                file = Base_DIR/route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file('404.html',404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(200)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

def run(server_class = HTTPServer, handler_class = HttpHandler):
    server_address = ('0.0.0.0', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def save_data(data):
    body = urllib.parse.unquote(data.decode())
    try:
        payload = {key: value for key, value in [el.split('=') for el in body.split('&')]}
        try:
            with open(Base_DIR.joinpath('data/data.json')) as file:
                existing_data = json.load(file)
                if not isinstance(existing_data, list):
                    existing_data = []
        except FileNotFoundError:
            existing_data = []

        existing_data.append(payload)

        with open(Base_DIR.joinpath('data/data.json'), 'w', encoding='utf-8') as fd:
            json.dump(existing_data, fd, ensure_ascii=False, indent=4)

        logging.info('Дані успішно додано до JSON-файлу.')
    except ValueError as err:
        logging.error(f'Помилка при обробці даних {body} з помилкою {err}')
    except OSError as err:
        logging.error(f'Помилка при обробці даних {body} з помилкою {err}')




def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    try:
        while True:
            data, address = server_socket.recvfrom(BUFFER)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server stopped')
    finally:
        server_socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(threadName)s %(message)s')
    STORAGE_DIR = pathlib.Path().joinpath('data')
    FILE_STORAGE = STORAGE_DIR / 'data.json'
    if not FILE_STORAGE.exists():
        with open(FILE_STORAGE, 'w', encoding='utf-8') as fd:
            json.dump({}, fd, ensure_ascii=False)

    tread_server = Thread(target = run)
    tread_server.start()

    tread_socket = Thread(target = run_socket_server(SERVER_IP, SERVER_PORT))
    tread_socket.start()


