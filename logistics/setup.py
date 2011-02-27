#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import sys, os
from django.core.management import execute_manager

def LoadProductsIntoRMS():
    from logistics.apps.logistics.models import Facility, ProductStock, Product
    RMSs = Facility.objects.filter(type='RMS')
    for rms in RMSs:
        products = Product.objects.all()
        for product in products:
            ProductStock(quantity=0, facility=rms, 
                         product=product, monthly_consumption=100).save()
    print "Loaded products into RMSs"

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r." % __file__)
    sys.exit(1)

if __name__ == "__main__":
    filedir = os.path.dirname(__file__)
    sys.path.append(os.path.join(filedir))
    sys.path.append(os.path.join(filedir,'..'))
    sys.path.append(os.path.join(filedir,'..','rapidsms'))
    sys.path.append(os.path.join(filedir,'..','rapidsms','lib'))
    sys.path.append(os.path.join(filedir,'..','rapidsms','lib','rapidsms'))
    sys.path.append(os.path.join(filedir,'..','rapidsms','lib','rapidsms','contrib'))
    LoadProductsIntoRMS()
