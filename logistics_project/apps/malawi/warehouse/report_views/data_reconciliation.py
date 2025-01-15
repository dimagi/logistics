import sentry_sdk
from logistics.models import Product
from logistics.reports import calc_percentage, format_percentage
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.warehouse.models import CalculatedConsumption

CONDITION_DIARRHEA = "Diarrhea"
CONDITION_UNCOMPLICATED_MALARIA_YOUNG = "Uncomplicated Malaria (5 - 35 months)"
CONDITION_UNCOMPLICATED_MALARIA_OLD = "Uncomplicated Malaria (36 - 59 months)"
CONDITION_SEVERE_MALARIA = "Severe malaria (All age groups)"
CONDITION_MRDT = "Malaria RDT"
CONDITION_PNEUMONIA_YOUNG = "Fast breathing - Pneumonia (2 - 11 months)"
CONDITION_PNEUMONIA_OLD = "Fast breathing - Pneumonia (12 - 59 months)"
CONDITION_MALNUTRITION = "Malnutrition"

CONDITIONS = [
    CONDITION_UNCOMPLICATED_MALARIA_YOUNG,
    CONDITION_UNCOMPLICATED_MALARIA_OLD,
    CONDITION_SEVERE_MALARIA,
    CONDITION_MRDT,
    CONDITION_PNEUMONIA_YOUNG,
    CONDITION_PNEUMONIA_OLD,
    CONDITION_DIARRHEA,
    CONDITION_MALNUTRITION,
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


def _get_cases_for_consumption_amount(condition, consumption):
    consumption_display = consumption
    cases = None
    if condition == CONDITION_DIARRHEA:
        # 3 sachets of ORS treatment per case
        cases = consumption / 3
    elif condition == CONDITION_UNCOMPLICATED_MALARIA_YOUNG:
        # 6 tablets treatment per case
        cases = consumption / 6
    elif condition == CONDITION_UNCOMPLICATED_MALARIA_OLD:
        # 12 tablets treatment per case
        cases = consumption / 12
    elif condition == CONDITION_PNEUMONIA_YOUNG:
        # 3/17th of the pills (30% of cases) go @ 10 per case
        used_consumption = (consumption * 3 / 17)
        cases = used_consumption / 10
        consumption_display = round(used_consumption)
    elif condition == CONDITION_PNEUMONIA_OLD:
        # 14/17th of the pills (70% of cases) go @ 20 per case
        used_consumption = (consumption * 14 / 17)
        cases = used_consumption / 20
        consumption_display = round(used_consumption)
    elif condition == CONDITION_SEVERE_MALARIA:
        # Dosage per case: 1 suppository
        cases = consumption / 1
    elif condition == CONDITION_MALNUTRITION:
        # 2 per day @ 1 month
        cases = consumption / 60
    elif condition == CONDITION_MRDT:
        # 1 test kit treatment per case
        cases = consumption / 1
    return round(cases), consumption_display

def _build_condition_row(condition, supply_point, month):
    def _get_product_display_name(product):
        if product.code == 'MT':
            return "MRDTs"
        else:
            return product.name
    product = _get_product_for_condition(condition)
    try:
        consumption = CalculatedConsumption.objects.get(
            supply_point=supply_point,
            product=product,
            date=month,
        )
    except CalculatedConsumption.DoesNotExist as e:
        sentry_sdk.capture_exception(e)
        cases, consumption_display = 0, 0
    else:
        cases, consumption_display = _get_cases_for_consumption_amount(condition, consumption.calculated_consumption)
    return [
        condition,
        _get_product_display_name(product),
        consumption_display,
        cases,
    ]


def _get_total_malaria_row(main_table_rows):
    return _get_total_row(
        main_table_rows, 'Total Malaria Cases',
        (CONDITION_UNCOMPLICATED_MALARIA_YOUNG, CONDITION_UNCOMPLICATED_MALARIA_OLD, CONDITION_SEVERE_MALARIA),
    )

def _get_total_pneumonia_row(main_table_rows):
    return _get_total_row(main_table_rows, 'Total Fast breathing - Pneumonia Cases',
                          (CONDITION_PNEUMONIA_YOUNG, CONDITION_PNEUMONIA_OLD))

def _get_total_row(main_table_rows, title, matching_conditions):
    total_cases = total_dispensed = 0
    for row in main_table_rows:
        if row[0] in matching_conditions:
            total_dispensed += row[2]
            total_cases += row[3]

    def _strong(value):
        return f'<strong>{value}</strong>'
    return [_strong(v) for v in [title, '-', total_dispensed, total_cases]]


def _get_data_row_by_condition(rows, condition):
    for row in rows:
        if row[0] == condition:
            return row

class View(warehouse_view.MalawiWarehouseView):
    def custom_context(self, request):
        # get consumption data
        reporting_sp = self.get_reporting_supply_point(request)
        month = request.datespan.enddate
        main_table_headers = [
            'Condition',
            'Product',
            'Products Dispensed',
            '# Cases',
        ]
        main_table_rows = self._get_main_table_rows(reporting_sp, month)
        malaria_total_row = _get_total_malaria_row(main_table_rows)
        pneumonia_total_row = _get_total_pneumonia_row(main_table_rows)
        main_table_rows.insert(3, malaria_total_row)
        main_table_rows.insert(7, pneumonia_total_row)

        main_table = {
            "is_datatable": False,
            "is_downloadable": False,
            "header": main_table_headers,
            "data": main_table_rows,
        }

        uncomplicated_malaria_young_cases = _get_data_row_by_condition(
            main_table_rows, CONDITION_UNCOMPLICATED_MALARIA_YOUNG
        )[3]
        uncomplicated_malaria_old_cases = _get_data_row_by_condition(
            main_table_rows, CONDITION_UNCOMPLICATED_MALARIA_OLD
        )[3]
        severe_malaria_cases = _get_data_row_by_condition(
            main_table_rows, CONDITION_SEVERE_MALARIA
        )[3]
        total_uncomplicated = uncomplicated_malaria_young_cases + uncomplicated_malaria_old_cases
        total_malaria = total_uncomplicated + severe_malaria_cases
        return {
            "show_single_date": True,
            "main_table": main_table,
            'uncomplicated_malaria_breakdown_table': {
                "is_datatable": False,
                "is_downloadable": False,
                "header": ['Age Group', 'Percent of Cases'],
                "data": [
                    [CONDITION_UNCOMPLICATED_MALARIA_YOUNG, format_percentage(uncomplicated_malaria_young_cases, total_uncomplicated)],
                    [CONDITION_UNCOMPLICATED_MALARIA_OLD, format_percentage(uncomplicated_malaria_old_cases, total_uncomplicated)],
                ]
            },
            'all_malaria_breakdown_table': {
                "is_datatable": False,
                "is_downloadable": False,
                "header": ['Age Group', 'Percent of Cases'],
                "data": [
                    [CONDITION_UNCOMPLICATED_MALARIA_YOUNG, format_percentage(uncomplicated_malaria_young_cases, total_malaria)],
                    [CONDITION_UNCOMPLICATED_MALARIA_OLD, format_percentage(uncomplicated_malaria_old_cases, total_malaria)],
                    [CONDITION_SEVERE_MALARIA, format_percentage(severe_malaria_cases, total_malaria)],
                ]
            }
        }

    def _get_main_table_rows(self, supply_point, month):
        return [
            _build_condition_row(condition, supply_point, month)
            for condition in CONDITIONS
        ]
