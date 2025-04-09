from django.db import models
import pandas as pd

class SheetData(models.Model):
    day = models.CharField(max_length=20)
    date = models.DateField()
    time_session_1 = models.CharField(max_length=50, blank=True, null=True)
    session_1 = models.TextField(blank=True, null=True)
    time_session_2 = models.CharField(max_length=50, blank=True, null=True)
    session_2 = models.TextField(blank=True, null=True)