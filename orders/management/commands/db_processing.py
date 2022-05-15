from ast import Return
from orders.models import DeviceType, Message, Request, Support, TelegramId
from asgiref.sync import sync_to_async
from textwrap import dedent


@sync_to_async
def get_telegram_object(telegram_id):
    return TelegramId.objects.get(telegram_id=telegram_id)


@sync_to_async
def get_devices_types():
    return [type.title for type in DeviceType.objects.all()]


@sync_to_async
def get_telegram_id_from_request(uuid):
    return Request.objects.get(uuid=uuid).user_telegram_id.telegram_id


@sync_to_async
def get_request(uuid):
    return Request.objects.get(uuid=uuid)

@sync_to_async
def get_support_request(uuid):
    return Support.objects.get(uuid=uuid)

@sync_to_async
def get_telegram_id_from_foreignkey(parent_object):
    return parent_object.telegram_id

@sync_to_async
def add_message(uuid: str, message: str, is_master: bool):
    request = Request.objects.get(uuid=uuid)
    Me = Message.objects.create(
        request=request,
        text=message,
        is_master=is_master
    )
    Me.save()

@sync_to_async
def create_support_request(user_id: int, message: str):
    telegram_id = TelegramId.objects.get(telegram_id=user_id)
    new_support_request = Support.objects.create(
        telegram_id=telegram_id,
        text=message,
        is_actual=True
    )
    return new_support_request

@sync_to_async
def get_last_messages(uuid, number):
    request = Request.objects.get(uuid=uuid)
    messages = Message.objects.filter(request=request).order_by('-created_at')[:number]
    
    text = str()
    for message in reversed(messages):
        if message.is_master:
            text += f'[MASTER]: "{message.text}"\n'
        else:
            text += f'[CUSTOMER]: "{message.text}"\n'
    return text

@sync_to_async
def create_new_request(user_telegram_id,
                       message,
                       phone,
                       user_name,
                       first_name):
    telegram_id_model, _ = TelegramId.objects.get_or_create(telegram_id=user_telegram_id)
    new_request = Request.objects.create(
        user_telegram_id=telegram_id_model,
        request=message,
        phone=phone,
        user_name=user_name,
        first_name=first_name
    )
    new_request.save()
    return new_request