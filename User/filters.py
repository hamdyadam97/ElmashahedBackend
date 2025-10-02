# filters.py
import django_filters
from .models import ClientDiploma

class ClientDiplomaFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="diploma__date", lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name="diploma__date", lookup_expr='lte')
    area = django_filters.CharFilter(field_name="client__area")
    sector = django_filters.CharFilter(field_name="client__sector")
    diploma = django_filters.NumberFilter(field_name="diploma__id")
    user = django_filters.NumberFilter(field_name="added_by_id")

    class Meta:
        model = ClientDiploma
        fields = ['start_date', 'end_date', 'area', 'sector', 'diploma', 'user']
