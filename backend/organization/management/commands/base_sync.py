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

        existing_keys = set(self.model.objects.values_list(self.field_key, flat=True))

        for line in file:
            line_trimmed = line.removesuffix("\n")
            element = self.parse_line(line_trimmed)
            self.handle_element(element)
            existing_keys.discard(element.key)

        self.delete(existing_keys)

    def parse_line(self, line: str) -> Element:
        (key, password) = line.rsplit(" ", maxsplit=1)

        return Element(key=key, password=password)

    def handle_element(self, element: Element) -> None:
        try:
            self.create(element)
        except IntegrityError:
            self.update_password(element)

    def get(self, key: str) -> models.Model:
        parameters = {self.field_key: key}
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
        model = self.get(element.key)
        model.set_password(element.password)
        model.save()
        self.stdout.write(f"{self.model_name} updated: {element.key}")
        return model

    def delete(self, discarded_keys: set[str]) -> None:
        # Using instance delete instead of queryset to activate foreign keys actions
        for key in discarded_keys:
            model = self.get(key)
            model.delete()

            self.stdout.write(f"{self.model_name} deleted: {key}")
