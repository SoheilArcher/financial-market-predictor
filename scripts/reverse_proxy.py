from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


TARGET_HOST = "127.0.0.1"
TARGET_PORT = 8000
HOP_BY_HOP = {
    "connection",
    "content-length",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        self._proxy()

    def do_POST(self):
        self._proxy()

    def do_PUT(self):
        self._proxy()

    def do_PATCH(self):
        self._proxy()

    def do_DELETE(self):
        self._proxy()

    def do_OPTIONS(self):
        self._proxy()

    def do_HEAD(self):
        self._proxy(send_body=False)

    def _proxy(self, send_body=True):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP and key.lower() != "host"
        }
        headers["Host"] = self.headers.get("Host", "51.83.160.143")
        headers["X-Forwarded-For"] = self.client_address[0]
        headers["X-Forwarded-Proto"] = "http"
        conn = HTTPConnection(TARGET_HOST, TARGET_PORT, timeout=60)
        try:
            conn.request(self.command, self.path, body=body, headers=headers)
            response = conn.getresponse()
            data = response.read() if send_body else b""
            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                if key.lower() not in HOP_BY_HOP:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.end_headers()
            if send_body:
                self.wfile.write(data)
            self.close_connection = True
        except Exception as exc:
            message = f"Proxy error: {exc}".encode()
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(message)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(message)
            self.close_connection = True
        finally:
            conn.close()


class NexTradeHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 128


if __name__ == "__main__":
    server = NexTradeHTTPServer(("0.0.0.0", 80), ProxyHandler)
    server.serve_forever()
