#!/usr/bin/env python3

from http.server import ThreadingHTTPServer
from http.server import SimpleHTTPRequestHandler
import os


HOST = "127.0.0.1"
PORT = 8000


os.chdir(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


server = ThreadingHTTPServer(
    (HOST, PORT),
    SimpleHTTPRequestHandler
)


print(
    f"[CLIENT] Server running at "
    f"http://{HOST}:{PORT}"
)


try:

    server.serve_forever()

except KeyboardInterrupt:

    print(
        "[CLIENT] Server stopped."
    )

finally:

    server.server_close()