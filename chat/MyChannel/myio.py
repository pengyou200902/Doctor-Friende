import logging
import uuid
import time

from sanic import response
from sanic.request import Request
from socketio import AsyncServer
from typing import Optional, Text, Any, List, Dict, Union

from rasa.core.channels.socketio import SocketBlueprint, SocketIOOutput
from rasa.core.channels.channel import InputChannel, OutputChannel
from rasa.core.channels.channel import UserMessage
from . import MyUtils


logger = logging.getLogger(__name__)


class MySocketIOInput(InputChannel):
    """A socket.io input channel."""

    @classmethod
    def name(cls):
        return "socketio"

    @classmethod
    def from_credentials(cls, credentials):
        credentials = credentials or {}
        return cls(
            credentials.get("user_message_evt", "user_uttered"),
            credentials.get("bot_message_evt", "bot_uttered"),
            credentials.get("namespace"),
            credentials.get("session_persistence", False),
            credentials.get("socketio_path", "/mysocket.io"),
            credentials.get("cors_allowed_origins", "*"),
        )

    def __init__(
        self,
        user_message_evt: Text = "user_uttered",
        bot_message_evt: Text = "bot_uttered",
        namespace: Optional[Text] = None,
        session_persistence: bool = False,
        socketio_path: Optional[Text] = "/mysocket.io",
        remote_addr: Text = "unknown",
        cors_allowed_origins: Union[Text, List[Text]] = "*"
    ):
        logger.debug("This is PY's custom Websocket InputChannel.")
        self.bot_message_evt = bot_message_evt
        self.session_persistence = session_persistence
        self.user_message_evt = user_message_evt
        self.namespace = namespace
        self.socketio_path = socketio_path
        self.remote_addr = remote_addr
        self.cors_allowed_origins = cors_allowed_origins


    def blueprint(self, on_new_message):
        sio = AsyncServer(async_mode="sanic", cors_allowed_origins=self.cors_allowed_origins)
        socketio_webhook = SocketBlueprint(
            sio, self.socketio_path, "socketio_webhook", __name__
        )

        @socketio_webhook.route("/", methods=["GET"])
        async def health(request: Request):
            return response.json({"status": "ok"})

        @sio.on("connect", namespace=self.namespace)
        async def connect(sid, environ):
            ip = environ['REMOTE_ADDR'] or environ['HTTP_X_FORWARDED_FOR']
            self.remote_addr = ip
            self.c = MyUtils.get_record_db_cursor()
            logger.debug("User {} (from {}) connected to socketIO endpoint.".format(sid, ip))

        @sio.on("disconnect", namespace=self.namespace)
        async def disconnect(sid):

            self.c.connection.close()
            logger.debug("User {} disconnected from socketIO endpoint.".format(sid))

        @sio.on("session_request", namespace=self.namespace)
        async def session_request(sid, data):
            if data is None:
                data = {}
            if "session_id" not in data or data["session_id"] is None:
                data["session_id"] = uuid.uuid4().hex
            await sio.emit("session_confirm", data["session_id"], room=sid)
            logger.debug("User {} connected to socketIO endpoint.".format(sid))

        @sio.on(self.user_message_evt, namespace=self.namespace)
        async def handle_message(sid, data):
            output_channel = SocketIOOutput(sio, sid, self.bot_message_evt)
            logger.debug("Received data: {} ".format(data))

            if self.session_persistence:
                if not data.get("session_id"):
                    logger.warning(
                        "A message without a valid sender_id "
                        "was received. This message will be "
                        "ignored. Make sure to set a proper "
                        "session id using the "
                        "`session_request` socketIO event."
                    )
                    return
                sender_id = data["session_id"]
            else:
                sender_id = sid
            message = UserMessage(
                data["message"], output_channel, sender_id, input_channel=self.name()
            )
            if data["message"][0] != '/':
                query = """insert into message_received
                    (from_user_id, session_id, content, `when`, ip_address)
                    values (%s, %s, %s, %s, %s)"""
                self.c.execute(query, (data["customData"]["from_user_id"],
                                       data["session_id"],
                                       data["message"],
                                       time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                       self.remote_addr))
                self.c.connection.commit()
            await on_new_message(message)

        return socketio_webhook