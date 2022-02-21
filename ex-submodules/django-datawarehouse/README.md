django-datawarehouse
====================

Simple utility wrapper for doing data warehousing in django

To use add a subclass of warehouse.runner.WarehouseRunner to your project and 
add the following to your settings.py

WAREHOUSE_RUNNER = 'path.to.my.runner.MyRunnerClassName'

Then use 

$ ./manage.py update_warehouse 
