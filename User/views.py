from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date

from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML

# views.py
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import User, Diploma, Client, ClientDiploma
from .serializers import UserSerializer, DiplomaSerializer, ClientSerializer, ClientDiplomaListSerializer


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

    def perform_create(self, serializer):
        diplomas_ids = serializer.validated_data.pop('diplomas_ids', [])
        if not diplomas_ids:
            raise serializers.ValidationError({"diplomas_ids": "يجب إضافة دبلوم واحد على الأقل."})

        user = self.request.user
        client, created = Client.objects.get_or_create(
            identity_number=serializer.validated_data['identity_number'],
            defaults={
                'name': serializer.validated_data.get('name'),
                'phone_number': serializer.validated_data.get('phone_number'),
                'email': serializer.validated_data.get('email'),
                'sector': serializer.validated_data.get('sector'),
                'area': serializer.validated_data.get('area'),

            }
        )

        # ربط الدبلومات بالعميل
        for diploma_id in diplomas_ids:
            diploma = Diploma.objects.get(id=diploma_id)
            ClientDiploma.objects.get_or_create(client=client, diploma=diploma, added_by=user)


        serializer.instance = client



class ClientRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Client.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ClientSerializer





def client_diploma_pdf(request, client_id, diploma_id):
    # جلب العميل والدبلوم
    client = get_object_or_404(Client, id=client_id)
    diploma = client.diplomas.filter(id=diploma_id).first()
    if not diploma:
        return HttpResponse("الدبلوم غير موجود للعميل.", status=404)

    # بيانات الـ template
    context = {
        "client": client,
        "diplomas": [diploma]  # لو عايز كل الدبلومات، خليها client.diplomas.all()
    }

    # توليد HTML
    html_string = render_to_string("print.html", context)

    # توليد PDF
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response['Content-Disposition'] = f'inline; filename="client_{client.id}_diploma_{diploma.id}.pdf"'
    return response



class DetailedClientReportView(APIView):


    def get(self, request):
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        area = request.GET.get("area")
        sector = request.GET.get("sector")
        diploma_id = request.GET.get("diploma")
        user_id = request.GET.get("user")

        clients = Client.objects.prefetch_related('diplomas').all()
        if start_date:
            clients = clients.filter(diplomas__date__gte=parse_date(start_date))
        if end_date:
            clients = clients.filter(diplomas__date__lte=parse_date(end_date))
        if area:
            clients = clients.filter(area=area)
        if sector:
            clients = clients.filter(sector=sector)
        if diploma_id:
            clients = clients.filter(diplomas__id=diploma_id)
        if user_id:
            clients = clients.filter(added_by_id=user_id)

        clients = clients.distinct()

        report = []
        for client in clients:
            diplomas = client.diplomas.all()
            report.append({
                "id": client.id,
                "name": client.name,
                "identity_number": client.identity_number,
                "phone_number": client.phone_number,
                "email": client.email,
                "sector": client.sector,
                "area": client.area,
                "added_by": client.added_by.full_name,
                "diplomas": [{"id": d.id, "name": d.name, "date": d.date} for d in diplomas]
            })

        return Response(report)

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
