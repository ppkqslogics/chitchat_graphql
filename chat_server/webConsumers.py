import base64
import json
from datetime import datetime
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer, JsonWebsocketConsumer
from asgiref.sync import async_to_sync
import os
from CHITCHAT_API.settings import MONGO_CLIENT
import pyrebase
from chat_server.encryption import encrypt_message
from CHITCHAT_API.firebaseConfig import firebaseConfig

firebaseConfig = pyrebase.initialize_app(firebaseConfig)
storage = firebaseConfig.storage()


@database_sync_to_async
def save_to_database(db, collection, chat_message):
    r = MONGO_CLIENT[db][collection].insert_one(chat_message)
    print('inside save_to_database====>', r.inserted_id)
    return True, r.inserted_id


@database_sync_to_async
def update_last_message(db, collection, roomId, last_message, timestamp, message_id):
    print("Inside update last message: ", message_id)
    query = {"id": int(roomId)}
    newValue = {
        "$set": {"last_message": last_message, "last_message_timestamp": timestamp, "last_message_id": message_id}}
    r = MONGO_CLIENT[db][collection].find_one_and_update(query, newValue)
    return r

class EventConsumer(JsonWebsocketConsumer):
    def connect(self):
        print('inside Eventconsumer connect()')
        async_to_sync(self.channel_layer.group_add)(
            'events',
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        print('inside EventConsumer disconnect()')
        print("Closed websocket with code: ", close_code)
        async_to_sync(self.channel_layer.group_discard)(
            'events',
            self.channel_name
        )
        self.close()

    def receive_json(self, content, **kwargs):
        print('inside EventConsumer receive_json()')
        print("Received event: {}".format(content))
        self.send_json(content)

    def send_json(self, content, close=False):
        self.send_json(self=self,content=content)

    def events_alarm(self, event):
        print('inside EventConsumer events_alarm()')
        self.send_json(
            content=json.dumps(event)
        )


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.currentUser = self.scope['url_route']['kwargs']['current_user']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.channel_layer.group_add(
            'server_announcements',
            self.channel_name
        )
        await self.accept()

        chat_data = {
            'current_user': self.currentUser,
            'online': True,
            'type': 'chat_message'
        }
        await self.channel_layer.group_send(
            self.room_group_name,
            chat_data
        )


    async def disconnect(self, code):
        chat_data = {
            'current_user': self.currentUser,
            'online': False,
            'type': 'chat_message'}
        await self.channel_layer.group_send(
            self.room_group_name,
            chat_data
        )
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )



    async def receive(self, text_data):
        room_id = self.room_name
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message') or ''
        message_type = text_data_json.get('message_type')
        reply_type = text_data_json.get('reply_type')
        replied_message = [{'replied_id': text_data_json.get('replied_id'),
                            'replied_text': text_data_json.get('replied_text'),
                            'replied_lat': text_data_json.get('replied_lat'),
                            'replied_long': text_data_json.get('replied_long'),
                            'replied_sender': text_data_json.get('replied_sender')
                            }]
        forwarded_by = [{'user_contact_id': text_data_json.get('forwarded_by')}]
        typing = text_data_json.get('typing') or False
        file_type = text_data_json.get('file_type') or ""
        out_of_focus = text_data_json.get('outoffocus') or False
        lat = text_data_json.get('lat') or 0
        long = text_data_json.get('long') or 0
        online = text_data_json.get('online', True)
        forward = text_data_json.get('forward') or None
        message_id = self.room_name + self.currentUser + str(round(datetime.now().timestamp() * 1000))
        file_name = text_data_json.get('file_name') or ""
        file_size = text_data_json.get('file_size') or ""
        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        favourite = text_data_json.get('favourite') or ""
        sender_name = text_data_json.get('sender_name') or None

        if message_type == 'photo':
            waiting_data = {
                'type': 'chat_message',
                'message': '',
                'message_id': message_id,
                'sender': self.currentUser,
                'message_type': message_type,
                'timestamp': timestamp,
                'online': True,
                'lat': 0,
                'long': 0,
                'typing': typing,
                'outoffocus': out_of_focus,
                'room_id': room_id,
                'forwarded_by': forwarded_by,
                'reply_type': reply_type,
                'replied_message': replied_message,
                'favourite': None,
                'reaction_info': None,
                'remark': 'File is uploading'
            }
            await self.channel_layer.group_send(
                self.room_group_name, waiting_data
            )

            if forward is True:
                message = message

            elif favourite is True:
                message = message

            else:
                outfile = str(round(datetime.now().timestamp() * 1000)) + "." + file_type

                cloud_url = "Photo/" + room_id + outfile

                with open(outfile, "wb") as fh:
                    a = fh.write(base64.decodebytes(message.encode("utf-8")))
                if a > 0:
                    try:
                        storage.child(cloud_url).put(outfile)
                        message = storage.child(cloud_url).get_url(None)

                    except:

                        waiting_data.update({'remark': 'File upload failed'})
                        message = ''
                        await self.channel_layer.group_send(
                            self.room_group_name, waiting_data
                        )
                os.remove(outfile)

        elif message_type == 'voice' or message_type == 'audio':
            waiting_data = {
                'type': 'chat_message',
                'message': '',
                'message_id': message_id,
                'sender': self.currentUser,
                'message_type': message_type,
                'timestamp': timestamp,
                'online': True,
                'lat': 0,
                'long': 0,
                'typing': typing,
                'outoffocus': out_of_focus,
                'room_id': room_id,
                'forwarded_by': forwarded_by,
                'reply_type': reply_type,
                'replied_message': replied_message,
                'favourite': None,
                'reaction_info': None,
                'remark': 'File is uploading'
            }
            await self.channel_layer.group_send(
                self.room_group_name, waiting_data
            )

            if forward is True:
                message = message

            elif favourite is True:
                message = message
            else:
                outfile = str(round(datetime.now().timestamp() * 1000)) + "." + file_type

                cloud_url = "Voice/" + room_id + outfile

                with open(outfile, "wb") as fh:
                    a = fh.write(base64.decodebytes(message.encode("utf-8")))
                if a > 0:
                    try:
                        storage.child(cloud_url).put(outfile)
                        message = storage.child(cloud_url).get_url(None)

                    except:

                        waiting_data.update({'remark': 'File upload failed'})
                        message = ''
                        await self.channel_layer.group_send(
                            self.room_group_name, waiting_data
                        )
                os.remove(outfile)

        elif message_type == 'video':
            waiting_data = {
                'type': 'chat_message',
                'message': '',
                'message_id': message_id,
                'sender': self.currentUser,
                'message_type': message_type,
                'timestamp': timestamp,
                'online': True,
                'lat': 0,
                'long': 0,
                'typing': typing,
                'outoffocus': out_of_focus,
                'room_id': room_id,
                'forwarded_by': forwarded_by,
                'reply_type': reply_type,
                'replied_message': replied_message,
                'favourite': None,
                'reaction_info': None,
                'remark': 'File is uploading',
                'time': datetime.now().strftime('%H:%M:%S')

            }
            if forward is True:
                message = message

            elif favourite is True:
                message = message
            else:
                outfile = str(round(datetime.now().timestamp() * 1000)) + "." + file_type

                cloud_url = "Video/" + room_id + outfile

                with open(outfile, "wb") as fh:
                    a = fh.write(base64.decodebytes(message.encode("utf-8")))
                if a > 0:
                    try:
                        storage.child(cloud_url).put(outfile)
                        message = storage.child(cloud_url).get_url(None)

                    except:

                        waiting_data.update({'remark': 'File upload failed'})
                        message = ''
                        await self.channel_layer.group_send(
                            self.room_group_name, waiting_data
                        )
                os.remove(outfile)

        elif message_type == 'file':
            waiting_data = {
                'type': 'chat_message',
                'message': '',
                'message_id': message_id,
                'sender': self.currentUser,
                'message_type': message_type,
                'timestamp': timestamp,
                'online': True,
                'lat': 0,
                'long': 0,
                'typing': typing,
                'outoffocus': out_of_focus,
                'room_id': room_id,
                'forwarded_by': forwarded_by,
                'reply_type': reply_type,
                'replied_message': replied_message,
                'favourite': None,
                'reaction_info': None,
                'remark': 'File is uploading',
            }
            self.channel_layer.group_send(
                self.room_group_name, waiting_data
            )

            if forward is True:
                message = message

            elif favourite is True:
                message = message
            else:
                outfile = str(round(datetime.now().timestamp() * 1000)) + "." + file_type

                cloud_url = "Files/" + room_id + outfile

                with open(outfile, "wb") as fh:
                    a = fh.write(base64.decodebytes(message.encode("utf-8")))
                if a > 0:
                    try:
                        storage.child(cloud_url).put(outfile)
                        message = storage.child(cloud_url).get_url(None)

                    except:
                        os.remove(outfile)
                        waiting_data.update({'remark': 'File upload failed'})
                        message = ''
                        await self.channel_layer.group_send(
                            self.room_group_name, waiting_data
                        )
                os.remove(outfile)

        else:
            message = message

        chat_data = {
            'type': 'chat_message',
            'sender': self.currentUser,
            'message_id': message_id,
            'message': message,
            'message_type': message_type,
            'online': True,
            'timestamp': timestamp,
            'lat': 0,
            'long': 0,
            'typing': typing,
            'outoffocus': out_of_focus,
            'room_id': room_id,
            'forwarded_by': forwarded_by,
            'reply_type': reply_type,
            'replied_message': replied_message,
            'favourite': None,
            'reaction_info': None,
            'file_size': file_size,
            'file_name': file_name,
            'time': datetime.now().strftime('%H:%M:%S'),
            'sender_name': sender_name
        }

        message_data = {
            'message_id': message_id,
            'sender': self.currentUser,
            'message': message,
            'message_type': message_type,
            'timestamp': timestamp,
            'lat': 0,
            'long': 0,
            'favourite': None,
            'room_id': room_id,
            'forwarded_by': forwarded_by,
            'reply_type': reply_type,
            'replied_message': replied_message,
            'reaction_info': None,
            'deleted_by': None,
            'file_size': file_size,
            'file_name': file_name

        }

        # print(message_data)
        if message:
            chat_data.update({'message': message})

            # Encrypt Before Inserting to DB
            encrypted_message = encrypt_message(message)
            message_data.update({'message': encrypted_message})

            # print(message_data)
            status, inserted_id = await save_to_database('ChitChat', 'chat_server_message', message_data)


            if message_type == 'text':
                await update_last_message('ChitChat', 'chat_server_chatroom', self.room_name, message,
                                          message_data['timestamp'], message_data['message_id'])

            else:
                msg = self.currentUser + ' send a ' + message_type
                await update_last_message('ChitChat', 'chat_server_chatroom', self.room_name, msg,
                                          message_data['timestamp'], message_data['message_id'])


            await self.channel_layer.group_send(
                self.room_group_name, chat_data
            )

        elif message_type == 'location':
            chat_data.update({'lat': lat})
            chat_data.update({'long': long})
            message_data.update({'lat': lat})
            message_data.update({'long': long})
            await save_to_database('ChitChat', 'chat_server_message', message_data)
            msg = self.currentUser + ' send a ' + message_type
            # print(message_data)
            await update_last_message('ChitChat', 'chat_server_chat_room', self.room_name, msg,
                                      message_data['timestamp'], message_data['message_id'])
            # send message to room group

            await self.channel_layer.group_send(
                self.room_group_name, chat_data
            )

        else:
            chat_data = {
                'type': 'chat_message',
                'sender': self.currentUser,
                'sender_name': sender_name,
                'online': True,
                'timestamp': timestamp,
                'typing': typing,
                'outoffocus': out_of_focus,
                'room_id': room_id,
            }

            await self.channel_layer.group_send(
                self.room_group_name, chat_data
            )


    # Receive message from room group
    async def chat_message(self, event):

        await self.send(text_data=json.dumps(event))