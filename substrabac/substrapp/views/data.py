from rest_framework.viewsets import ModelViewSet

from substrapp.models import Data
from substrapp.serializers import DataSerializer


class DataViewSet(ModelViewSet):
    queryset = Data.objects.all()
    serializer_class = DataSerializer
