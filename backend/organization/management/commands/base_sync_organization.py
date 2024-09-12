import abc
import argparse

import pydantic
import structlog
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db import models

# Get an instance of a logger
logger = structlog.getLogger(__name__)


class Element(pydantic.BaseModel):
    key: str
    password: str


class BaseSyncOrganizationCommand(BaseCommand, abc.ABC):
    help = "Sync organization"
    model: models.Model
    model_name: str
    field_password: str

    def add_arguments(self, parser):
        parser.add_argument("path", type=argparse.FileType())

    def handle(self, *args, **options):
        file = options["path"]

        existing_elements = set(self.model.objects.values_list("organization_id", flat=True))

        for line in file:
            line_trimmed = line.removesuffix("\n")
            element = self.parse_line(line_trimmed)
            self.handle_element(element, existing_elements=existing_elements)

        self.delete_elements(existing_elements)

    def parse_line(self, line: str) -> Element:
        (key, password) = line.rsplit(" ", maxsplit=1)

        return Element(key=key, password=password)

    def handle_element(self, element: Element, existing_elements: set[str]) -> None:
        try:
            self.model.objects.create(
                organization_id=element.key,
                password=element.password,
            )
            self.stdout.write(f"{self.model_name} created: {element.key}")
        except IntegrityError:
            self.update_password(element.key, element.password)
        existing_elements.discard(element.key)

    def update_password(self, key: str, password: str) -> None:
        element = self.model.objects.get(organization_id=key)
        element.set_password(password)
        element.save()
        self.stdout.write(f"{self.model_name} updated: {key}")

    def delete_elements(self, discarded_elements: set[models.Model]) -> None:
        if len(discarded_elements) > 0:
            self.model.objects.filter(organization_id__in=discarded_elements).delete()
            self.stdout.write(f"{self.model_name} deleted: {', '.join(discarded_elements)}")
