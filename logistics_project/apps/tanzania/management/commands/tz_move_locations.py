from logistics.models import SupplyPoint
from django.core.management.base import LabelCommand
import sys
from logistics_project.apps.tanzania.reporting.run_reports import default_start_date, process_non_facility_warehouse_data
from warehouse.models import ReportRun


class Command(LabelCommand):
    help = "For a given list of locations, move them from one parent to another."

    def handle(self, *args, **options):
        strict = True
        facs_to_move = (
            ("D30082", "KILOSA", "GAIRO"),
            ("D30079", "KILOSA", "GAIRO"),
            ("D33574", "KILOSA", "GAIRO"),
            ("D30911", "KILOSA", "GAIRO"),
            ("D30075", "KILOSA", "GAIRO"),
            ("D30083", "KILOSA", "GAIRO"),
            ("D30098", "KILOSA", "GAIRO"),
            ("D30103", "KILOSA", "GAIRO"),
            ("D30914", "KILOSA", "GAIRO"),
            ("D30071", "KILOSA", "GAIRO"),
            ("D30111", "KILOSA", "GAIRO"),
            ("D35264", "KILOSA", "GAIRO"),
            ("D30913", "KILOSA", "GAIRO"),
            ("D30093", "KILOSA", "GAIRO"),
            ("D30084", "KILOSA", "GAIRO"),
        )
        parents = set()
        warehouse_start_date = default_start_date()
        warehouse_end_date = ReportRun.last_success().end
        for code, current_parent_name, new_parent_name in facs_to_move:
            fac = SupplyPoint.objects.get(code=code)
            parent = fac.supplied_by
            expected_parent = SupplyPoint.objects.get(name__iexact=current_parent_name)
            new_parent = SupplyPoint.objects.get(
                type__code=parent.type.code,
                name__iexact=new_parent_name,
            )
            if strict:
                assert parent == expected_parent

            assert fac.location.parent == parent.location
            assert fac.type.code == 'facility'
            assert parent.type.code != 'facility'
            assert new_parent.type.code != 'facility'
            fac.supplied_by = new_parent
            fac.location.parent = new_parent.location
            fac.save()
            parents.update((parent, new_parent))

        for parent in parents:
            # for all affected parents, rerun the aggregate warehouse update
            process_non_facility_warehouse_data(parent, warehouse_start_date, warehouse_end_date, strict=False)
