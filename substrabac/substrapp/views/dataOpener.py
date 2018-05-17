from rest_framework.viewsets import ModelViewSet

from substrapp.models import DataOpener
from substrapp.serializers import DataOpenerSerializer


class DataOpenerViewSet(ModelViewSet):
    queryset = DataOpener.objects.all()
    serializer_class = DataOpenerSerializer
