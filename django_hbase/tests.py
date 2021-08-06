from testing.testcases import TestCase
from django_hbase.client import HBaseClient


class HBaseClientTest(TestCase):

    def setUp(self) -> None:
        self.clear_hbase()

    def test_get_connection(self):
        families = {'cf': dict()}
        conn = HBaseClient.get_connection()
        conn.create_table('test_table_1', families)
        self.assertEqual(conn.tables(), [b'test_table_1'])
        conn.create_table('test_table_2', families)
        self.assertEqual(len(conn.tables()), 2)
        self.assertEqual(conn.tables(), [b'test_table_1', b'test_table_2'])
        conn.delete_table('test_table_1', disable=True)
        self.assertEqual(conn.tables(), [b'test_table_2'])

        # lose connection
        conn.close()
        conn.open()
        self.assertEqual(conn.tables(), [b'test_table_2'])
        self.clear_hbase()




