import graphene
import chat_server.schema
import Reaction.schema
import Favourite.schema
import BackgroundImages.schema
import Dating.schema
import Report.schema


class Query(chat_server.schema.Query, Reaction.schema.Query, Favourite.schema.Query, BackgroundImages.schema.Query,
            Dating.schema.Query, Report.schema.Query, graphene.ObjectType):
    pass


class Mutation(chat_server.schema.Mutation, Reaction.schema.Mutation, Favourite.schema.Mutation,
               BackgroundImages.schema.Mutation, Dating.schema.Mutation, Report.schema.Mutation, graphene.ObjectType):
    pass


class Subscription(chat_server.schema.Subscription):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription)
