from __future__ import annotations

import tornado.ioloop
import tornado.web
import tornado.websocket

from botc.routes import http_routes, ws_routes


def make_app(debug=True):
    return tornado.web.Application(
        http_routes() + ws_routes(),
        debug=debug,
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8765)
    print("Server on http://localhost:8765")
    tornado.ioloop.IOLoop.current().start()
