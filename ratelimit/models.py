from django.db import models


class RequestLog(models.Model):
    client_ip = models.GenericIPAddressField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    counter = models.IntegerField()
