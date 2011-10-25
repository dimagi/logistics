# Logistics App
# These settings define how many months constitute emergency, low supply,
# and oversupply stock for the logistics app
LOGISTICS_EMERGENCY_LEVEL_IN_MONTHS = 0.5
LOGISTICS_REORDER_LEVEL_IN_MONTHS = 1.5
LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS = 3
LOGISTICS_DEFAULT_PRODUCT_ACTIVATION_STATUS = True
LOGISTICS_AGGRESSIVE_SOH_PARSING = True # whether to parse ~all messages as stock reports
LOGISTICS_EXCEL_EXPORT_ENABLED = True
LOGISTICS_MINIMUM_DAYS_TO_CALCULATE_CONSUMPTION=10
LOGISTICS_MINIMUM_NUM_TRANSACTIONS_TO_CALCULATE_CONSUMPTION=1
LOGISTICS_USE_STATIC_EMERGENCY_LEVELS = False
LOGISTICS_USE_AUTO_CONSUMPTION = False
LOGISTICS_REPORTING_CYCLE_IN_DAYS = 7
LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT = 7
LOGISTICS_DAYS_UNTIL_DATA_UNAVAILABLE = 21
LOGISTICS_USE_AUTO_CONSUMPTION = False
LOGISTICS_PRODUCT_ALIASES = {} # you can add aliases for products here.
LOGISTICS_USE_DEFAULT_HANDLERS = True
LOGISTICS_USE_LOCATION_SESSIONS = False # keep persistent locations across requests in cookies
LOGISTICS_NAVIGATION_MODE = "url" # "url" or "param", depending how your site navigation works
LOGISTICS_USE_SPOT_CACHING = False # use spot caches in various places we've found performance hits
LOGISTICS_SPOT_CACHE_TIMEOUT = 60 * 60 # spot cache timeout, in seconds, defaults to an hour
