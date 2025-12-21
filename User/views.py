
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.templatetags.static import static  # <--- هذا السطر مهم
from datetime import datetime, timedelta
from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .filters import ClientDiplomaFilter
from .models import User, Diploma, Client, ClientDiploma
from .serializers import UserSerializer, DiplomaSerializer, ClientSerializer, ClientDiplomaListSerializer, \
    ClientDiplomaReportSerializer


class UserListCreateAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    # permission_classes = [IsAdminUser]
    serializer_class = UserSerializer


class UserRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDeleteAPIView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer



# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer

class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        return Response({
            "success": True,
            "data": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "identity_number": user.identity_number,
                "branch": user.branch,
                "profile_picture": user.profile_picture.url if user.profile_picture else None,
                "is_active": user.is_active,
                "refresh": str(refresh),
                "access": access,
                'is_Superuser': user.is_superuser,
                'is_staff': user.is_staff,
            }
        }, status=status.HTTP_200_OK)


class DiplomaListCreateView(generics.ListCreateAPIView):
    queryset = Diploma.objects.all()
    serializer_class = DiplomaSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Diploma.objects.all()

        # جلب باراميتر type من الـ URL
        diploma_type = self.request.query_params.get('type', None)

        # فلترة حسب النوع إذا تم إرساله
        if diploma_type:
            queryset = queryset.filter(type=diploma_type)

        print(queryset)
        return queryset

class DiplomaRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Diploma.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = DiplomaSerializer


class ClientCreateView(generics.CreateAPIView):
    queryset = Client.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ClientSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_data = serializer.save()
        return Response({
            "data": client_data
        }, status=status.HTTP_201_CREATED)


class ClientRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Client.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ClientSerializer





def client_diploma_pdf(request, client_id, diploma_id):
    client = get_object_or_404(Client, id=client_id)
    client_diploma = client.client_diplomas.filter(diploma_id=diploma_id).first()
    if not client_diploma:
        return HttpResponse("الدبلوم غير موجود للعميل.", status=404)

    diploma = client_diploma.diploma
    institute = getattr(client_diploma, 'institute', None)

    # إعداد القوالب والخلفيات والختم
    institute_templates = {
        'Afaq Al-Tatawor Higher Institute for Training': {
            'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html',
            'bg': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.jpg',
            'seal': 'Afaq-seal.png',
            'signature': 'Signature-Faw-Advanced.png'
        },
        'Al-Ahli Higher Institute': {
            'template': 'Al-AhliHigherInstitute–ArarSakakaAl-Qurayyat.html',
            'bg': 'Al-AhliHigherInstitute–ArarSakakaAl-Qurayyat.jpeg',
            'seal': 'Faw-Advanced-seal.png',
            'signature': 'Signature-Faw-Advanced.png'
        },
        'Al-Faw Advanced Higher Institute for Training': {
            'template': 'Al-FawAdvancedHigherInstituteforTraining.html',
            'bg': 'Al-FawAdvancedHigherInstituteforTraining.png',
            'seal': 'Faw-Advanced-seal.png',
            'signature': 'Signature-Faw-Advanced.png'
        },
        'Al-Faw Specialized Higher Institute for Training': {
            'template': 'Al-FawSpecializedHigherInstituteforTraining–Qassim.html',
            'bg': 'Al-FawSpecializedHigherInstituteforTraining–Qassim.jpeg',
            'seal': 'Specialized-Seal.png',
            'signature':'Specialized-Signature.png'
        },
    }

    # لو المعهد مش في القائمة، استخدم الافتراضي
    area_settings = institute_templates.get(
        institute.name if institute else None,
        {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'Afaq.jpg', 'seal': 'default-seal.png'}
    )
    bg_url = request.build_absolute_uri(static(area_settings['bg']))
    seal_url = request.build_absolute_uri(static(area_settings['seal']))
    signature_url = request.build_absolute_uri(static(area_settings['signature']))

    # تمرير البيانات إلى القالب
    context = {
        "client": client,
        "diplomas": [diploma],
        "bg_url": bg_url,
        "seal_url": seal_url,  # << هنا بنضيف صورة الختم
        "signature_url": signature_url,  # << هنا بنضيف صورة الختم
        "institute_name": institute.name if institute else "",
    }

    # توليد الـ HTML و PDF
    html_string = render_to_string(area_settings['template'], context)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response['Content-Disposition'] = f'inline; filename="client_{client.id}_diploma_{diploma.id}.pdf"'
    return response




class ClientDiplomaListView(generics.ListAPIView):
    serializer_class = ClientDiplomaListSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        queryset = ClientDiploma.objects.select_related('client', 'diploma', 'added_by').all()
        sector = self.request.query_params.get("sector")
        area = self.request.query_params.get("area")
        search = self.request.query_params.get("search")

        if sector:
            queryset = queryset.filter(client__sector=sector)
        if area:
            queryset = queryset.filter(client__area=area)
        if search:
            queryset = queryset.filter(
                Q(client__name__icontains=search) |
                Q(diploma__name__icontains=search)
            )
        return queryset


class DetailedClientReportView(generics.ListAPIView):
    queryset = ClientDiploma.objects.select_related('client', 'diploma', 'added_by').all()
    serializer_class = ClientDiplomaReportSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ClientDiplomaFilter


    def get_queryset(self):
        queryset = ClientDiploma.objects.select_related('client', 'diploma', 'added_by').all()
        params = self.request.query_params

        sector = params.get("sector")
        area = params.get("area")
        search = params.get("search")
        from_date = params.get("date_from")
        to_date = params.get("date_to")
        added_by = params.get("added_by")

        # 🔹 فلترة القطاع
        if sector:
            queryset = queryset.filter(client__sector=sector)

        # 🔹 فلترة المنطقة
        if area:
            queryset = queryset.filter(client__area=area)

        # 🔹 البحث باسم العميل أو الدبلوم
        if search:
            queryset = queryset.filter(
                Q(client__name__icontains=search) |
                Q(diploma__name__icontains=search)
            )

        # 🔹 فلترة بالتاريخ (من - إلى)
        if from_date and to_date:
            try:
                start_date = datetime.strptime(from_date, "%Y-%m-%d")
                end_date = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
                queryset = queryset.filter(added_at__gte=start_date, added_at__lt=end_date)
            except ValueError:
                pass
        elif from_date:
            queryset = queryset.filter(added_at__date__gte=from_date)
        elif to_date:
            queryset = queryset.filter(added_at__date__lte=to_date)

        # 🔹 فلترة المستخدم الذي أضاف السجل
        if added_by:
            queryset = queryset.filter(
                Q(added_by__full_name__icontains=added_by)
            )

        return queryset
