# accounts/urls.py
from django.urls import path
from .views import UserListCreateAPIView, UserRetrieveUpdateAPIView, UserDeleteAPIView, LoginAPIView, \
     ClientRetrieveUpdateDestroyView, DiplomaListCreateView, DiplomaRetrieveUpdateDestroyView, \
    client_diploma_pdf, DetailedClientReportView, ClientCreateView,ClientDiplomaListView

app_name = 'User'

urlpatterns = [
    path('', UserListCreateAPIView.as_view(), name='user-list-create'),
    path('<int:pk>/', UserRetrieveUpdateAPIView.as_view(), name='user-retrieve-update'),
    path("clients/", ClientDiplomaListView.as_view(), name="client-list-create"),
    path('clients/create/', ClientCreateView.as_view(), name='client-create'),  # POST لإضافة عميل
    path("clients/<int:pk>/", ClientRetrieveUpdateDestroyView.as_view(), name="client-detail"),
    # Diplomas
    path("diplomas/", DiplomaListCreateView.as_view(), name="diploma-list-create"),
    path("diplomas/<int:pk>/", DiplomaRetrieveUpdateDestroyView.as_view(), name="diploma-detail"),
    path('<int:pk>/delete/', UserDeleteAPIView.as_view(), name='user-delete'),
    path('login/', LoginAPIView.as_view(), name='user-login'),

    path('client/<int:client_id>/diploma/<int:diploma_id>/pdf/', client_diploma_pdf,
         name='client-diploma-pdf'),
    path('report/',DetailedClientReportView.as_view(), name='client-report'),

]
