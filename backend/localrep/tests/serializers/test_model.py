from hashlib import sha256
from uuid import uuid4

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from events.localsync import _create_model
from localrep.models import Model
from localrep.serializers import ModelSerializer
from substrapp.tests import factory


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

    def test_sync_disabled_model(self):
        """Disabled models should be syncable without address"""

        algo = factory.create_algo()
        compute_plan = factory.create_computeplan()
        compute_task = factory.create_computetask(compute_plan, algo)

        orc_output_model = {
            "key": str(uuid4()),
            "category": "MODEL_SIMPLE",
            "compute_task_key": str(compute_task.key),
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
                "download": {
                    "public": False,
                    "authorized_ids": ["MyOrg1MSP"],
                },
            },
            "owner": "MyOrg1MSP",
            "creation_date": "2022-01-20T14:18:55.354089+00:00",
        }

        try:
            self.assertTrue(_create_model("mychannel", orc_output_model))
        except Exception as e:
            self.fail(f"_create_model raised {e} unexpectedly")
