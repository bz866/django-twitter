from utils.json_encoder import JSONEncoder
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
            stream_or_string=serialized_data,
        ))[0].object
