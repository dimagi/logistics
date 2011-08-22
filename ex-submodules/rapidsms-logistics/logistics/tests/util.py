from rapidsms.tests.scripted import TestScript
from logistics import loader as logi_loader

def load_test_data():
    logi_loader.init_reports()
    logi_loader.init_supply_point_types()
    logi_loader.init_test_location_and_supplypoints()
    logi_loader.init_test_product_and_stock()
    