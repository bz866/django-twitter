from json_encoder import JSONEncoder
from django.core import serializers


class DjangoModelSerializer:
    @classmethod
    def serialize(cls, instance):
        return serializers.serialize(
            format='json',
            # django.core.serializers only work for queryset, not instance
            queryset=[instance],
            cls=JSONEncoder,
        )

    @classmethod
    def deserialize(cls, serialized_data):
        return list(serializers.deserialize(
            format='json',
            serialized_data=serialized_data,
            cls=JSONEncoder,
        ))[0].object
