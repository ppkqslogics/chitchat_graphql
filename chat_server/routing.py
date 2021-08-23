from django.conf.urls import url
from django.urls import path

from chat_server import webConsumers
from CHITCHAT_API.consumers import MyGraphqlWsConsumer

websocket_urlpatterns = [
    url(r'^ws/chat/(?P<current_user>[^/]+)/(?P<room_name>[^/]+)/$', webConsumers.ChatConsumer.as_asgi()),
    path('graphql/', MyGraphqlWsConsumer.as_asgi())

]