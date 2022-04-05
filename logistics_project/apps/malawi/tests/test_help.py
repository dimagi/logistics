from __future__ import unicode_literals

from logistics_project.apps.malawi.tests import MalawiTestBase, create_hsa


class TestHelp(MalawiTestBase):

    def testHelpWithProduct(self):
        create_hsa(self, "+16175551000", "wendy", products="co la lb zi")
        a = """
              +16175551000 > help la
              +16175551000 < la is the code for CCM product LA 1 x 6
            """
        self.runScript(a)

    def testHelpUnknown(self):
        create_hsa(self, "+16175551000", "wendy", products="co la lb zi")
        a = """
              +16175551000 > help zzz
              +16175551000 < Text 'help stock' for help on the format of stock reports; 'help codes' for a list of product codes; 'help [product code]' for a product's description
            """
        self.runScript(a)
