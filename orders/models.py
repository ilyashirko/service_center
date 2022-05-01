from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
import uuid
from django.core.validators import MinLengthValidator


class Master(models.Model):
    uuid = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    first_name = models.CharField("Имя", max_length=20)
    last_name = models.CharField("Фамилия", max_length=20)
    patronymic  = models.CharField("Отчество", max_length=20)
    phonenumber = PhoneNumberField("Номер телефона")
    photo = models.ImageField("Фото", blank=True)

    def __str__(self):
        return f'{self.last_name} {self.first_name}'
    

class Customer(models.Model):
    uuid = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    first_name = models.CharField("Имя", max_length=20)
    last_name = models.CharField("Фамилия", max_length=20)
    patronymic  = models.CharField("Отчество", max_length=20, blank=True)

    phonenumber = PhoneNumberField("Номер телефона")
    extra_phonenumber = PhoneNumberField("Дополнительный номер телефона", blank=True)

    mail = models.EmailField("Электронная почта", blank=True)

    devices = models.ForeignKey(
        "Device",
        on_delete=models.PROTECT,
        verbose_name="Устройства",
        related_name="owner",
        null=True,
        blank=True
    )

    feedbacks = models.ForeignKey(
        "Feedback",
        on_delete=models.PROTECT,
        verbose_name="Отзывы",
        related_name="customer",
        null=True,
        blank=True
    )

    telegram_id = models.ForeignKey(
        "TelegramId",
        on_delete=models.PROTECT,
        verbose_name="Telegram ID",
        related_name="customer",
        null=True,
        blank=True
    )

    def __str__(self):
        return f'{self.first_name} {self.last_name}{f" ({self.phonenumber})" if self.phonenumber else ""}'

class Device(models.Model):
    uuid = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    device_type = models.ForeignKey(
        "DeviceType",
        on_delete=models.PROTECT,
        verbose_name="Тип устройства",
        related_name="devices"
    )
    brand = models.CharField("Производитель", max_length=20)
    model = models.CharField("Модель", max_length=20)
    serial = models.CharField("Серийный номер", max_length=50, blank=True)
    imei = models.CharField("IMEI", max_length=20, blank=True)

    def __str__(self):
        text = f'{self.device_type}: {self.brand} {self.model}'
        if self.serial:
            text += f' (s/n: {self.serial})'
        if self.imei:
            text += f' (imei: {self.imei})'
        return text


class DeviceType(models.Model):
    title = models.CharField("Тип устройства", max_length=20)

    def __str__(self):
        return self.title


class Order(models.Model):
    uuid = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    device = models.ForeignKey(
        "Device",
        on_delete=models.PROTECT,
        verbose_name="Устройство",
        related_name="orders"
    )

    condition = models.CharField(
        "Состояние устройства",
        default='Следы эксплуатации',
        max_length=500
    )

    customer = models.ForeignKey(
        "Customer",
        on_delete=models.PROTECT,
        verbose_name="Клиент",
        related_name="orders"
    )

    master = models.ForeignKey(
        "Master",
        on_delete=models.PROTECT,
        verbose_name="Мастер",
        related_name="orders"
    )

    admiss_date = models.DateField(
        "Дата приема",
        auto_now_add=True
    )

    return_date = models.DateField(
        "Дата выдачи",
        null=True,
        blank=True
    )

    comment = models.TextField(
        "Дополнительная информация",
        max_length=1000,
        blank=True
    )

    def __str__(self):
        text = f'{self.device}' 
        if self.admiss_date:
            text += f' | принят: {self.admiss_date}'
        if self.return_date:
            text += f' | возвращен: {self.return_date}'
        return text


class Feedback(models.Model):
    uuid = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    order = models.ForeignKey(
        "Order",
        on_delete=models.PROTECT,
        verbose_name="Заказ",
        related_name="order"
    )

    text = models.TextField(
        "Текст отзыва",
        max_length=2000
    )

    created_at = models.DateField(
        "Дата отзыва",
        auto_now_add=True
    )


class TelegramId(models.Model):
    telegram_id = models.SmallIntegerField("Telegram ID")
