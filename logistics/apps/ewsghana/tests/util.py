from rapidsms.tests.scripted import TestScript
from logistics.apps.logistics.models import SupplyPointType, \
    ProductReportType, SupplyPoint, Product, ProductStock, \
    ProductType, STOCK_ON_HAND_REPORT_TYPE
from rapidsms.contrib.locations.models import Location

def load_test_data():
        ProductReportType.objects.get_or_create(code=STOCK_ON_HAND_REPORT_TYPE,
                                                name=STOCK_ON_HAND_REPORT_TYPE)
        location, created = Location.objects.get_or_create(name='Dangme East', 
                                                           code='de')
        gar, created = Location.objects.get_or_create(name='Greater Accra Region', 
                                                      code='gar')
        hctype, created = SupplyPointType.objects.get_or_create(code='hc')
        rmstype, created = SupplyPointType.objects.get_or_create(code='rms')
        rms, created = SupplyPoint.objects.get_or_create(code='garms', name="GARMS", 
                                                         type=rmstype, 
                                                         location=gar)
        dedh, created = SupplyPoint.objects.get_or_create(code='dedh', 
                                                          name='Dangme East District Hospital',
                                                          location=location, active=True,
                                                          type=hctype, supplied_by=rms)
        fp, created = ProductType.objects.get_or_create(code='fp', name="Family Planning")
        ov, created = Product.objects.get_or_create(sms_code='ov', name='Overette',
                                                    type=fp, units='cycle')
        ml, created = Product.objects.get_or_create(sms_code='ml', name='Microlut',
                                                    type=fp, units='cycle')
        ml.equivalents.add(ov)
        ps, created = ProductStock.objects.get_or_create(product=ov, supply_point=dedh, 
                                           manual_monthly_consumption=10, 
                                           use_auto_consumption=False)
        ps, created = ProductStock.objects.get_or_create(product=ml, supply_point=dedh, 
                                           manual_monthly_consumption=10, 
                                           use_auto_consumption=False)
        
