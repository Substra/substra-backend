# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: organization.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'organization.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x12organization.proto\x12\x0corchestrator\x1a\x1fgoogle/protobuf/timestamp.proto\"^\n\x0cOrganization\x12\n\n\x02id\x18\x01 \x01(\t\x12\x31\n\rcreation_date\x18\x02 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x0f\n\x07\x61\x64\x64ress\x18\x03 \x01(\t\"P\n\x1bGetAllOrganizationsResponse\x12\x31\n\rorganizations\x18\x01 \x03(\x0b\x32\x1a.orchestrator.Organization\",\n\x19RegisterOrganizationParam\x12\x0f\n\x07\x61\x64\x64ress\x18\x01 \x01(\t\"\x1a\n\x18GetAllOrganizationsParam2\xdc\x01\n\x13OrganizationService\x12[\n\x14RegisterOrganization\x12\'.orchestrator.RegisterOrganizationParam\x1a\x1a.orchestrator.Organization\x12h\n\x13GetAllOrganizations\x12&.orchestrator.GetAllOrganizationsParam\x1a).orchestrator.GetAllOrganizationsResponseB+Z)github.com/substra/orchestrator/lib/assetb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'organization_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z)github.com/substra/orchestrator/lib/asset'
  _globals['_ORGANIZATION']._serialized_start=69
  _globals['_ORGANIZATION']._serialized_end=163
  _globals['_GETALLORGANIZATIONSRESPONSE']._serialized_start=165
  _globals['_GETALLORGANIZATIONSRESPONSE']._serialized_end=245
  _globals['_REGISTERORGANIZATIONPARAM']._serialized_start=247
  _globals['_REGISTERORGANIZATIONPARAM']._serialized_end=291
  _globals['_GETALLORGANIZATIONSPARAM']._serialized_start=293
  _globals['_GETALLORGANIZATIONSPARAM']._serialized_end=319
  _globals['_ORGANIZATIONSERVICE']._serialized_start=322
  _globals['_ORGANIZATIONSERVICE']._serialized_end=542
# @@protoc_insertion_point(module_scope)
