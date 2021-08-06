from django_hbase.client import HBaseClient
from django_hbase.models import IntegerField, TimeStampField, HBaseField
from django.conf import settings


class HBaseModel:
    class Meta:
        table_name = None
        row_keys = ()

    def __init__(self, **kwargs):
        for key, field in self.get_field_hash().items():
            value = kwargs.get(key)
            setattr(self, key, value)

    @property
    def row_key(self):
        return self.serialize_row_key(self.__dict__)

    @classmethod
    def init_from_row(cls, row_key, row_data):
        if not row_data:
            return None

        data = cls.deserialize_row_key(row_key)
        for column_key, column_value in row_data.items():
            column_key = column_key.decode('utf-8')
            # remove column family from column_key
            key = column_key[column_key.find(':') + 1:]
            data[key] = cls.deserialize_field(key, column_value)
        return cls(**data)

    @classmethod
    def get_table(cls):
        conn = HBaseClient.get_connection()
        return conn.table(cls.get_table_name())

    @classmethod
    def get_field_hash(cls):
        field_hash = {}
        for field in cls.__dict__:
            field_obj = getattr(cls, field)
            if isinstance(field_obj, HBaseField):
                field_hash[field] = field_obj
        return field_hash

    @classmethod
    def serialize_row_key(cls, data):
        """
        serialize row_key fields in bytes as HBasa keys

        Input & Output Example:
        {k1: v1} => 'v1'
        {k1: v1, k2: v2} => 'v1:v2'
        {k1: v1, k2: v2, k3: v3} => 'v1:v2:v3'
        """
        values = []
        field_hash = cls.get_field_hash()
        for key in cls.Meta.row_keys:
            field = field_hash[key]
            value = data.get(key)
            if not value:
                raise BadRowKeyException(f"{key} not defined")
            serialized_value = cls.serialize_field(field, value)
            if ':' in serialized_value:
                raise BadRowKeyException(
                    f"{key} must not have ':' in value {value}")
            values.append(serialized_value)
        return bytes(':'.join(values), encoding='utf-8')

    @classmethod
    def deserialize_row_key(cls, row_key):
        """
        deserialize HBasa bytes keys into row_key, fields dictionary

        Input & Output Example:
        'v1' => {k1: v1}
        'v1:v2' => {k1: v1, k2: v2}
        'v1:v2:v3' = > {k1: v1, k2: v2, k3: v3}
        """
        data = {}
        if isinstance(row_key, bytes):
            row_key = row_key.decode('utf-8')

        # follow the pattern v1:v2:v3: to easily determine the last value by searching ':'
        row_key = row_key + ':'
        for key in cls.Meta.row_keys:
            index = row_key.find(':')
            if index == -1:
                break
            data[key] = cls.deserialize_field(key, row_key[:index])
            row_key = row_key[index + 1:]
        return data

    @classmethod
    def serialize_row_data(cls, data):
        """
        serialize column_key fields as the column content in HBase

        Input & Output Example:
        {k1: v1, k2: v2} => {'cf:k1': serialize_field(v1), 'cf:k2': serialize_field(v2)}
        """
        row_data = {}
        field_hash = cls.get_field_hash()
        for key, field in field_hash.items():
            # skip row_keys
            if not field.column_family:
                continue
            value = data.get(key)
            # skip without saving for empty field
            if not value:
                continue
            column_key = "{}:{}".format(field.column_family, key)
            column_value = cls.serialize_field(field, value)
            row_data[column_key] = column_value
        return row_data

    @classmethod
    def serialize_field(cls, field, value):
        value = str(value)
        if isinstance(field, IntegerField):
            value = value.rjust(16, '0')
        if field.reverse:
            value = value[::-1]
        return value

    @classmethod
    def deserialize_field(cls, key, value):
        field = cls.get_field_hash()[key]
        if field.reverse:
            value = value[::-1]
        if field.field_type in [IntegerField.field_type,
                                TimeStampField.field_type]:
            value = int(value)
        return value

    def save(self):
        row_data = self.serialize_row_data(self.__dict__)
        # if row_data is empty, the HBase will skip it without saving
        # if row_key is empty, raise error
        if len(row_data) == 0:
            raise EmptyColumnException()
        table = self.get_table()
        table.put(self.row_key, row_data)

    @classmethod
    def get(cls, **kwargs):
        row_key = cls.serialize_row_key(kwargs)
        table = cls.get_table()
        row_data = table.row(row_key)
        return cls.init_from_row(row_key, row_data)

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        return instance

    @classmethod
    def get_table_name(cls):
        if not cls.Meta.table_name:
            raise NotImplementedError("table is not defined in HBase")
        # seperate the test and production table names to isolate the test environment
        if settings.TESTING:
            return f"test_{cls.Meta.table_name}"
        return cls.Meta.table_name

    @classmethod
    def create_table(cls):
        if not settings.TESTING:
            raise Exception("it not allowed to create tables "
                            "outside the testing environment")

        conn = HBaseClient.get_connection()
        # skip if table existed
        existed_tables = [table.decode('utf-8') for table in conn.tables()]
        if cls.get_table_name() in existed_tables:
            return
        # otherwise, create new table
        column_families = {
            field.column_family: dict()
            for key, field in cls.get_field_hash().items()
            if field.column_family is not None
        }
        conn.create_table(name=cls.get_table_name(), families=column_families)

    @classmethod
    def drop_table(cls):
        if not settings.TESTING:
            raise Exception("it not allowed to delete tables "
                            "outside the testing environment")

        conn = HBaseClient.get_connection()
        conn.delete_table(cls.get_table_name(), disable=True)


class EmptyColumnException(Exception):
    pass


class BadRowKeyException(Exception):
    pass
