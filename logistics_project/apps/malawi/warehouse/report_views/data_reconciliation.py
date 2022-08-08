from logistics_project.apps.malawi.warehouse import warehouse_view


class View(warehouse_view.MalawiWarehouseView):
    def custom_context(self, request):
        return {
            "show_single_date": True,
        }
