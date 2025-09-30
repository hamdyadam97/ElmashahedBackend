from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, Client, Diploma, ClientDiploma


class UserSerializer(serializers.ModelSerializer):
    refresh = serializers.CharField(read_only=True, source='token')
    access = serializers.CharField(read_only=True, source='token.access_token')
    class Meta:
        model = User
        fields = [
            "id", "full_name", "email", "identity_number",'refresh', 'access',
            "branch", "profile_picture", "is_active", "password", 'is_Superuser', 'is_staff',

        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }


    def validate_password(self, data):
        validate_password(data)
        return data

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        # user = User.objects.create_user(**validated_data)
        return user


    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance




class LoginSerializer(serializers.Serializer):
    identity_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identity_number = data.get("identity_number")
        password = data.get("password")

        if identity_number and password:
            # نبحث عن المستخدم أولاً
            try:
                user = User.objects.get(identity_number=identity_number)
            except User.DoesNotExist:
                raise serializers.ValidationError("رقم الهوية أو كلمة المرور غير صحيحة")

            # نتحقق من الباسورد
            if not user.check_password(password):
                raise serializers.ValidationError("رقم الهوية أو كلمة المرور غير صحيحة")

            if not user.is_active:
                raise serializers.ValidationError("الحساب غير مفعل")
        else:
            raise serializers.ValidationError("يجب إدخال رقم الهوية وكلمة المرور")

        data["user"] = user
        return data



class DiplomaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diploma
        fields = ["id", "name", "date"]


class ClientDiplomaSerializer(serializers.ModelSerializer):
    diploma = DiplomaSerializer(read_only=True)
    added_by_name = serializers.CharField(source='added_by.full_name', read_only=True)
    class Meta:
        model = ClientDiploma
        fields = ['client', 'diploma', 'added_at','added_by_name','added_by']
        read_only_fields = ['added_at', 'added_by']

    def validate(self, attrs):
        client = attrs.get('client')
        diploma = attrs.get('diploma')

        # التحقق من وجود العميل
        if not Client.objects.filter(id=client.id).exists():
            raise serializers.ValidationError({"client": "العميل غير موجود."})

        # التحقق من وجود الدبلوم
        if not Diploma.objects.filter(id=diploma.id).exists():
            raise serializers.ValidationError({"diploma": "الدبلوم غير موجود."})

        # التحقق من عدم التكرار
        if ClientDiploma.objects.filter(client=client, diploma=diploma).exists():
            raise serializers.ValidationError("هذا العميل لديه هذا الدبلوم بالفعل")

        return attrs




class ClientSerializer(serializers.ModelSerializer):
    diplomas = ClientDiplomaSerializer(source="client_diplomas",many=True, read_only=True)
    diplomas_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )


    class Meta:
        model = Client
        fields = [
            "id", "name", "identity_number", "phone_number", "email",
            "sector", "area", "diplomas", "diplomas_ids",
        ]


    def create(self, validated_data):
        diplomas_ids = validated_data.pop('diplomas_ids', [])
        user = self.context['request'].user
        validated_data['added_by'] = user

        # إنشاء العميل أو جلبه إذا موجود
        client, created = Client.objects.get_or_create(
            identity_number=validated_data['identity_number'],
            defaults=validated_data
        )

        # إضافة الدبلومات مع تفادي التكرار
        for diploma_id in diplomas_ids:
            diploma = Diploma.objects.get(id=diploma_id)
            ClientDiploma.objects.get_or_create(client=client, diploma=diploma)

        return client


class ClientDiplomaListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='client.name', read_only=True)
    identity_number = serializers.CharField(source='client.identity_number', read_only=True)
    sector = serializers.CharField(source='client.sector', read_only=True)
    area = serializers.CharField(source='client.area', read_only=True)
    diploma = DiplomaSerializer(read_only=True)
    added_by_name = serializers.CharField(source='added_by.full_name', read_only=True)

    class Meta:
        model = ClientDiploma
        fields = [
            'id',
            'client_id', 'name', 'identity_number', 'sector', 'area',
            'diploma',
            'added_at',
            'added_by', 'added_by_name'
        ]