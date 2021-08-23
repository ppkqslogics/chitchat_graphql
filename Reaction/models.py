from django.db import models
from chat_server.models import TrackingModel

# Create your models here.

class Reaction(TrackingModel):
    id = models.AutoField(primary_key=True)
    emoji_value = models.CharField(max_length=255)
    emoji = models.CharField(max_length=255)