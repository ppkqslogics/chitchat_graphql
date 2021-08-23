from __future__ import unicode_literals
import graphene
import os
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from graphene_django import DjangoObjectType
from .models import BackgroundImages


class Upload(graphene.Scalar):
    def serialize(self):
        pass


class BackgroundImageType(DjangoObjectType):
    class Meta:
        model = BackgroundImages
        fields = ("id", "url")


class Query(graphene.ObjectType):
    all_images = graphene.List(BackgroundImageType)

    @staticmethod
    def resolve_all_images(root,info):
        return BackgroundImages.objects.all()


class CreateBgImageMutation(graphene.Mutation):
    class Arguments:
        pass

    backgroundImage = graphene.Field(BackgroundImageType)
    ok = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info):
        if info.context.FILES and info.context.method == 'POST':
            image = info.context.FILES['itemImage']
            filename = str(uuid.uuid4()) + image.name
            path = default_storage.save(filename, ContentFile(image.read()))
            tmp_file = os.path.join(settings.MEDIA_URL, path)
            background_image = BackgroundImages(url=tmp_file)
            background_image.save()
            return CreateBgImageMutation(backgroundImage=background_image)


class DeleteBgImageMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, id):
        backgroundImage = BackgroundImages.objects.get(id=id)
        backgroundImage.delete()
        os.remove(settings.BASE_DIR + backgroundImage.url)
        return DeleteBgImageMutation(ok=True)


class Mutation(graphene.ObjectType):
    add_image = CreateBgImageMutation.Field()
    delete_image = DeleteBgImageMutation.Field()


schema = graphene.Schema(query=Query)