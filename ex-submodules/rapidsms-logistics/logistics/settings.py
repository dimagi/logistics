# Logistics App
# These settings define how many months constitute emergency, low supply,
# and oversupply stock for the logistics app
LOGISTICS_EMERGENCY_LEVEL_IN_MONTHS = 0.5
LOGISTICS_REORDER_LEVEL_IN_MONTHS = 1.5
LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS = 3
LOGISTICS_DEFAULT_PRODUCT_ACTIVATION_STATUS = True
LOGISTICS_AGGRESSIVE_SOH_PARSING = True # whether to parse ~all messages as stock reports
LOGISTICS_EXCEL_EXPORT_ENABLED = True

LOGISTICS_CONSUMPTION = {
    "MINIMUM_TRANSACTIONS": 2,
    "MINIMUM_DAYS": 10,
    "MAXIMUM_DAYS": None,          # none is no max
    "INCLUDE_END_STOCKOUTS": False, # whether or not to include periods ending in a stockout
    
}

LOGISTICS_USE_STATIC_EMERGENCY_LEVELS = False
LOGISTICS_USE_AUTO_CONSUMPTION = False
LOGISTICS_REPORTING_CYCLE_IN_DAYS = 7
LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT = 7
LOGISTICS_DAYS_UNTIL_DATA_UNAVAILABLE = 21
LOGISTICS_PRODUCT_ALIASES = {} # you can add aliases for products here.
LOGISTICS_USE_DEFAULT_HANDLERS = True
LOGISTICS_USE_LOCATION_SESSIONS = False # keep persistent locations across requests in cookies
LOGISTICS_NAVIGATION_MODE = "url" # "url" or "param", depending how your site navigation works
LOGISTICS_USE_SPOT_CACHING = False # use spot caches in various places we've found performance hits
LOGISTICS_SPOT_CACHE_TIMEOUT = 60 * 60 # spot cache timeout, in seconds, defaults to an hour
class StockedBy:
    # this is the set of allowable values for STOCKED_BY
    USER='user' # sp's are responsible for reporting commodities registered to specific users
    FACILITY='facility' # sp's are respnsible for reporting commodities registered to specific facilities
    PRODUCT='product' # sp's are responsible for reporting commodities marked as 'is_active'
LOGISTICS_STOCKED_BY = StockedBy.USER
