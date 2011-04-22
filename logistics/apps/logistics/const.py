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
    ALL_REPORTS = {
        SOH: "stock on hand",
        REC: "stock received",
        GIVE: "stock given"
    }

