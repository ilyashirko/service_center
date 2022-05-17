from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
import uuid
import datetime
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
    telegram_id = models.ForeignKey(
        "TelegramId",
        on_delete=models.PROTECT,
        verbose_name="Telegram ID",
        related_name="master",
        null=True,
        blank=True
    )
    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class Request(models.Model):
    uuid = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    user_telegram_id = models.ForeignKey(
        "TelegramId",
        on_delete=models.PROTECT,
        verbose_name="Telegram ID",
        related_name="requests",
        null=True,
        blank=True
    )
    request = models.CharField(
        "Сообщение от пользователя",
        max_length=1000
    )
    phone = PhoneNumberField("Номер телефона")
    user_name = models.CharField("TG username", max_length=50, null=True, blank=True)
    first_name = models.CharField("TG first name", max_length=50, null=True, blank=True)
    master = models.ForeignKey(
        "Master",
        on_delete=models.SET_DEFAULT,
        default=None,
        related_name='requests',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        "Сформирован",
        auto_now_add=True,
        editable=False
    )
    processed = models.BooleanField("Заявка отработана", default=False)

    def __str__(self):
        return f"[{datetime.datetime.strftime(self.created_at, '%Y-%m-%d %H:%m')}]: {self.user_name} ({self.phone}) - {self.request}"


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

    devices = models.ManyToManyField(
        "Device",
        verbose_name="Устройства",
        related_name="owner",
        blank=True
    )

    feedbacks = models.OneToOneField(
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
        max_length=500
    )

    response = models.TextField(
        "Ответ от администратора",
        max_length=500,
        null=True,
        blank=True
    )
    created_at = models.DateField(
        "Дата отзыва",
        auto_now_add=True,
        editable=False
    )


class TelegramId(models.Model):
    telegram_id = models.SmallIntegerField("Telegram ID", unique=True)

    def __str__(self):
        return str(self.telegram_id)

class Message(models.Model):
    text = models.CharField("Сообщение", max_length=1000)
    request = models.ForeignKey(
        'Request',
        verbose_name="Переписка",
        related_name="messages",
        on_delete=models.PROTECT,
        null=True,
        blank=True
    ) 
    created_at = models.DateTimeField(
        "Отправлено",
        auto_now_add=True,
        editable=False
    )
    is_master = models.BooleanField("Сообщение от мастера", default=None, null=True)


class Support(models.Model):
    uuid = models.CharField(
        "id",
        unique=True,
        default=uuid.uuid1,
        max_length=36,
        validators=[MinLengthValidator(36)],
        primary_key=True,
        editable=False
    )
    telegram_id = models.ForeignKey(
        "TelegramId",
        on_delete=models.PROTECT,
        verbose_name="Telegram ID",
        related_name="support"
    )
    request = models.CharField("Сообщение", max_length=1000)
    response = models.CharField("Ответ", max_length=1000, blank=True)
    created_at = models.DateTimeField(
        "Отправлено",
        auto_now_add=True,
        editable=False
    )
    processed = models.BooleanField("Заявка отработана")