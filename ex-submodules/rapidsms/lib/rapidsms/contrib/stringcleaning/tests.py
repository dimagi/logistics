
from circumcision.apps.labresults.app import App as labresults_App
from circumcision.apps.stringcleaning.app import App as cleaning_App
from circumcision.apps.stringcleaning.inputcleaner import InputCleaner

from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.tests.scripted import TestScript


class TestApp(TestScript):
    
    ic = InputCleaner()
    def testSoundEx(self):
        print '*' * 70
        print 'Testing soundex\n'
        self.assertEqual(self.ic.soundex('thri'), self.ic.soundex('three'))

    def testWordsToDigits(self):
        print '*' * 70
        print 'Testing testWordsToDigits\n'
        self.assertEqual(2, self.ic.words_to_digits('two'))
        self.assertEqual(2, self.ic.words_to_digits('too'))
        self.assertEqual(302, self.ic.words_to_digits('thri hundred two'))
        self.assertEqual(302, self.ic.words_to_digits('thri hundred and two'))
        self.assertEqual(26, self.ic.words_to_digits('twenti six'))
        self.assertEqual(8002, self.ic.words_to_digits('Eight thousand and two'))
        self.assertEqual(2001082, self.ic.words_to_digits('2 milion one thouzand Eighty too samples'))

    def testReplaceoilWith011(self):
        print '*' * 70
        print 'Testing testReplaceoilWith011\n'
        self.assertEqual('00111', self.ic.try_replace_oil_with_011('oOiIl'))
        self.assertEqual('403012', self.ic.try_replace_oil_with_011('4o3oi2'))


    def testRemoveDoubleSpaces(self):
        print '*' * 70
        print 'Testing testRemoveDoubleSpaces\n'
        self.assertEqual('request 10 for db samples',
                         self.ic.remove_double_spaces('request  10    for  db      samples'))

    def testDigitToWord(self):
        print '*' * 70
        print 'Testing testDigitToWord\n'
        self.assertEqual('One', self.ic.digit_to_word(1))
        self.assertEqual('Two', self.ic.digit_to_word(2))
        self.assertEqual('Thirty', self.ic.digit_to_word(30))
        self.assertEqual(None, self.ic.digit_to_word(31))

    def testLdistance(self):
        print '*' * 70
        print 'Testing ldistance\n'
        self.assertEqual(0, self.ic.ldistance('pea', 'PeA'))
        self.assertEqual(1, self.ic.ldistance('peac', 'PeA'))
        self.assertEqual(1, self.ic.ldistance('pea', 'PeAc'))
        self.assertEqual(1, self.ic.ldistance('pea', 'PeAc'))
        self.assertEqual(4, self.ic.ldistance('trev', 'nanc'))
