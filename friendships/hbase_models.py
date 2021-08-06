from django_hbase.models import HBaseModel
from django_hbase import models as hbase_models


class HBaseFollowing(HBaseModel):
    """
    Save users the from_user_id is following, sorted by 'from_user_id + created_at'

    Enable queries:
    1. from_user_id followings order by created_at
    2. range query for from_user_id followings given time range
    3. range query for from_user_id followings given before or after a timestamp
    """
    # row_key
    from_user_id = hbase_models.IntegerField(reverse=True)
    created_at = hbase_models.TimeStampField()
    # column_key
    to_user_id = hbase_models.IntegerField(column_family='cf')

    class Meta:
        table_name = 'twitter_followings'
        row_keys = ('from_user_id', 'created_at',)


class HBaseFollower(HBaseModel):
    """
    Save to_user_id followers, sorted by 'to_user_id + created_at'

    Enable queries:
    1.to_user_id followers order by created_at
    2. range query for to_user_id followers given time range
    3. range query for to_user_id followers given before or after a timestamp
    """
    # row_key
    to_user_id = hbase_models.IntegerField(reverse=True)
    created_at = hbase_models.TimeStampField()
    # column_key
    from_user_id = hbase_models.IntegerField(column_family='cf')

    class Meta:
        table_name = 'twitter_followers'
        row_keys = ('to_user_id', 'created_at',)


