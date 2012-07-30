from warehouse.runner import WarehouseRunner

class MalawiWarehouseRunner(WarehouseRunner):
    """
    Malawi's implementation of the warehouse runner. 
    """
    
    def cleanup(self, start=None, end=None):
        print "Malawi warehouse cleanup!"  
    
    def generate(self, start=None, end=None):
        print "Malawi warehouse generate!"
    
    
