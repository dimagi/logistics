from logistics.models import Product
from logistics_project.apps.malawi.warehouse import warehouse_view


CONDITION_DIARRHEA = "Diarrhea"
CONDITION_UNCOMPLICATED_MALARIA_YOUNG = "Uncomplicated Malaria (5 - 35 months)"
CONDITION_UNCOMPLICATED_MALARIA_OLD = "Uncomplicated Malaria (36 - 59 months)"
CONDITION_PNEUMONIA_YOUNG = "Fast breathing - Pneumonia (2 - 11 months)"
CONDITION_PNEUMONIA_OLD = "Fast breathing - Pneumonia (12 - 59 months)"
CONDITION_SEVERE_MALARIA = "Severe malaria (All age groups)"
CONDITION_MALNUTRITION = "Malnutrition"
CONDITION_MRDT = "MRDT"

CONDITIONS = [
    CONDITION_DIARRHEA,
    CONDITION_UNCOMPLICATED_MALARIA_YOUNG,
    CONDITION_UNCOMPLICATED_MALARIA_OLD,
    CONDITION_PNEUMONIA_YOUNG,
    CONDITION_PNEUMONIA_OLD,
    CONDITION_SEVERE_MALARIA,
    CONDITION_MALNUTRITION,
    CONDITION_MRDT,
]


def _get_product_for_condition(condition):
    condition_code_map = {
        CONDITION_DIARRHEA: 'or',
        CONDITION_UNCOMPLICATED_MALARIA_YOUNG: 'la',
        CONDITION_UNCOMPLICATED_MALARIA_OLD: 'lb',
        CONDITION_PNEUMONIA_YOUNG: 'AM',
        CONDITION_PNEUMONIA_OLD: 'AM',
        CONDITION_SEVERE_MALARIA: 'RA',
        CONDITION_MALNUTRITION: 'RU',
        CONDITION_MRDT: 'MT',
    }
    return Product.objects.get(sms_code__iexact=condition_code_map[condition])


def _build_condition_row(condition, supply_point, month):
    product = _get_product_for_condition(condition)
    return [
        condition,
        100,
        product.name,
        200,
    ]


class View(warehouse_view.MalawiWarehouseView):
    def custom_context(self, request):
        # get consumption data
        reporting_sp = self.get_reporting_supply_point(request)
        month = request.datespan.enddate
        main_table_headers = [
            'Condition',
            '# Cases',
            'Product',
            'Medicines/Commodities Dispensed'
        ]
        main_table_rows = self._get_main_table_rows(reporting_sp, month)
        extra_rows = [
            [
                'Total Malaria Cases',
                300,
                '-',
                '-',
            ],
            [
                'Total Fast breathing - Pneumonia Cases',
                200,
                '-',
                '-',
            ]
        ]
        main_table = {
            "is_datatable": False,
            "is_downloadable": False,
            "header": main_table_headers,
            "data": main_table_rows + extra_rows,
        }
        return {
            "show_single_date": True,
            "main_table": main_table,
            'uncomplicated_malaria_breakdown_table': {
                "is_datatable": False,
                "is_downloadable": False,
                "header": ['Age Group', 'Percent of Cases'],
                "data": [
                    [CONDITION_UNCOMPLICATED_MALARIA_YOUNG, '50%'],
                    [CONDITION_UNCOMPLICATED_MALARIA_OLD, '50%'],
                ]
            },
            'all_malaria_breakdown_table': {
                "is_datatable": False,
                "is_downloadable": False,
                "header": ['Age Group', 'Percent of Cases'],
                "data": [
                    [CONDITION_UNCOMPLICATED_MALARIA_YOUNG, '40%'],
                    [CONDITION_UNCOMPLICATED_MALARIA_OLD, '30%'],
                    [CONDITION_SEVERE_MALARIA, '30%'],
                ]
            }
        }

    def _get_main_table_rows(self, supply_point, month):
        return [
            _build_condition_row(condition, supply_point, month)
            for condition in CONDITIONS
        ]


