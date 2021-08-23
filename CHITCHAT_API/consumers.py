import channels_graphql_ws
from CHITCHAT_API.schema import schema

def demo_middleware(next_middleware, root, info, *args, **kwds):
    if(
        info.operation.name is not None
        and info.operation.name.value != "IntrospectionQuery"
    ):
        print("Demo middleware report")
        print("     operation :", info.operation.operation)
        print("     name      :", info.operation.name.value)
    return next_middleware(root, info, *args, **kwds)

class MyGraphqlWsConsumer(channels_graphql_ws.GraphqlWsConsumer):

    async def on_connect(self, payload):
        print("New client connected!", payload)

    schema = schema
    middleware = [demo_middleware]