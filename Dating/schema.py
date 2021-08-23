import graphene
import pyrebase
from django.db.models import BinaryField
from graphene_django import DjangoObjectType
from Dating.models import *
from graphene_django.converter import convert_django_field
from graphene_file_upload.scalars import Upload

firebaseConfig = {
    "apiKey": "AIzaSyD6RZqyERVDKFSg9p6DtC8D722D6LB5udc",
    "authDomain": "chit-chat-otp.firebaseapp.com",
    "databaseURL": "https://chit-chat-otp.firebaseio.com",
    "projectId": "chit-chat-otp",
    "storageBucket": "chit-chat-otp.appspot.com",
    "messagingSenderId": "696243358039",
    "appId": "1:696243358039:web:489870e0292b526e9f9612",
    "measurementId": "G-EVWG694C9K"
}

firebaseApp = pyrebase.initialize_app(firebaseConfig)
storage = firebaseApp.storage()


@convert_django_field.register(BinaryField)
def convert_field(field, register=None):
    return graphene.String()

class LookingForInfo(DjangoObjectType):
    class Meta:
        model = Looking_for

class InterestsInfo(DjangoObjectType):
    class Meta:
        model = Interests

class Query(object):
    looking_for_lists = graphene.List(LookingForInfo)
    interest_lists = graphene.List(InterestsInfo)

    def resolve_looking_for_lists(self, info, **kwargs):
        return Looking_for.objects.using('Dating').all()

    def resolve_interest_lists(self, info, **kwargs):
        return Interests.objects.using('Dating').all()

class CreateLookingfor(graphene.Mutation):
    looking_type = graphene.Field(LookingForInfo)

    class Arguments:
        looking_for_type = graphene.String()

    def mutate(self, info, looking_for_type):
        data = Looking_for(looking_for_type=looking_for_type)
        data.save(using='Dating')
        return CreateLookingfor(looking_type=data)

class DeleteLookingfor(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID()

    def mutate(self, info, id):
        data = Looking_for.objects.using('Dating').get(pk=id)
        data.delete()
        return DeleteLookingfor(ok=True)

class EditLookingfor(graphene.Mutation):
    looking_for = graphene.Field(LookingForInfo)

    class Arguments:
        looking_id = graphene.ID()
        looking_type = graphene.String()

    def mutate(self, info, looking_id, looking_type):
        data = Looking_for.objects.using('Dating').get(pk=looking_id)
        data.looking_for_type = looking_type
        data.save(using='Dating')
        return EditLookingfor(looking_for=data)

class CreateInterestType(graphene.Mutation):
    class Arguments:
        interest_name = graphene.String()
        interest_logo = Upload()

    interest_type = graphene.Field(InterestsInfo)

    def mutate(self, info, interest_name, interest_logo=None):
        if interest_logo:
            if info.context.FILES and info.context.method == 'POST':
                image = info.context.FILES['itemImage']
                cloud_url = 'Interest/' + interest_name + '.jpg'
                storage.child(cloud_url).put(image)

                interest = Interests.objects.using('Dating').create(
                interest_name=interest_name,
                interest_logo=storage.child(cloud_url).get_url(None),
                )
        interest.save(using='Dating')

        return CreateInterestType(interest_type=interest)

class DeleteInterestType(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    ok = graphene.Boolean()

    def mutate(self, info, id):
        interest = Interests.objects.using('Dating').get(pk=id)
        interest.delete()

        return DeleteLookingfor(ok=True)
class Mutation(graphene.ObjectType):
    create_looking_for_type = CreateLookingfor.Field()
    delete_looking_for_type = DeleteLookingfor.Field()
    edit_looking_for_type = EditLookingfor.Field()
    create_interest_type = CreateInterestType.Field()
    delete_interest_type = DeleteInterestType.Field()