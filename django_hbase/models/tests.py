from testing.testcases import TestCase
from django_hbase.models import HBaseModel
from utils.time_helper import utc_now
from django_hbase.models import HBaseField, IntegerField, TimeStampField


class HBaseModelTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        self.clear_hbase()
        # dummy user
        self.user1, self.user1_client = self.create_user_and_client(username='user1')
        self.user2, self.user2_client = self.create_user_and_client(username='user2')


