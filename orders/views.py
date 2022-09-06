from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from orders.models import Master
from orders.serializers import MasterSerializer


@csrf_exempt
def master_list(request):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        snippets = Master.objects.all()
        serializer = MasterSerializer(snippets, many=True)
        return JsonResponse(
            serializer.data,
            safe=False,
            json_dumps_params={
                'ensure_ascii': False,
                'indent': 4
            })

    elif request.method == 'POST':
        return JsonResponse(serializer.errors, status=403)
        # data = JSONParser().parse(request)
        # serializer = MasterModelSerializer(data=data)
        # if serializer.is_valid():
        #     serializer.save()
        #     return JsonResponse(serializer.data, status=201)
        # return JsonResponse(serializer.errors, status=400)


@csrf_exempt
def master_detail(request, uuid):
    """
    Retrieve, update or delete a code snippet.
    """
    try:
        master = Master.objects.get(uuid=uuid)
    except Master.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = MasterSerializer(master)
        return JsonResponse(
            serializer.data,
            json_dumps_params={
                'ensure_ascii': False,
                'indent': 4
            })
    else:
        return HttpResponse(status=403)

    # elif request.method == 'PUT':
    #     data = JSONParser().parse(request)
    #     serializer = MasterSerializer(master, data=data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return JsonResponse(serializer.data)
    #     return JsonResponse(serializer.errors, status=400)

    # elif request.method == 'DELETE':
    #     master.delete()
    #     return HttpResponse(status=204)
