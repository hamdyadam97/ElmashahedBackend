from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date

from django.template.loader import render_to_string
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from weasyprint import HTML
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.templatetags.static import static  # <--- هذا السطر مهم
from django.conf import settings
# views.py
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

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
    # permission_classes = [IsAuthenticated]
    serializer_class = DiplomaSerializer
    pagination_class = None

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


# def client_diploma_pdf(request, client_id, diploma_id):
#     client = get_object_or_404(Client, id=client_id)
#     diploma = client.diplomas.filter(id=diploma_id).first()
#     if not diploma:
#         return HttpResponse("الدبلوم غير موجود للعميل.", status=404)
#
#
#     # bg_url = request.build_absolute_uri(static('Afaq.jpg'))
#     # bg2_url = request.build_absolute_uri(static('image2.png'))
#
#     area_templates = {
#         'riyadh': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'Afaq.jpg'},
#         'makkah': {'template': 'Al-AhliHigherInstitute–ArarSakakaAl-Qurayyat.html', 'bg': 'Ahley.jpeg'},
#         # 'madinah': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'madinah_bg.jpg'},
#         # 'qassim': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'qassim_bg.jpg'},
#         # 'eastern': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'eastern_bg.jpg'},
#         # 'asir': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'asir_bg.jpg'},
#         # 'tabuk': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'tabuk_bg.jpg'},
#         # 'hail': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'hail_bg.jpg'},
#         # 'north_border': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'north_border_bg.jpg'},
#         # 'jazan': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'jazan_bg.jpg'},
#         # 'najran': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'najran_bg.jpg'},
#         # 'baha': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'baha_bg.jpg'},
#         'jouf': {'template': 'Al-FawSpecializedHigherInstituteforTraining–Qassim.html', 'bg': 'fawo.jpeg'},
#     }
#     area_settings = area_templates.get(client.area, {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'Afaq.jpg',})
#     bg_url = request.build_absolute_uri(static(area_settings['bg']))
#
#
#     bg2_url = request.build_absolute_uri(static('image2.png'))
#
#
#     context = {
#         "client": client,
#         "diplomas": [diploma],
#         "bg_url": bg_url,
#         "bg2_url": bg2_url,
#
#     }
#
#     html_string = render_to_string(area_settings['template'], context)
#     pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
#
#     response = HttpResponse(pdf_file, content_type="application/pdf")
#     response['Content-Disposition'] = f'inline; filename="client_{client.id}_diploma_{diploma.id}.pdf"'
#     return response


def client_diploma_pdf(request, client_id, diploma_id):
    client = get_object_or_404(Client, id=client_id)
    client_diploma = client.client_diplomas.filter(diploma_id=diploma_id).first()
    if not client_diploma:
        return HttpResponse("الدبلوم غير موجود للعميل.", status=404)

    diploma = client_diploma.diploma
    institute = getattr(client_diploma, 'institute', None)


    institute_templates = {
        'Afaq Al-Tatawor Higher Institute for Training': {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.jpg'},
        'Al-Ahli Higher Institute': {'template': 'Al-AhliHigherInstitute–ArarSakakaAl-Qurayyat.html', 'bg': 'Al-AhliHigherInstitute–ArarSakakaAl-Qurayyat.jpeg'},
        'Al-Faw Advanced Higher Institute for Training': {'template': 'Al-FawAdvancedHigherInstituteforTraining.html', 'bg': 'Al-FawAdvancedHigherInstituteforTraining.png'},
        'Al-Faw Specialized Higher Institute for Training': {'template': 'Al-FawSpecializedHigherInstituteforTraining–Qassim.html', 'bg': 'Al-FawSpecializedHigherInstituteforTraining–Qassim.jpeg'},

    }


    area_settings = institute_templates.get(institute.name if institute else None,
                                            {'template': 'AfaqAl-TataworHigherInstituteforTraining–Dammam.html', 'bg': 'Afaq.jpg'})

    bg_url = request.build_absolute_uri(static(area_settings['bg']))
    context = {
        "client": client,
        "diplomas": [diploma],
        "bg_url": bg_url,
        "institute_name": institute.name if institute else "",
    }

    html_string = render_to_string(area_settings['template'], context)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response['Content-Disposition'] = f'inline; filename="client_{client.id}_diploma_{diploma.id}.pdf"'
    return response



class DetailedClientReportView(generics.ListAPIView):
    queryset = ClientDiploma.objects.select_related('client', 'diploma', 'added_by').all()
    serializer_class = ClientDiplomaReportSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ClientDiplomaFilter

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
