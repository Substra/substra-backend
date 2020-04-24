from rest_framework.parsers import MultiPartParser, DataAndFiles
from rest_framework.settings import api_settings
from rest_framework.utils import json


class JsonMultiPartParser(MultiPartParser):
    media_type = 'multipart/form-data'
    strict = api_settings.STRICT_JSON

    def _load_json(self, data):
        if 'json' not in data:
            return {}

        parse_constant = json.strict_constant if self.strict else None
        return json.loads(data['json'], parse_constant=parse_constant)

    def parse(self, stream, media_type, parser_context):
        data_and_files = super().parse(stream, media_type, parser_context)
        files = data_and_files.files.dict()
        data = self._load_json(data_and_files.data)
        return DataAndFiles(data, files)
