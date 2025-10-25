from django.urls import path
from pos_app import consumers

websocket_urlpatterns = [
    path('ws/socket-server/', consumers.POSConsumer.as_asgi()),
]
