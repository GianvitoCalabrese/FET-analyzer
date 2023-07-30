from django.db import models

class CurveData(models.Model):
    title = models.CharField(max_length=100)
    data_file = models.FileField(upload_to='curve_data/')
