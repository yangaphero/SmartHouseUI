import json
import time
from collections import namedtuple

from kivy.logger import Logger as log
import websocket
from queue import Queue
from threading import Thread

Message = namedtuple('Message', 'body, persistent')


class LightController:
    def __init__(self, host, port, debug=False):
        self._host = host
        self._port = port
        self._debug = debug
        self._message_queue = Queue()
        self._client = None
        self._srv_thread = None
        self._pusher_thread = None
        self._have_connection = False

    def on_message(self, message):
        log.info('WebSocket message: %s', message)

    def on_error(self, error):
        log.error('WebSocket error: %s', error)

    def on_close(self):
        log.info('WebSocket disconnected')
        self._have_connection = False

    def on_open(self):
        log.info('WebSocket connected')
        self._have_connection = True

    def _message_pusher(self):
        while True:
            try:
                message: Message = self._message_queue.get()

                if not self._have_connection:
                    if message.persistent:
                        self._message_queue.put(message)
                        time.sleep(1)

                    continue

                try:
                    text = (
                        json.dumps(message.body)
                        if isinstance(message.body, dict)
                        else message.body
                    )
                    self._client.send(text)
                except Exception:
                    # Didn't work, let's put the message back
                    if message.persistent:
                        self._message_queue.put(message)

                    raise

            except Exception:
                log.exception('WebSocket message pusher error')
                time.sleep(1)

    def _server_runner(self):
        while True:
            try:
                # Forever heree actually means "until the first error"
                self._client.run_forever()
                time.sleep(1)

            except Exception:
                log.exception('Error in WebSocket server main thread, reconnecting')

    def start(self):
        websocket.enableTrace(self._debug)

        self._pusher_thread = Thread(target=self._message_pusher, daemon=True)
        self._pusher_thread.start()

        self._client = websocket.WebSocketApp(
            f'ws://{self._host}:{self._port}/',
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )

        self._srv_thread = Thread(target=self._server_runner, daemon=True)
        self._srv_thread.start()

    def send(self, body, persistent=False):
        self._message_queue.put(Message(body, persistent))
