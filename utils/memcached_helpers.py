from django.conf import settings
from django.core.cache import caches

cache = caches['testing'] if settings.TESTING else caches['default']


class MemcachedHelper:
    @classmethod
    def _get_key(cls, model_class, object_id):
        return '{}:{}'.format(model_class.__name__, object_id)

    @classmethod
    def get_object_throught_cache(cls, model_class, object_id):
        key = cls._get_key(model_class,object_id)
        object = cache.get(key)
        if object is not None:
            return object
        # cache miss read from db
        object = model_class.objects.get(id=object_id)
        cache.set(key, object)
        return object

    @classmethod
    def invalidate_object_cache(cls, model_class, object_id):
        key = cls._get_key(model_class, object_id)
        cache.delete(key)
