from rapidsms.tests.scripted import TestScript
from logistics.apps.malawi import loader


class MalawiTestBase(TestScript):
    """
    Base test class that prepopulates tests with malawi's static data
    """
    def setUp(self):
        super(MalawiTestBase, self).setUp()
        loader.init_static_data()
