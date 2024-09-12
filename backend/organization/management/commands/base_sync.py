import abc
import argparse

import pydantic
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db import models


class Element(pydantic.BaseModel):
    key: str
    password: str


class BaseSyncCommand(BaseCommand, abc.ABC):
    help = "Sync base"
    model: models.Model
    model_name: str
    field_key: str

    def add_arguments(self, parser):
        parser.add_argument("path", type=argparse.FileType())

    def handle(self, *args, **options):
        file = options["path"]

        existing_elements = set(self.model.objects.values_list(self.field_key, flat=True))

        for line in file:
            line_trimmed = line.removesuffix("\n")
            element = self.parse_line(line_trimmed)
            self.handle_element(element)
            existing_elements.discard(element.key)

        self.delete_elements(existing_elements)

    def parse_line(self, line: str) -> Element:
        (key, password) = line.rsplit(" ", maxsplit=1)

        return Element(key=key, password=password)

    def handle_element(self, element: Element) -> None:
        try:
            self.create(element)
        except IntegrityError:
            self.update_password(element)

    def get(self, element: Element) -> models.Model:
        parameters = {self.field_key: element.key}
        return self.model.objects.get(**parameters)

    def create(self, element: Element) -> models.Model:
        parameters = {
            self.field_key: element.key,
            "password": element.password,
        }
        model = self.model.objects.create(**parameters)
        self.stdout.write(f"{self.model_name} created: {element.key}")
        return model

    def update_password(self, element: Element) -> models.Model:
        model = self.get(element)
        model.set_password(element.password)
        model.save()
        self.stdout.write(f"{self.model_name} updated: {element.key}")
        return model

    def delete_elements(self, discarded_elements: set[models.Model]) -> None:
        if len(discarded_elements) > 0:
            parameters = {f"{self.field_key}__in": discarded_elements}
            self.model.objects.filter(**parameters).delete()
            self.stdout.write(f"{self.model_name} deleted: {', '.join(discarded_elements)}")
