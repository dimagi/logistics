# Logistics App

""" 
 Stock policy (i.e. when & how much to reorder) varies across countries & projects. 
 Most deployments will be fine using one stock policy (and the 3 LEVEL settings below)
 Those that require different settings for different facility types should set the
 GLOBAL_STOCK_LEVEL_POLICY to False, and then define the LEVELS in static.deployment.config.py
"""
LOGISTICS_USE_GLOBAL_STOCK_LEVEL_POLICY = True
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
    "LOOKBACK_DAYS": None,          # none is no max
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
LOGISTICS_IGNORE_EMPTY_STOCKS = False # if there is no stock, ignore 0 soh values
LOGISTICS_USE_BACKORDERS = True  # enable back orders or set to false to cancel pending orders on receipt

# set to a non-zero integer to enable max stock thresholds for sms reporting
# the number is the factor of the maximum level that represents the max allowed
# report amount
LOGISTICS_MAX_REPORT_LEVEL_FACTOR = None

# this is the set of allowable values for STOCKED_BY
STOCKED_BY_USER='user' # sp's are responsible for reporting commodities registered to specific users
STOCKED_BY_FACILITY='facility' # sp's are respnsible for reporting commodities registered to specific facilities
STOCKED_BY_PRODUCT='product' # sp's are responsible for reporting commodities marked as 'is_active'
LOGISTICS_STOCKED_BY = STOCKED_BY_USER
