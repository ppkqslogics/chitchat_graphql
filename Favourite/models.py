from django.db import models
from chat_server.models import TrackingModel

# Create your models here.

class FavouriteType(TrackingModel):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=500)