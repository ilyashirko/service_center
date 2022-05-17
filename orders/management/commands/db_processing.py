from ast import Return
from orders.models import DeviceType, Master, Message, Request, Support, TelegramId
from asgiref.sync import sync_to_async
from textwrap import dedent


@sync_to_async
def get_masters_first_last_names():
    return [f'{master.last_name} {master.first_name}' for master in Master.objects.all()]


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
def get_master_id_from_request(uuid):
    master = Request.objects.get(uuid=uuid).master
    if master:
        return Request.objects.get(uuid=uuid).master.telegram_id.telegram_id

@sync_to_async
def get_request(uuid):
    return Request.objects.get(uuid=uuid)

@sync_to_async
def assign_master_for_request(uuid, master_name):
    request = Request.objects.get(uuid=uuid)
    last_name, first_name = master_name.split(' ')
    master = Master.objects.get(first_name=first_name, last_name=last_name)
    request.master = master
    request.save()
    return request.master.telegram_id.telegram_id

@sync_to_async
def get_support_request(uuid):
    return Support.objects.get(uuid=uuid)

@sync_to_async
def close_support_request(uuid, response):
    support_request = Support.objects.get(uuid=uuid)
    support_request.response = response
    support_request.processed = True
    support_request.save()

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
        request=message,
        processed=False
    )
    return new_support_request

@sync_to_async
def get_last_messages(uuid, number = None):
    request = Request.objects.get(uuid=uuid)
    if number:
        messages = Message.objects.filter(request=request).order_by('-created_at')[:number]
    else:
        messages = Message.objects.filter(request=request).order_by('-created_at')
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
        first_name=first_name,
        master=None,
        processed=False
    )
    new_request.save()
    return new_request