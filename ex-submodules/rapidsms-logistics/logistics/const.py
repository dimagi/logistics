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
    LOSS_ADJUST = "la" # la = losses & adjustments
    ALL_REPORTS = {
        SOH: "stock on hand",
        REC: "stock received",
        GIVE: "stock given",
        EMERGENCY_SOH: "emergency stock on hand",
        LOSS_ADJUST: "loss or adjustment" 
    }

