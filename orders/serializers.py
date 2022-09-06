from django.contrib.auth.models import User
from orders.models import Master, Request, TelegramId
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers, viewsets


# class UserSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = User
#         fields = ['url', 'username', 'email', 'is_staff']
#         # permission_classes = [permissions.IsAuthenticated]


# class UserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     # permission_classes = [permissions.IsAuthenticated]


# class MasterHyperlinkedModelSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = Master


# class MasterHyperlinkedModelViewSet(viewsets.ModelViewSet):
#     queryset = Master.objects.all
#     serializer_class = MasterHyperlinkedModelSerializer


class MasterSerializer(serializers.Serializer):
    uuid = serializers.CharField(read_only=True)
    first_name = serializers.CharField()
    # last_name = serializers.CharField()
    # patronymic = serializers.CharField()
    # phonenumber = PhoneNumberField()
    # photo = serializers.ImageField(required=False)
    # telegram_id = serializers.CharField(required=False)
    requests = serializers.SerializerMethodField()
    
    def __create(self, validated_data):
        """
        Create and return a new `Snippet` instance, given the validated data.
        """
        return Master.objects.create(**validated_data)

    def __update(self, instance, validated_data):
        
        """
        Update and return an existing `Snippet` instance, given the validated data.
        """
        instance.uuid = validated_data.get('uuid', instance.uuid)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.patronymic = validated_data.get('patronymic', instance.patronymic)
        instance.phonenumber = validated_data.get('phonenumber', instance.phonenumber)
        instance.photo = validated_data.get('photo', instance.photo)
        instance.telegram_id = validated_data.get('telegram_id', instance.telegram_id)
        instance.requests = validated_data.get('requests', instance.requests)
        return instance
    
    def get_requests(self, obj):
        queryset = Request.objects.filter(master=obj)
        return [RequestModelSerializer(request).data for request in queryset]


class MasterViewSet(viewsets.ModelViewSet):
    queryset = Master.objects.all()
    serializer_class = MasterSerializer
    # permission_classes = [permissions.IsAuthenticated]


class RequestModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = [
            'uuid',
            'master',
            'created_at',
            'processed'
        ]

# class MasterModelSerializer(serializers.ModelSerializer):
#     telegram_id = serializers.SerializerMethodField()
#     requests = serializers.SerializerMethodField()

#     class Meta:
#         model = Master
#         fields = [
#             'uuid',
#             'first_name',
#             'last_name',
#             'patronymic',
#             'phonenumber',
#             'photo',
#             'telegram_id',
#             'requests'
#         ]
    
#     def get_requests(self, obj):
#         queryset = Request.objects.filter(master=obj)
#         return [RequestModelSerializer(request).data for request in queryset]
    
#     def get_telegram_id(self, obj):
#         return obj.telegram_id.telegram_id


# class MasterModelViewSet(viewsets.ModelViewSet):
#     queryset = Master.objects.all()
#     serializer_class = MasterModelSerializer
#     # permission_classes = [permissions.IsAuthenticated]