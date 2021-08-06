class HBaseField:
    field_type = None

    def __init__(self, reverse=False, column_family=None):
        self.reverse = reverse
        self.column_family = column_family
        # TODO: add required=True, default=None
        # TODO: handle in HBaseModel and throw exceptions when needed


class IntegerField(HBaseField):
    field_type = 'int'

    def __init__(self, *args, **kwargs):
        super(IntegerField, self).__init__(*args, **kwargs)


class TimeStampField(HBaseField):
    field_type = 'timestamp'

    def __init__(self, *args, **kwargs):
        super(TimeStampField, self).__init__(*args, **kwargs)
