from testing.testcases import TestCase
from utils.redis_client import RedisClient


class RedisTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()

    def testRedisClient(self):
        conn = RedisClient.get_connection()
        # push values to Redis List
        for i in range(3):
            conn.lpush('testkey', f'{i}')
        self.assertEqual(conn.lrange('testkey', 0, -1), [b'2', b'1', b'0'])

        self.clear_cache()
        self.assertEqual(conn.lrange('testkey', 0, -1), [])
