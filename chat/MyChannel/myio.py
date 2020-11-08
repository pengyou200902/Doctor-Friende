import logging
import uuid
import time

from typing import Any, Awaitable, Callable, Dict, Union, List, Optional, Text

from rasa.core.channels.channel import InputChannel, OutputChannel, UserMessage
from rasa.core.channels.socketio import SocketBlueprint, SocketIOOutput
import rasa.shared.utils.io

from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from socketio import AsyncServer
from . import MyUtils


logger = logging.getLogger(__name__)


class MySocketIOInput(InputChannel):
    """A socket.io input channel."""

    @classmethod
    def name(cls) -> Text:
        return "socketio"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
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
        self.sio = None
        self.remote_addr = remote_addr
        self.cors_allowed_origins = cors_allowed_origins

    def get_output_channel(self) -> Optional["OutputChannel"]:
        if self.sio is None:
            rasa.shared.utils.io.raise_warning(
                "SocketIO output channel cannot be recreated. "
                "This is expected behavior when using multiple Sanic "
                "workers or multiple Rasa Open Source instances. "
                "Please use a different channel for external events in these "
                "scenarios."
            )
            return
        return SocketIOOutput(self.sio, self.bot_message_evt)

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[Any]]
    ) -> Blueprint:
        # Workaround so that socketio works with requests from other origins.
        # https://github.com/miguelgrinberg/python-socketio/issues/205#issuecomment-493769183
        sio = AsyncServer(async_mode="sanic", cors_allowed_origins=self.cors_allowed_origins)
        socketio_webhook = SocketBlueprint(
            sio, self.socketio_path, "socketio_webhook", __name__
        )

        # make sio object static to use in get_output_channel
        self.sio = sio

        @socketio_webhook.route("/", methods=["GET"])
        async def health(_: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @sio.on("connect", namespace=self.namespace)
        async def connect(sid: Text, environ) -> None:
            ip = environ['REMOTE_ADDR'] or environ['HTTP_X_FORWARDED_FOR']
            self.remote_addr = ip
            self.c = MyUtils.get_record_db_cursor()
            logger.debug(f"User {sid} (from {ip}) connected to socketIO endpoint.")

        @sio.on("disconnect", namespace=self.namespace)
        async def disconnect(sid: Text) -> None:
            self.c.connection.close()
            logger.debug(f"User {sid} disconnected from socketIO endpoint.")

        @sio.on("session_request", namespace=self.namespace)
        async def session_request(sid: Text, data: Optional[Dict]):
            if data is None:
                data = {}
            if "session_id" not in data or data["session_id"] is None:
                data["session_id"] = uuid.uuid4().hex
            if self.session_persistence:
                sio.enter_room(sid, data["session_id"])
            await sio.emit("session_confirm", data["session_id"], room=sid)
            logger.debug(f"User {sid} connected to socketIO endpoint.")

        @sio.on(self.user_message_evt, namespace=self.namespace)
        async def handle_message(sid: Text, data: Dict) -> Any:
            output_channel = SocketIOOutput(sio, self.bot_message_evt)

            if self.session_persistence:
                if not data.get("session_id"):
                    rasa.shared.utils.io.raise_warning(
                        "A message without a valid session_id "
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

                logger.debug(f"from_user_id={data['customData']['from_user_id']}, "
                             f"session_id={data['session_id']}, "
                             f"content={data['message']}, "
                             f"ip_address={self.remote_addr}")

                query = """insert into message_received
                    (from_user_id, session_id, content, `when`, ip_address)
                    values (%s, %s, %s, %s, %s)"""
                try:
                    self.c.execute(query, (data["customData"]["from_user_id"],
                                           data["session_id"],
                                           data["message"],
                                           time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                           self.remote_addr))
                    self.c.connection.commit()
                    logger.debug("self.c.connection.commit()")
                except Exception as e:
                    logger.error(e)
            await on_new_message(message)

        return socketio_webhook