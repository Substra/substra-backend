import orchestrator
import substrapp.clients.organization as organization_client


class Datastore:
    def __init__(self, channel: str) -> None:
        self.channel = channel

    def _get_from_address(self, organization: str, address: orchestrator.Address) -> bytes:
        return organization_client.get(
            channel=self.channel, organization_id=organization, url=address.uri, checksum=address.checksum
        )

    def get_algo(self, algo: orchestrator.Algo) -> bytes:
        return self._get_from_address(algo.owner, algo.algorithm)


def get_datastore(channel: str) -> Datastore:
    return Datastore(channel)
