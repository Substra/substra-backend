import orchestrator
import substrapp.clients.organization as organization_client


class DatastoreError(Exception):
    pass


class Datastore:
    def __init__(self, channel: str) -> None:
        self.channel = channel

    def _get_from_address(self, organization: str, address: orchestrator.Address) -> bytes:
        return organization_client.get(
            channel=self.channel, organization_id=organization, url=address.uri, checksum=address.checksum
        )

    def get_function(self, function: orchestrator.Function) -> bytes:
        return self._get_from_address(function.owner, function.functionrithm)

    def delete_model(self, model_key: str) -> None:
        from substrapp.models import Model

        try:
            Model.objects.get(key=model_key).delete()
        except Model.DoesNotExist as exc:
            raise DatastoreError() from exc


def get_datastore(channel: str) -> Datastore:
    return Datastore(channel)
