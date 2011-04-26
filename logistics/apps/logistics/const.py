'''
Constants go here
'''


class Reports(object):
    """
    Types of reports
    """
    SOH = "soh"
    REC = "rec"
    GIVE = "give"
    EMERGENCY_SOH = "eo" # eo = emergency order
    ALL_REPORTS = {
        SOH: "stock on hand",
        REC: "stock received",
        GIVE: "stock given",
        EMERGENCY_SOH: "emergency stock on hand"
    }

