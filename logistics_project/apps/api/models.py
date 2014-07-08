from django.db import models


class ApiCheckpoint(models.Model):

    domain = models.CharField(max_length=100)
    api_method_name = models.CharField(max_length=30)
    last_sync_model_id = models.IntegerField()
    is_all_goes_fine = models.BooleanField(default=False)