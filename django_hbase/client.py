import happybase
from django.conf import settings


class HBaseClient:
    conn = None

    @classmethod
    def get_connection(cls):
        if not cls.conn:
            cls.conn = happybase.Connection(settings.HBASE_HOST)
        return cls.conn

    @classmethod
    def clear_all_tables(cls):
        if not cls.conn:
            cls.conn = cls.get_connection()
        for t in cls.conn.tables():
            cls.conn.disable_table(t)
            cls.conn.delete_table(t)

