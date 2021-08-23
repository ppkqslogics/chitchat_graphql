from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import chat_server.routing

application = ProtocolTypeRouter(
    {
        'websocket': (
            URLRouter(
                chat_server.routing.websocket_urlpatterns
            )
        )
    }
)