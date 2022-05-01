from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Master(models.Model):
    first_name = models.CharField("Имя", max_length=20)
    last_name = models.CharField("Имя", max_length=20)
    patronymic  = models.CharField("Имя", max_length=20)

    phonenumber = PhoneNumberField("Номер телефона")
    

class Customer(models.Model):
    first_name = models.CharField("Имя", max_length=20)
    last_name = models.CharField("Имя", max_length=20)
    patronymic  = models.CharField("Имя", max_length=20, blank=True)

class Device(models.Model):
    pass

class Order(models.Model):
    pass

class Feedback(models.Model):
    pass
