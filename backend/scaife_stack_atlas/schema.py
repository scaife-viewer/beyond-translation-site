import graphene

import scaife_viewer.atlas.schema


class Query(scaife_viewer.atlas.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


schema = graphene.Schema(query=Query)
