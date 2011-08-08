from django.utils.importlib import import_module
from rapidsms.conf import settings
from re import findall
from string import maketrans

if hasattr(settings,'LOGISTICS_CONFIG'):
    config = import_module(settings.LOGISTICS_CONFIG)
else:
    import config
    
if hasattr(settings, "CODE_CHARS_RANGE"):
    CODE_CHARS_RANGE = settings.CODE_CHARS_RANGE
else:
    CODE_CHARS_RANGE = (2,4) # from 2 to 4 characters per product code

if hasattr(settings, "NUMERIC_LETTERS"):
    NUMERIC_LETTERS = settings.NUMERIC_LETTERS
else:
    NUMERIC_LETTERS = ("lLO", "110")

def parse_report(val):
    """
    Takes a product report string, such as "zi 10 co 20 la 30", and parses it into a list of tuples
    of (code, quantity):

    >>> parse_report("zi 10 co 20 la 30")
    [('zi', 10), ('co', 20), ('la', 30)]

    Properly handles arbitrary whitespace:

    >>> parse_report("zi10 co20 la30")
    [('zi', 10), ('co', 20), ('la', 30)]

    Properly deals with Os being used for 0s:

    >>> parse_report("zi1O co2O la3O")
    [('zi', 10), ('co', 20), ('la', 30)]

    Properly handles extra spam in the string:

    >>> parse_report("randomextradata zi1O co2O la3O randomextradata")
    [('zi', 10), ('co', 20), ('la', 30)]
    """
    return [(x[0], int(x[1].translate(maketrans(NUMERIC_LETTERS[0], NUMERIC_LETTERS[1])))) \
            for x in findall("\s*(?P<code>[A-Za-z]{%(minchars)d,%(maxchars)d})\s*(?P<quantity>[\-?0-9%(numeric_letters)s]+)\s*" % \
                                    {"minchars": CODE_CHARS_RANGE[0],
                                     "maxchars": CODE_CHARS_RANGE[1],
                                     "numeric_letters": NUMERIC_LETTERS[0]}, str(val))]

if __name__ == '__main__':
    import doctest
    doctest.testmod()