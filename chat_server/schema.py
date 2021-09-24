from __future__ import unicode_literals
import base64
import uuid
import os
import json
from itertools import chain
import channels_graphql_ws
import graphene
import requests
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from graphene_django.converter import convert_django_field
from djongo.models import ArrayField
from graphene_django import DjangoObjectType
from chat_server.models import *
from chat_server.decryption import decrypt_message
from CHITCHAT_API.settings import MONGO_CLIENT
from CHITCHAT_API.firebaseConfig import firebaseConfig
import pyrebase
import firebase_admin
from firebase_admin import storage as admin_storage, credentials, firestore
from graphene_file_upload.scalars import Upload
from graphene.types.generic import GenericScalar

firebaseApp = pyrebase.initialize_app(firebaseConfig)
storage = firebaseApp.storage()
cred = credentials.Certificate('CHITCHAT_API/chitchat-cred.json')
firebase_admin.initialize_app(cred, {"storageBucket": "chit-chat-otp.appspot.com"})
bucket = admin_storage.bucket()


@convert_django_field.register(ArrayField)
def convert_arrayfield(field, register=None):
    return graphene.String()


class ChatRoomInfo(DjangoObjectType):
    class Meta:
        model = ChatRoom
        fields = "__all__"


class MessageInfo(DjangoObjectType):
    class Meta:
        model = Message
        fields = "__all__"


class Query(graphene.ObjectType):
    room_list = graphene.List(ChatRoomInfo, currentUserContactId=graphene.String(), first=graphene.Int(),
                              skip=graphene.Int())
    allRoom = graphene.List(ChatRoomInfo)
    favourite_message_list = graphene.List(MessageInfo, room_id=graphene.ID(), current_user_id=graphene.String())
    check_room = graphene.List(ChatRoomInfo, user_name=graphene.String(), current_user_id=graphene.String(),
                               chit_chat_id=graphene.String(),
                               user_contact_id=graphene.String(), user_phone=graphene.String(), first=graphene.Int(),
                               skip=graphene.Int())
    message_history = graphene.List(MessageInfo, room_id=graphene.String(), first=graphene.Int(), skip=graphene.Int())
    favourite_filter = graphene.List(MessageInfo, room_id=graphene.String(), message_type=graphene.String(),
                                     current_user_id=graphene.String())
    favourite_search = graphene.List(MessageInfo, keyword=graphene.String(), room_id=graphene.String(),
                                     current_user_id=graphene.String())

    message_search = graphene.List(MessageInfo, keyword=graphene.String(), room_id=graphene.String(), first=graphene.Int(), skip=graphene.Int())

    @staticmethod
    def resolve_allRoom(self, info):
        return ChatRoom.objects.all()

    def resolve_room_list(self, info, currentUserContactId, first=None, skip=None, **kwargs):
        rooms = ChatRoom.objects.filter(participants={'user_contact_id': currentUserContactId}).order_by(
            'last_message_timestamp').reverse()

        if first:
            rooms = rooms[:first]

        if skip:
            rooms = rooms[skip:]

        return rooms

    def resolve_favourite_message_list(self, info, room_id, current_user_id):
        message_query_set = Message.objects.filter(room_id=room_id,
                                                   favourite={'user_contact_id': current_user_id}).order_by(
            'timestamp').reverse()
        for message_query in message_query_set:
            message_query.message = decrypt_message(message_query.message)
        return message_query_set

    def resolve_favourite_search(self, info, room_id, keyword, current_user_id):
        message_query_set = Message.objects.filter(room_id=room_id,
                                                   favourite={'user_contact_id': current_user_id}).order_by(
            'timestamp').reverse()
        ids = []
        for message_query in message_query_set:
            message_query.message = decrypt_message(message_query.message).lower()
            keyword = keyword.lower()
            if keyword in message_query.message:
                ids.append(message_query.message_id)
        if len(ids) == 1:# message_favourite = Message.objects.get(pk=ids[0])
            message_favourite = Message.objects.filter(message_id=ids[0])
            for msg in message_favourite:
                msg.message = decrypt_message(msg.message)
            return message_favourite

        elif len(ids) > 1:
            message_favourite = Message.objects.filter(pk__in=ids)
            for message_query in message_favourite:
                message_query.message = decrypt_message(message_query.message)
            return message_favourite

        else:
            return ""

    def resolve_message_search(self, info, room_id, keyword, first=None, skip=None):
        message_query_set = Message.objects.filter(room_id=room_id).order_by('timestamp').reverse()

        ids = []
        for message_query in message_query_set:
            message_query.message = decrypt_message(message_query.message).lower()
            keyword = keyword.lower()
            if keyword in message_query.message:
                ids.append(message_query.message_id)

        if len(ids) == 1:
            search_message = Message.objects.filter(message_id=ids[0])
            for msg in search_message:
                msg.message = decrypt_message(msg.message)
            return search_message
        elif len(ids) > 1:
            search_message = Message.objects.filter(pk__in=ids)
            for msg in search_message:
                msg.message = decrypt_message(msg.message)

            if first:
                search_message = search_message[:first]

            if skip:
                search_message = search_message[skip:]
            return search_message
        else:
            return ""

    def resolve_favourite_filter(self, info, room_id, message_type, current_user_id):
        if message_type == 'photo' or message_type == 'video':
            print("reach")
            photo_message = Message.objects.filter(room_id=room_id, message_type='photo',
                                                   favourite={'user_contact_id': current_user_id}).order_by(
                'timestamp').reverse()
            video_message = Message.objects.filter(room_id=room_id, message_type='video',
                                                   favourite={'user_contact_id': current_user_id}).order_by(
                'timestamp'
            ).reverse()
            message_query_set = list(chain(photo_message, video_message))

        elif message_type == 'audio' or 'voice':
            audio_message = Message.objects.filter(room_id=room_id, message_type='audio',
                                                   favourite={'user_contact_id': current_user_id}).order_by(
                'timestamp'
            ).reverse()
            voice_message = Message.objects.filter(room_id=room_id, message_type='voice',
                                                   favourite={'user_contact_id': current_user_id}).order_by(
                'timestamp').reverse()
            message_query_set = list(chain(audio_message, voice_message))

        else:
            message_query_set = Message.objects.filter(room_id=room_id, message_type=message_type,
                                                   favourite={'user_contact_id': current_user_id}).order_by(
            'timestamp').reverse()

        for message_query in message_query_set:
            message_query.message = decrypt_message(message_query.message)
        return message_query_set

    def resolve_message_history(self, info, room_id, first=None, skip=None, **kwargs):

        message_query_set = Message.objects.filter(room_id=room_id).order_by('timestamp').reverse()
        for message_query in message_query_set:
           message_query.message = decrypt_message(message_query.message)
            
        if skip:
            message_query_set = message_query_set[skip:]

        if first:
            message_query_set = message_query_set[:first]

        return (message_query_set)

    def resolve_check_room(self, info, user_name=None, current_user_id=None, chit_chat_id=None, user_contact_id=None,
                           user_phone=None, first=None, skip=None):
        rooms = ChatRoom.objects.filter(participants={'user_contact_id': current_user_id}).order_by(
            'last_message_timestamp').reverse()

        ids = []

        if user_name is not None:
            for all in rooms:
                par_list = all.participants
                for i in range(len(par_list)):
                    org_name = par_list[i].get('user_name').lower()
                    user_name = user_name.lower()

                    if user_name in org_name:
                        ids.append(all.id)
            if len(ids) == 1:
                print('here', ids[0])
                room = ChatRoom.objects.filter(id=ids[0])
                return room
            elif len(ids) == 0:
                return None
            else:
                room = ChatRoom.objects.filter(pk__in=ids).order_by('last_message_timestamp').reverse()
                if skip:
                    room = room[skip:]
                if first:
                    room = room[:first]
                return room

        if user_contact_id is not None:
            for all in rooms:
                par_list = all.participants
                for i in range(len(par_list)):
                    org_name = par_list[i].get('user_contact_id').lower()
                    user_name = user_contact_id.lower()
                    if user_name in org_name:
                        ids.append(all.id)

            if len(ids) == 1:
                print('here', ids[0])
                room = ChatRoom.objects.filter(id=ids[0])
                return room
            elif len(ids) == 0:
                return None
            else:
                room = ChatRoom.objects.filter(pk__in=ids).order_by('last_message_timestamp').reverse()
                if skip:
                    room = room[skip:]
                if first:
                    room = room[:first]
                return room

        if chit_chat_id is not None:
            for all in rooms:
                par_list = all.participants
                for i in range(len(par_list)):
                    org_name = par_list[i].get('chit_chat_id').lower()
                    user_name = chit_chat_id.lower()

                    if user_name in org_name:
                        ids.append(all.id)

            if len(ids) == 1:
                print('here', ids[0])
                room = ChatRoom.objects.filter(id=ids[0])
                return room
            elif len(ids) == 0:
                return None
            else:
                room = ChatRoom.objects.filter(pk__in=ids).order_by('last_message_timestamp').reverse()
                if skip:
                    room = room[skip:]
                if first:
                    room = room[:first]
                return room

        if user_phone is not None:
            for all in rooms:
                par_list = all.participants
                for i in range(len(par_list)):
                    org_name = par_list[i].get('user_phone')
                    user_name = user_phone

                    if user_name in org_name:
                        ids.append(all.id)

            if len(ids) == 1:
                print('here', ids[0])
                room = ChatRoom.objects.filter(id=ids[0])
                return room
            elif len(ids) == 0:
                return None
            else:
                room = ChatRoom.objects.filter(pk__in=ids).order_by('last_message_timestamp').reverse()
                if skip:
                    room = room[skip:]
                if first:
                    room = room[:first]
                return room


class CreateChatRoom(graphene.Mutation):
    class Arguments:
        ids = graphene.List(graphene.String)
        room_name = graphene.String()
        photo = graphene.String()

    room_id = graphene.String()
    participants = graphene.List(graphene.String)
    room_name = graphene.String()
    room_photo = graphene.String()
    thread_type = graphene.String()

    def mutate(self, info, ids, room_name=None, photo=None):

        if len(ids) > 2:
            thread_type = 'group'
        else:
            thread_type = 'private'
            a = ChatRoom.objects.filter(participants={'user_contact_id': ids[0]}, thread_type='private')
            a = a.filter(participants={'user_contact_id': ids[1]})
            if len(a) == 1:
                for all in a:
                    print(all.id)
                    room_id = all.id
                    room_query = ChatRoom.objects.get(pk=room_id)
                    return CreateChatRoom(room_id=room_id, participants=room_query.participants,
                                          room_name=room_query.room_name, room_photo=room_query.room_photo,
                                          thread_type=room_query.thread_type)

        participant = []

        for all in ids:
            url = "http://localhost:8000/profile_app/profile/" + all
            rest_data = requests.get(url)
            rest_data = rest_data.text
            rest_data = json.loads(rest_data)

            data = {
                "chit_chat_id": rest_data['user']['chit_chat_id'],
                "user_contact_id": rest_data['user']['id'],
                "user_name": rest_data['user']['name'],
                "user_photo": rest_data['user']['photo'],
                "user_phone": rest_data['user']['phone']
            }
            participant.append(data)
        if thread_type == 'private':
            room = ChatRoom.objects.create(
                thread_type=thread_type,
                participants=participant
            )
            room_query = ChatRoom.objects.get(pk=room.id)
            return CreateChatRoom(room_id=room_query.id, participants=room_query.participants,
                                  room_name=room_query.room_name, room_photo=room_query.room_photo,
                                  thread_type=room_query.thread_type)
        else:
            if room_name is not None and photo is None:
                room = ChatRoom.objects.create(
                    thread_type=thread_type,
                    participants=participant,
                    room_name=room_name
                )

            elif room_name is None and photo is not None:
                outfile = str(round(datetime.now().timestamp() * 10000)) + '.jpg'
                cloud_url = 'GroupPhoto/' + outfile

                with open(outfile, "wb") as fh:
                    a = fh.write(base64.decodebytes(photo.encode("utf-8")))
                storage.child(cloud_url).put(outfile)
                room = ChatRoom.objects.create(
                    thread_type=thread_type,
                    participants=participant,
                    room_photo=storage.child(cloud_url).get_url(None)
                )
                os.remove(outfile)

            elif room_name and photo is not None:
                outfile = str(round(datetime.now().timestamp() * 10000)) + '.jpg'
                cloud_url = 'GroupPhoto/' + outfile

                with open(outfile, "wb") as fh:
                    a = fh.write(base64.decodebytes(photo.encode("utf-8")))
                storage.child(cloud_url).put(outfile)

                room = ChatRoom.objects.create(
                    thread_type=thread_type,
                    participants=participant,
                    room_name=room_name,
                    room_photo=storage.child(cloud_url).get_url(None)
                )
                os.remove(outfile)

            else:
                room = ChatRoom.objects.create(
                    thread_type=thread_type,
                    participants=participant
                )
            room_query = ChatRoom.objects.get(pk=room.id)

            return CreateChatRoom(room_id=room_query.id, participants=room_query.participants,
                                  room_name=room_query.room_name, room_photo=room_query.room_photo,
                                  thread_type=room_query.thread_type)


class SetOrCancelChatRoomPinTop(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        currentUserContactId = graphene.String()

    room = graphene.Field(ChatRoomInfo)

    def mutate(self, info, id, currentUserContactId):
        room = ChatRoom.objects.get(pk=id)

        if room.pin_top is None or len(room.pin_top) == 0:
            room.pin_top = [{"user_contact_id": currentUserContactId}]
            room.save()
            RealTimeAction.broadcast(payload={
                'action': 'SetOrCancelChatRoomPinTop',
                'id': room.id,
                'room_name': room.room_name,
                'room_photo': room.room_photo,
                'thread_type': room.thread_type,
                'last_message_id': room.last_message_id,
                'last_message': room.last_message,
                'last_message_timestamp': room.last_message_timestamp,
                'participants': room.participants,
                'pin_top': room.pin_top,
                'deleted_by': room.deleted_by,
                'background': room.backgrounds
            })
            return SetOrCancelChatRoomPinTop(room=room)
        else:
            for all in room.pin_top:
                print('currently pin top user :', all['user_contact_id'])
                if all['user_contact_id'] == currentUserContactId:
                    room.pin_top.remove(all)
                    room.save()
                    RealTimeAction.broadcast(payload={
                        'action': 'SetOrCancelChatRoomPinTop',
                        'id': room.id,
                        'room_name': room.room_name,
                        'room_photo': room.room_photo,
                        'thread_type': room.thread_type,
                        'last_message_id': room.last_message_id,
                        'last_message': room.last_message,
                        'last_message_timestamp': room.last_message_timestamp,
                        'participants': room.participants,
                        'pin_top': room.pin_top,
                        'deleted_by': room.deleted_by,
                        'background': room.backgrounds
                    })
                    return SetOrCancelChatRoomPinTop(room=room)
            for all in room.pin_top:
                if all['user_contact_id'] != currentUserContactId:
                    pin_user = {"user_contact_id": currentUserContactId}
                    room.pin_top.append(pin_user)
                    room.save()
                    RealTimeAction.broadcast(payload={
                        'action': 'SetOrCancelChatRoomPinTop',
                        'id': room.id,
                        'room_name': room.room_name,
                        'room_photo': room.room_photo,
                        'thread_type': room.thread_type,
                        'last_message_id': room.last_message_id,
                        'last_message': room.last_message,
                        'last_message_timestamp': room.last_message_timestamp,
                        'participants': room.participants,
                        'pin_top': room.pin_top,
                        'deleted_by': room.deleted_by,
                        'background': room.backgrounds
                    })
                    return SetOrCancelChatRoomPinTop(room=room)


class SetOrCancelReaction(graphene.Mutation):
    class Arguments:
        message_id = graphene.ID()
        reaction = graphene.String()
        current_user_id = graphene.String()

    reaction_message = graphene.Field(MessageInfo)

    def mutate(self, info, message_id, reaction, current_user_id):

        message = Message.objects.get(pk=message_id)
        db_client = MONGO_CLIENT["ChitChat"]["chat_server_message"]
        id_query = {"message_id": message_id}

        # Check if there's previous reaction or not
        if message.reaction_info is None or len(message.reaction_info) < 1:

            new_values = {"$set": {"reaction_info": [{
                'user_contact_id': current_user_id,
                'reaction': reaction
            }]}}
            db_client.update_one(id_query, new_values)
            updated_message = Message.objects.get(pk=message_id)
            updated_message.message = decrypt_message(message.message)

            RealTimeAction.broadcast(payload={
                'action': 'SetOrCancelReaction',
                'message_id': updated_message.message_id,
                'message': updated_message.message,
                'message_type': updated_message.message_type,
                'sender': updated_message.sender,
                'timestamp': updated_message.sender,
                'lat': updated_message.lat,
                'long': updated_message.long,
                'favourite': updated_message.favourite,
                'room_id': updated_message.room_id,
                'forwarded_by': updated_message.forwarded_by,
                'reply_type': updated_message.reply_type,
                'replied_message': updated_message.replied_message,
                'reaction_info': updated_message.reaction_info,
                'deleted_by': updated_message.deleted_by
            })
            return SetOrCancelReaction(reaction_message=updated_message)

        # If there's previous reaction

        else:
            reaction_info = message.reaction_info
            for r in reaction_info:
                # Check if the current_user_id exists in the reaction_info field
                if r['user_contact_id'] == current_user_id:
                    # If the reaction is the same, remove it
                    if r['reaction'] == reaction:
                        remove_reaction = {"$pull": {"reaction_info": {
                            'user_contact_id': current_user_id,
                            'reaction': reaction
                        }}}
                        db_client.update_one(id_query, remove_reaction)
                        updated_message = Message.objects.get(pk=message_id)
                        updated_message.message = decrypt_message(message.message)

                        RealTimeAction.broadcast(payload={
                            'action': 'SetOrCancelReaction',
                            'message_id': updated_message.message_id,
                            'message': updated_message.message,
                            'message_type': updated_message.message_type,
                            'sender': updated_message.sender,
                            'timestamp': updated_message.sender,
                            'lat': updated_message.lat,
                            'long': updated_message.long,
                            'favourite': updated_message.favourite,
                            'room_id': updated_message.room_id,
                            'forwarded_by': updated_message.forwarded_by,
                            'reply_type': updated_message.reply_type,
                            'replied_message': updated_message.replied_message,
                            'reaction_info': updated_message.reaction_info,
                            'deleted_by': updated_message.deleted_by
                        })
                        return SetOrCancelReaction(reaction_message=updated_message)

                    # If the reaction is not the same, replace the old with new reaction
                    elif r['reaction'] != reaction:
                        find_previous_reaction = {"message_id": message_id,
                                                  "reaction_info.user_contact_id": current_user_id}
                        new_values = {"$set": {"reaction_info.$.reaction": reaction}}
                        db_client.update_one(find_previous_reaction, new_values)
                        updated_message = Message.objects.get(pk=message_id)
                        updated_message.message = decrypt_message(message.message)

                        RealTimeAction.broadcast(payload={
                            'action': 'SetOrCancelReaction',
                            'message_id': updated_message.message_id,
                            'message': updated_message.message,
                            'message_type': updated_message.message_type,
                            'sender': updated_message.sender,
                            'timestamp': updated_message.sender,
                            'lat': updated_message.lat,
                            'long': updated_message.long,
                            'favourite': updated_message.favourite,
                            'room_id': updated_message.room_id,
                            'forwarded_by': updated_message.forwarded_by,
                            'reply_type': updated_message.reply_type,
                            'replied_message': updated_message.replied_message,
                            'reaction_info': updated_message.reaction_info,
                            'deleted_by': updated_message.deleted_by
                        })
                        return SetOrCancelReaction(reaction_message=updated_message)

            # If the user is new, append new document
            new_values = {"$push": {"reaction_info": {'user_contact_id': current_user_id, 'reaction': reaction}}}
            db_client.update_one(id_query, new_values)
        updated_message = Message.objects.get(pk=message_id)
        updated_message.message = decrypt_message(message.message)

        RealTimeAction.broadcast(payload={
            'action': 'SetOrCancelReaction',
            'message_id': updated_message.message_id,
            'message': updated_message.message,
            'message_type': updated_message.message_type,
            'sender': updated_message.sender,
            'timestamp': updated_message.sender,
            'lat': updated_message.lat,
            'long': updated_message.long,
            'favourite': updated_message.favourite,
            'room_id': updated_message.room_id,
            'forwarded_by': updated_message.forwarded_by,
            'reply_type': updated_message.reply_type,
            'replied_message': updated_message.replied_message,
            'reaction_info': updated_message.reaction_info,
            'deleted_by': updated_message.deleted_by
        })
        return SetOrCancelReaction(reaction_message=updated_message)


class SetOrCancelFavouriteMessage(graphene.Mutation):
    class Arguments:
        message_id = graphene.ID()
        current_user_id = graphene.String()

    favourite_message = graphene.Field(MessageInfo)

    def mutate(self, info, message_id, current_user_id):
        message = Message.objects.get(pk=message_id)
        db_client = MONGO_CLIENT["ChitChat"]["chat_server_message"]
        id_query = {"message_id": message_id}
        favourite = message.favourite
        if favourite is None or len(favourite) < 1:
            new_values = {"$set": {"favourite": [{'user_contact_id': current_user_id}]}}
            db_client.update_one(id_query, new_values)
            updated_message = Message.objects.get(pk=message_id)
            updated_message.message = decrypt_message(message.message)

            RealTimeAction.broadcast(payload={
                'action': 'SetOrCancelFavouriteMessage',
                'message_id': updated_message.message_id,
                'message': updated_message.message,
                'message_type': updated_message.message_type,
                'sender': updated_message.sender,
                'timestamp': updated_message.sender,
                'lat': updated_message.lat,
                'long': updated_message.long,
                'favourite': updated_message.favourite,
                'room_id': updated_message.room_id,
                'forwarded_by': updated_message.forwarded_by,
                'reply_type': updated_message.reply_type,
                'replied_message': updated_message.replied_message,
                'reaction_info': updated_message.reaction_info,
                'deleted_by': updated_message.deleted_by
            })
            return SetOrCancelFavouriteMessage(updated_message)

        else:
            for f in favourite:
                # Check if the current_user_id exists in the favourite field
                if f['user_contact_id'] == current_user_id:
                    remove_favorite = {"$pull": {"favourite": {
                        'user_contact_id': current_user_id
                    }}}
                    db_client.update_one(id_query, remove_favorite)
                    updated_message = Message.objects.get(pk=message_id)
                    updated_message.message = decrypt_message(updated_message.message)
                    RealTimeAction.broadcast(payload={
                        'action': 'SetOrCancelFavouriteMessage',
                        'message_id': updated_message.message_id,
                        'message': updated_message.message,
                        'message_type': updated_message.message_type,
                        'sender': updated_message.sender,
                        'timestamp': updated_message.sender,
                        'lat': updated_message.lat,
                        'long': updated_message.long,
                        'favourite': updated_message.favourite,
                        'room_id': updated_message.room_id,
                        'forwarded_by': updated_message.forwarded_by,
                        'reply_type': updated_message.reply_type,
                        'replied_message': updated_message.replied_message,
                        'reaction_info': updated_message.reaction_info,
                        'deleted_by': updated_message.deleted_by
                    })
                    return SetOrCancelFavouriteMessage(updated_message)

            new_values = {"$push": {"favourite": {'user_contact_id': current_user_id}}}
            db_client.update_one(id_query, new_values)
            updated_message = Message.objects.get(pk=message_id)
            updated_message.message = decrypt_message(message.message)

            RealTimeAction.broadcast(payload={
                'action': 'SetOrCancelFavouriteMessage',
                'message_id': updated_message.message_id,
                'message': updated_message.message,
                'message_type': updated_message.message_type,
                'sender': updated_message.sender,
                'timestamp': updated_message.sender,
                'lat': updated_message.lat,
                'long': updated_message.long,
                'favourite': updated_message.favourite,
                'room_id': updated_message.room_id,
                'forwarded_by': updated_message.forwarded_by,
                'reply_type': updated_message.reply_type,
                'replied_message': updated_message.replied_message,
                'reaction_info': updated_message.reaction_info,
                'deleted_by': updated_message.deleted_by
            })
            return SetOrCancelFavouriteMessage(updated_message)


class DeleteChatRoom(graphene.Mutation):
    class Arguments:
        room_id = graphene.ID()
        current_user_id = graphene.ID()

    ok = graphene.Boolean()

    def mutate(self, info, current_user_id, room_id):
        room = ChatRoom.objects.get(pk=room_id)

        def mark_message_as_delete(room_id, current_user_id, par_len):
            db_client = MONGO_CLIENT["ChitChat"]["chat_server_message"]
            try:
                message_data = Message.objects.filter(room_id=room_id)

                for msg in message_data:
                    id_query = {"message_id": msg.message_id}
                    if msg.deleted_by is None or len(room.deleted_by) == 0:
                        print("message delete is zero")
                        new_values = {"$set": {"deleted_by": [{'user_contact_id': current_user_id}]}}
                        db_client.update_one(id_query, new_values)
                    else:
                        delete_info = msg.deleted_by
                        current_info = {'user_contact_id': current_user_id}
                        if current_info in delete_info:
                            print(True, current_info, delete_info )
                        else:
                            print('inserting new value')
                            new_values = {"$push": {"deleted_by": {'user_contact_id': current_user_id}}}
                            db_client.update_one(id_query, new_values)

            except:
                pass
            try:
                message_data_data_ = Message.objects.filter(room_id=room_id)
                for all in message_data_data_:
                    if len(all.deleted_by) == par_len:
                        all.delete()
            except:
                pass

        if room.deleted_by is None or len(room.deleted_by) == 0:
            room.deleted_by = [{'user_contact_id': current_user_id}]
            room.save()
            mark_message_as_delete(room_id, current_user_id, len(room.participants))
            RealTimeAction.broadcast(
                payload={
                    'action': 'DeleteChatRoom',
                    'room_id': room_id,
                    'ok': True
                }
            )
            return DeleteChatRoom(ok=True)
        else:
            delete_info = room.deleted_by
            for d in delete_info:
                if d['user_contact_id'] == current_user_id:
                    mark_message_as_delete(room_id, current_user_id, len(room.participants))
                    return DeleteChatRoom(ok=True)
            room.deleted_by.append({'user_contact_id': current_user_id})
            room.save()

            if len(room.deleted_by) == len(room.participants):
                room.delete()

            mark_message_as_delete(room_id, current_user_id, len(room.participants))
            RealTimeAction.broadcast(
                payload={
                    'action': 'DeleteChatRoom',
                    'room_id': room_id,
                    'ok': True
                }
            )
            return DeleteChatRoom(ok=True)

        RealTimeAction.broadcast(
            payload={
                'action': 'DeleteChatRoom',
                'room_id': room_id,
                'ok': False
            }
        )
        return DeleteChatRoom(ok=False)


class DeleteMessage(graphene.Mutation):
    class Arguments:
        ids = graphene.List(graphene.String)
        room_id = graphene.String()
        current_user_id = graphene.String()
        delete_type = graphene.String()

    ok = graphene.Boolean()

    def mutate(self, info, ids, room_id, current_user_id, delete_type):

        db_client = MONGO_CLIENT["ChitChat"]["chat_server_message"]
        room = ChatRoom.objects.get(pk=room_id)
        room_participants_len = len(room.participants)

        print(room_participants_len)

        def update_last_message(chatroom_id):
            room_to_update = ChatRoom.objects.get(pk=chatroom_id)
            lastMessageObject = Message.objects.filter(room_id=chatroom_id).order_by('-timestamp')[0]

            # UPDATE CHAT_SERVER_ROOM COLLECTION WITH NEW LAST MESSAGE
            room_to_update.last_message_id = lastMessageObject.message_id
            room_to_update.last_message = decrypt_message(lastMessageObject.message)
            room_to_update.last_message_timestamp = lastMessageObject.timestamp
            room_to_update.save()

        if len(ids) == 1:
            print(ids[0])
            message = Message.objects.get(pk=ids[0])
            id_query = {"message_id": ids[0]}

            if delete_type == 'recall':
                if message.message_type == 'photo' or 'file' or 'video' or 'voice':
                    del_path = decrypt_message(message.message)
                    del_path = del_path[del_path.find('/o/') + 3:del_path.find('?')].replace('%2F', '/')
                    print(del_path)
                    blog = bucket.blob(del_path)
                    # blog.delete()
                message.delete()
                update_last_message(room_id)
                RealTimeAction.broadcast(payload={
                    'action': 'DeleteMessage',
                    'ids': ids,
                    'ok': True
                })
                return DeleteMessage(ok=True)
            elif delete_type == 'delete':
                if message.deleted_by is None:
                    new_values = {"$set": {"deleted_by": [{'user_contact_id': current_user_id}]}}
                    db_client.update_one(id_query, new_values)
                    RealTimeAction.broadcast(payload={
                        'action': 'DeleteMessage',
                        'ids': ids,
                        'ok': True

                    })
                    return DeleteMessage(ok=True)
                elif len(message.deleted_by) < room_participants_len:
                    new_values = {"$push": {"deleted_by": {'user_contact_id': current_user_id}}}
                    db_client.update_one(id_query, new_values)
                    RealTimeAction.broadcast(payload={
                        'action': 'DeleteMessage',
                        'ids': ids,
                        'ok': True
                    })
                    return DeleteMessage(ok=True)
                else:
                    if message.message_type == 'photo' or 'file' or 'video' or 'voice':
                        del_path = decrypt_message(message.message)
                        del_path = del_path[del_path.find('/o/') + 3:del_path.find('?')].replace('%2F', '/')
                        blob = bucket.blob(del_path)
                        blob.delete()
                    message.delete()
                    update_last_message(room_id)
                    RealTimeAction.broadcast(payload={
                        'action': 'DeleteMessage',
                        'ids': ids,
                        'ok': True
                    })
                    return DeleteMessage(ok=True)


        elif len(ids) > 1:
            for msg_id in ids:
                message = Message.objects.get(pk=msg_id)
                id_query = {"message_id": msg_id}
                if message.deleted_by is None:
                    new_values = {"$set": {"deleted_by": [{'user_contact_id': current_user_id}]}}
                    db_client.update_one(id_query, new_values)

                elif len(message.deleted_by) < room_participants_len-1:
                    new_values = {"$push": {"deleted_by": {'user_contact_id': current_user_id}}}
                    db_client.update_one(id_query, new_values)

                else:

                    message.delete()
                    update_last_message(room_id)
            RealTimeAction.broadcast(payload={
                'action': 'DeleteMessage',
                'ids': ids,
                'ok': True
            })
            return DeleteMessage(ok=True)

            RealTimeAction.broadcast(payload={
                'action': 'DeleteMessage',
                'ids': ids,
                'ok': False
            })
            return DeleteMessage(ok=False)


class UploadBackground(graphene.Mutation):
    class Arguments:
        room_id = graphene.String(required=True)
        current_user_id = graphene.String(required=True)
        image_data = graphene.String(required=True)

    room = graphene.Field(ChatRoomInfo)

    @classmethod
    def mutate(cls, root, info, room_id, current_user_id, image_data, bg_type="user"):
        room = ChatRoom.objects.get(pk=room_id)
        if image_data is not None:
            outfile = str(round(datetime.now().timestamp()*10000)) + '.jpg'
            cloud_url = 'Background/' + outfile
            with open(outfile, "wb") as fh:
                a = fh.write(base64.decodebytes(image_data.encode("utf-8")))
            storage.child(cloud_url).put(outfile)
            bg_url = storage.child(cloud_url).get_url(None)

            os.remove(outfile)

            if room.backgrounds is None:
                room.backgrounds = [{'user_contact_id': current_user_id, 'background_url': bg_url, 'bg_type': bg_type}]
            else:
                must_replace = False
                replace_index = 0
                for i, bg in enumerate(room.backgrounds):
                    if bg.get('user_contact_id', "Not Found") is current_user_id:
                        must_replace = True
                        replace_index = i
                        break
                if must_replace:
                    if room.backgrounds[replace_index].get('bg_type') == 'user':
                        pass
                        #os.remove(settings.BASE_DIR + room.backgrounds[replace_index].get('background_url'))
                    room.backgrounds[replace_index] = {'user_contact_id': current_user_id, 'background_url': bg_url,
                                                       'bg_type': bg_type}
                else:
                    room.backgrounds.append(
                        {'user_contact_id': current_user_id, 'background_url': bg_url, 'bg_type': bg_type})
            room.save()

            return UploadBackground(room=room)


class SelectBackground(graphene.Mutation):
    class Arguments:
        room_id = graphene.String(required=True)
        current_user_id = graphene.String(required=True)
        bg_url = graphene.String(required=True)

    room = graphene.Field(ChatRoomInfo)

    def mutate(self, info, room_id, current_user_id, bg_url, bg_type="system"):
        room = ChatRoom.objects.get(pk=room_id)
        if room.backgrounds is None:
            room.backgrounds = [{'user_contact_id': current_user_id, 'background_url': bg_url, 'bg_type': bg_type}]
        else:
            must_replace = False
            replace_index = 0
            for i, bg in enumerate(room.backgrounds):
                if bg.get('user_contact_id', "Not Found") is current_user_id:
                    must_replace = True
                    replace_index = i
                    break
            if must_replace:
                if room.backgrounds[replace_index].get('bg_type') == 'user':
                    pass
                    #os.remove(settings.BASE_DIR + room.backgrounds[replace_index].get('background_url'))
                room.backgrounds[replace_index] = {'user_contact_id': current_user_id, 'background_url': bg_url,
                                                   'bg_type': bg_type}
            else:
                room.backgrounds.append(
                    {'user_contact_id': current_user_id, 'background_url': bg_url, 'bg_type': bg_type})
        room.save()
        return SelectBackground(room=room)


class Mutation(graphene.ObjectType):
    create_chat_room = CreateChatRoom.Field()
    set_or_cancel_chat_room_pin_top = SetOrCancelChatRoomPinTop.Field()
    set_or_cancel_favourite = SetOrCancelFavouriteMessage.Field()
    set_or_cancel_reaction = SetOrCancelReaction.Field()
    delete_chat_room = DeleteChatRoom.Field()
    delete_message = DeleteMessage.Field()
    select_background = SelectBackground.Field()
    upload_background = UploadBackground.Field()


class RealTimeAction(channels_graphql_ws.Subscription):
    payload = GenericScalar()

    def subscribe(self, info):
        return ['group42']

    def publish(payload, info):
        return RealTimeAction(payload=payload)


class Subscription(graphene.ObjectType):
    real_time_action = RealTimeAction.Field()
