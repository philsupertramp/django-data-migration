from django.db import models


class Customer(models.Model):
    first_name = models.CharField(max_length=1, null=True)
    last_name = models.CharField(max_length=1, null=True)
    address_line_1 = models.CharField(max_length=255, null=True)
    address_line_2 = models.CharField(max_length=255, null=True)
    is_business = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class MModel(models.Model):
    bit = models.BooleanField()
    name = models.CharField(max_length=2, null=True)
