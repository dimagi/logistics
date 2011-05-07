# Logistics App
# These settings define how many months constitute emergency, low supply,
# and oversupply stock for the logistics app
LOGISTICS_EMERGENCY_LEVEL_IN_MONTHS = 0.5
LOGISTICS_REORDER_LEVEL_IN_MONTHS = 1.5
LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS = 3
LOGISTICS_DEFAULT_PRODUCT_ACTIVATION_STATUS = False
LOGISTICS_AGGRESSIVE_SOH_PARSING = True # whether to parse ~all messages as stock reports
LOGISTICS_GHANA_HACK_CREATE_SCHEDULES = False # whether to do the hard-coded schedule creation
LOGISTICS_EXCEL_EXPORT_ENABLED = True
LOGISTICS_MINIMUM_DAYS_TO_CALCULATE_CONSUMPTION=10
