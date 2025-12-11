from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, Client, Diploma, ClientDiploma, Institute


class UserSerializer(serializers.ModelSerializer):
    refresh = serializers.CharField(read_only=True, source='token')
    access = serializers.CharField(read_only=True, source='token.access_token')
    class Meta:
        model = User
        fields = [
            "id", "full_name", "email", "identity_number",'refresh', 'access',
            "branch", "profile_picture", "is_active", "password", 'is_superuser', 'is_staff',

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
        fields = ["id", "name", "date",'attendance_mode','type']


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

class DiplomaInputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    selectedType = serializers.CharField(required=False)


class ClientSerializer(serializers.ModelSerializer):
    diplomas = ClientDiplomaSerializer(source="client_diplomas",many=True, read_only=True)
    institute = serializers.IntegerField(write_only=True)
    diploma_id = serializers.IntegerField(write_only=True)
    selectedType = serializers.CharField(write_only=True)

    class Meta:
        model = Client
        fields = [
            "id", "name", "identity_number", "phone_number", "email",
            "sector", "area", "diplomas",'institute','diploma_id','selectedType']

    def create(self, validated_data):

        institute_id = validated_data.pop('institute')
        diploma_id = validated_data.pop('diploma_id')
        selectedType = validated_data.pop('selectedType')
        user = self.context['request'].user
        validated_data['added_by'] = user

        client, created = Client.objects.get_or_create(
            identity_number=validated_data['identity_number'],
            defaults={
                'name': validated_data.get('name'),
                'phone_number': validated_data.get('phone_number'),
                'email': validated_data.get('email'),
                'sector': validated_data.get('sector'),
                'area': validated_data.get('area'),

            }
        )

        existing_diplomas = ClientDiploma.objects.filter(
            client=client,
            diploma_id=diploma_id
        ).values_list('diploma__name', flat=True)

        if existing_diplomas:
            # لو فيه دبلومات موجودة مسبقًا، نرجع خطأ
            raise serializers.ValidationError(
                {"diploma_ids_list": f"العميل موجود بالفعل بالدبلوم/الدبلومات: {', '.join(existing_diplomas)}"}
            )
        institute_obj = Institute.objects.filter(id=institute_id).first()
        if not institute_obj:
            raise serializers.ValidationError({"institute": "المعهد المحدد غير موجود."})
        diploma = Diploma.objects.filter(id=diploma_id).first()
        if diploma:
            cd = ClientDiploma.objects.create(
                    client=client,
                    diploma=diploma,
                    added_by=user,
                    institute=institute_obj,
                    attendance_type=selectedType
            )
        else:
            raise serializers.ValidationError('هذا دبلوم غير متاح حاليا')

        return {
            "id": client.id,
            "name": client.name,
            "identity_number": client.identity_number,
            "phone_number": client.phone_number,
            "email": client.email,
            "sector": client.sector,
            "area": client.area,
            "diplomas": [
                {
                    "client": cd.client.id,
                    "diploma": {
                        "id": cd.diploma.id,
                        "name": cd.diploma.name,
                        "date": cd.diploma.date
                    },
                    "added_at": cd.added_at,
                    # "added_by_name": cd.added_by_name,
                    "added_by": cd.added_by.full_name,
                    "added_by_id": cd.added_by.id
                }
            ]
        }


class ClientDiplomaListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='client.name', read_only=True)
    identity_number = serializers.CharField(source='client.identity_number', read_only=True)
    phone_number = serializers.CharField(source='client.phone_number', read_only=True)
    email = serializers.CharField(source='client.email', read_only=True)
    sector = serializers.CharField(source='client.sector', read_only=True)
    area = serializers.CharField(source='client.area', read_only=True)
    diploma = DiplomaSerializer(read_only=True)
    added_by_name = serializers.CharField(source='added_by.full_name', read_only=True)

    class Meta:
        model = ClientDiploma
        fields = [
            'id',
            'client_id', 'name', 'identity_number', 'sector', 'area','email','phone_number',
            'diploma',
            'added_at',
            'added_by', 'added_by_name'
        ]


class ClientDiplomaReportSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(source="client.id")
    client_name = serializers.CharField(source="client.name")
    identity_number = serializers.CharField(source="client.identity_number")
    phone_number = serializers.CharField(source="client.phone_number")
    email = serializers.EmailField(source="client.email")
    sector = serializers.CharField(source="client.sector")
    area = serializers.CharField(source="client.area")
    diploma_id = serializers.IntegerField(source="diploma.id")
    diploma_name = serializers.CharField(source="diploma.name")
    diploma_date = serializers.DateField(source="diploma.date")
    added_by_name = serializers.CharField(source="added_by.full_name")

    class Meta:
        model = ClientDiploma
        fields = [
            "client_id", "client_name", "identity_number", "phone_number",
            "email", "sector", "area", "diploma_id", "diploma_name", "diploma_date",
            "added_by_name", "added_at"
        ]