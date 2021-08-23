import graphene
from graphene_django import DjangoObjectType
from Reaction.models import Reaction
from emoji import demojize

class ReactionInfo(DjangoObjectType):
    class Meta:
        model = Reaction
        fields = "__all__"

class Query(graphene.ObjectType):
    reaction_list = graphene.List(ReactionInfo)

    def resolve_reaction_list(self, info, **kwargs):
        return Reaction.objects.all()

class CreateNewReaction(graphene.Mutation):
    class Arguments:
        reaction = graphene.String()

    reaction = graphene.Field(ReactionInfo)

    def mutate(self, info, reaction):
        emoji_value = demojize(reaction)
        data = Reaction.objects.create(
            emoji_value=emoji_value,
            emoji=reaction
        )
        data.save()
        return CreateNewReaction(reaction=data)


class DeleteReaction(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    ok = graphene.Boolean()

    def mutate(self, info, id):
        reaction = Reaction.objects.get(pk=id)
        reaction.delete()
        return DeleteReaction(ok=True)

class Mutation(graphene.ObjectType):
    create_new_reaction = CreateNewReaction.Field()
    delete_reaction = DeleteReaction.Field()

