import graphene
from graphene_django import DjangoObjectType
from Favourite.models import FavouriteType

class FavouriteInfo(DjangoObjectType):
    class Meta:
        model = FavouriteType
        fields = "__all__"


class Query(graphene.ObjectType):
    favourite_list = graphene.List(FavouriteInfo)

    def resolve_favourite_list(self, info, **kwargs):
        return FavouriteType.objects.all()

class CreateFavouriteType(graphene.Mutation):
    class Arguments:
        favourite_type = graphene.String()

    favourite = graphene.Field(FavouriteInfo)

    def mutate(self, info, favourite_type):
        data = FavouriteType.objects.create(type=favourite_type)
        data.save()
        return CreateFavouriteType(favourite=data)

class DeleteFavouriteType(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    ok = graphene.Boolean()

    def mutate(self, info, id):
        favourite = FavouriteType.objects.get(pk=id)
        favourite.delete()
        return DeleteFavouriteType(ok=True)

class Mutation(graphene.ObjectType):
    create_favourite_type = CreateFavouriteType.Field()
    delete_favourite_type = DeleteFavouriteType.Field()