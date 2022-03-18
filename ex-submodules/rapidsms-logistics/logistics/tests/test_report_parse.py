from __future__ import print_function
from django.test import SimpleTestCase

from logistics.util import parse_report


class TestReportParsing(SimpleTestCase):

    def test_basic(self):
        self.assertEqual(
            [('zi', 10), ('co', 20), ('la', 30)],
            parse_report("zi 10 co 20 la 30")
        )

    def test_whitespace(self):
        self.assertEqual(
            [('zi', 10), ('co', 20), ('la', 30)],
            parse_report("zi10 co20 la30")
        )

    def test_zero_substitution(self):
        self.assertEqual(
            [('zi', 10), ('co', 20), ('la', 30)],
            parse_report("zi1O co2O la3O")
        )

    def test_extra_stuff(self):
        self.assertEqual(
            [('zi', 10), ('co', 20), ('la', 30)],
            parse_report("randomextradata zi1O co2O la3O randomextradata")
        )

