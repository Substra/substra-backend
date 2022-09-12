import argparse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from api.models import ChannelOrganization
from organization.models import OutgoingOrganization


def pretty_row(row: list[str], columns_width: list[int]) -> str:
    """Returns a line formatted to display a table.

    Args:
        row: A data row to format.
        columns_width: A list containing each column width.

    Returns:
        A formatted string with the format "| data |".
    """
    for idx, column in enumerate(row):
        length = columns_width[idx]
        row[idx] = f" {column: ^{length}} "

    formatted_line = "|".join(row)
    return f"|{formatted_line}|"


def get_cell_width(table: list[list[str]]) -> list[int]:
    """Returns a list containing the max string length for each of the columns in data.

    Args:
        table: A two dimension list representing a data table.

    Returns:
        A list containing the max width for each column of the table.
    """
    columns_width = []
    for col in range(0, len(table[0])):
        items = [len(row[col]) for row in table]
        columns_width.append(max(items))
    return columns_width


class Command(BaseCommand):
    help = "Get outgoing organizations"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("organization_id", nargs="?")

    def handle(self, *args: list, **options: dict) -> None:
        organization_id = options.get("organization_id")

        outgoing_organizations = OutgoingOrganization.objects.all()
        if organization_id:
            outgoing_organizations = outgoing_organizations.filter(organization_id=organization_id)

        channel_organizations = ChannelOrganization.objects.filter(
            organization_id__in=[org.organization_id for org in outgoing_organizations]
        )

        outgoing_channel_org = {org.organization_id: org for org in channel_organizations}
        output_rows = [["org_id", "org_address", "http_status"]]
        for organization in outgoing_organizations:
            org_address = outgoing_channel_org[organization.organization_id].address
            response_code: str = ""
            try:
                res = requests.get(
                    f"{org_address}/info/",
                    timeout=settings.HTTP_CLIENT_TIMEOUT_SECONDS,
                )
                response_code = str(res.status_code)
            except requests.exceptions.RequestException as exc:
                response_code = str(exc)
            output_rows.append([organization.organization_id, org_address, response_code])

        width = get_cell_width(output_rows)
        for line in output_rows:
            self.stdout.write(self.style.SUCCESS(pretty_row(line, width)))
