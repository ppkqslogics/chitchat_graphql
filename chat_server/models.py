from datetime import datetime
from djongo import models

class TrackingModel(models.Model):
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(models.Model):
    chit_chat_id = models.CharField(max_length=255)
    user_contact_id = models.CharField(primary_key=True, max_length=255)
    user_name = models.CharField(max_length=255)
    user_photo = models.CharField(max_length=255)
    user_phone = models.CharField(max_length=255)


class PintopUser(models.Model):
    user_contact_id = models.CharField(max_length=255)

    class Meta:
        abstract = True


class ReactionUser(models.Model):
    user_contact_id = models.CharField(max_length=255)
    reaction = models.CharField(max_length=255)

    class Meta:
        abstract = True


class BackgroundUser(models.Model):
    user_contact_id = models.CharField(max_length=255)
    background_url = models.URLField()
    bg_type = models.TextField()

    class Meta:
        abstract = True


class RepliedMessage(models.Model):
    replied_id = models.CharField(max_length=255)
    replied_text = models.TextField()
    replied_lat = models.TextField()
    replied_long = models.TextField()
    replied_sender = models.CharField(max_length=255)

    class Meta:
        abstract = True


class ChatRoom(models.Model):
    THREAD_TYPE = (
        ('private', 'Private'),
        ('group', 'Group')
    )
    id = models.AutoField(primary_key=True)
    room_name = models.CharField(max_length=255, null=True)
    room_photo = models.CharField(max_length=255, null=True)
    thread_type = models.CharField(max_length=15, choices=THREAD_TYPE, default='private')
    last_message_id = models.CharField(max_length=255, null=True)
    last_message = models.TextField(null=True)
    last_message_timestamp = models.CharField(max_length=255, null=True)
    participants = models.ArrayField(
        model_container=User
    )
    pin_top = models.ArrayField(
        model_container=PintopUser, null=True
    )
    deleted_by = models.ArrayField(
        model_container=PintopUser, null=True
    )
    backgrounds = models.ArrayField(
        model_container=BackgroundUser, null=True
    )



def message_id():
    return str(round(datetime.now().timestamp() * 1000))


class Message(models.Model):
    message_id = models.CharField(primary_key=True, max_length=255, default=message_id)
    message = (models.TextField(null=True))
    contact_message = models.ArrayField(model_container=User, null=True)
    message_type = models.CharField(max_length=255)
    sender = models.CharField(max_length=255)
    timestamp = models.CharField(max_length=255)
    lat = models.FloatField(default=0)
    long = models.FloatField(default=0)
    file_name = models.CharField(max_length=255, null=True)
    file_size = models.CharField(max_length=255, null=True)
    favourite = models.ArrayField(
        model_container=PintopUser, null=True
    )
    room_id = models.CharField(max_length=255)
    forwarded_by = models.ArrayField(
        model_container=PintopUser, null=True
    )
    reply_type = models.TextField(null=True)
    replied_message = (models.ArrayField(
        model_container=RepliedMessage, null=True))
    reaction_info = models.ArrayField(
        model_container=ReactionUser, null=True
    )
    deleted_by = models.ArrayField(
        model_container=PintopUser, null=True
    )
