from logistics_project.apps.malawi.warehouse import warehouse_view

class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        table = {
            "id": "hsa-reporting-summary",
            "is_datatable": False,
            "header": ["Months", "On Time", "Late", "Complete"],
            "data": [['Jan', 33, 42, 53], ['Feb', 22, 25, 41], ['Mar', 41, 41, 46]],
        }

        table2 = {
            "id": "calc-consumption-stock-levels",
            "is_datatable": False,
            "header": ["Product", "Total Calc Cons", "Avg Rep Rate", "AMC", "Total SOH", "Avg MOS",
                "Avg Days Stocked Out", "Total Adj Calc Cons", "Resupply Qts Required"],
            "data": [['CC', 33, 42, 53, 23, 0, 2, 4, 2]],
        }

        table3 = {
            "id": "order-response-time",
            "is_datatable": False,
            "header": ["Product", "Is Emergency", "Balance", "Amt Requested", "Amt Received", "Requested On",
                "Responded On", "Received On", "Status"],
            "data": [['CC', 33, 42, 53, 23, 0, 2, 4, 2]],
        }

        table4 = {
            "id": "recent-messages",
            "is_datatable": False,
            "header": ["Date", "Message Text"],
            "data": [['2012-05-04', 'soh cc 12']],
        }

        table5 = {
            "id": "hsa-details",
            "is_datatable": False,
            "header": ["", ""],
            "data": [['District', 'BULA']],
        }


        return {"table": table,
                "table2": table2,
                "table3": table3,
                "table4": table4,
                "table5": table5,
        }