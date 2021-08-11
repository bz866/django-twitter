from testing.testcases import TestCase
from gatekeeper.models import GateKeeper


class GateKeeperTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()

    def test_gatekeeper_model(self):
        hash = GateKeeper.get('non-existed-table')
        # get non-existed table
        self.assertEqual(hash['percent'], 0)
        self.assertEqual(hash['description'], '')
        self.assertEqual(GateKeeper.is_switch_on('non-existed-table'), False)
        self.assertEqual(GateKeeper.in_gk('non-existed-table', 1), False)
        # set gate for gray release
        GateKeeper.set_kv('table1', 'percent', 20)
        hash = GateKeeper.get('table1')
        self.assertEqual(hash['percent'], 20)
        self.assertEqual(hash['description'], '')
        self.assertEqual(GateKeeper.is_switch_on('table1'), False)
        self.assertEqual(GateKeeper.in_gk('table1', 10), True)
        self.assertEqual(GateKeeper.in_gk('table1', 101), True)
        self.assertEqual(GateKeeper.in_gk('table1', 20), False)
        self.assertEqual(GateKeeper.in_gk('table1', 21), False)
        # set 100% opened gate
        GateKeeper.set_kv('table2', 'percent', 100)
        GateKeeper.set_kv('table2', 'description', 'description for table2')
        self.assertEqual(GateKeeper.is_switch_on('table2'), True)
        self.assertEqual(GateKeeper.in_gk('table2', 100), True)
        # modify gatekeeper
        GateKeeper.set_kv('table1', 'percent', 99)
        hash = GateKeeper.get('table1')
        self.assertEqual(hash['percent'], 99)