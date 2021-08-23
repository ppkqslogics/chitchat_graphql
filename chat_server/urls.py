from django.urls import path
from django.conf.urls import url
from chat_server import views
urlpatterns = [
    path('', views.index, name='index'),
    url(r'^room/(?P<current_user>[^/]+)/(?P<room_id>[^/]+)/$', views.room)
]

