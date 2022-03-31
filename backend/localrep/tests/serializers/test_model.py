from hashlib import sha256
from uuid import uuid4

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from localrep.models import Model
from localrep.serializers import ModelSerializer


class ModelSerializerTests(TestCase):
    def test_disabled_model_address(self):
        """Disabled models should not have an address"""

        model = Model(
            key=uuid4(),
            model_checksum=sha256("checksum1".encode()).hexdigest(),
        )
        serializer = ModelSerializer(instance=model)
        assert serializer.data["address"] is None

        request = APIRequestFactory().get("/model")
        model = Model(
            key=uuid4(),
            model_address="http://somewhere",
            model_checksum=sha256("checksum2".encode()).hexdigest(),
        )
        serializer = ModelSerializer(instance=model, context={"request": request})
        # serialized address value is recomputed from the key and differ from the instance value
        assert serializer.data["address"]["storage_address"] == f"http://testserver/model/{model.key}/file/"

        # unless there is no associated request, then instance value is used
        serializer = ModelSerializer(instance=model)
        assert serializer.data["address"]["storage_address"] == model.model_address
