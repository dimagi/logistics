import csv
from logistics_project.apps.migration import utils

'''
Utilities used by the migration(s).
'''

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]
def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        try:
            yield line.encode('utf-8')
        except UnicodeDecodeError:
            print line
            continue


def check_router():
    # quasi-stolen from the httptester
    # TODO: this is broken on new rapidsms
    from rapidsms.contrib.ajax.exceptions import RouterNotResponding, RouterError
    try:
        utils.check_status()
        return True
    except RouterNotResponding:
        print "The router is not available! Remember to start the rapidsms " \
          "router before running the migration. FAIL."
    except RouterError:
        print "The router appears to be running but returned an error. " \
              "Is the migration app in your installed_apps list? and " \
              "have you enabled the migration backend?" 
        return False

