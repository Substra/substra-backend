# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: info.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ninfo.proto\x12\x0corchestrator\"\x13\n\x11QueryVersionParam\"?\n\x14QueryVersionResponse\x12\x14\n\x0corchestrator\x18\x01 \x01(\t\x12\x11\n\tchaincode\x18\x02 \x01(\t2b\n\x0bInfoService\x12S\n\x0cQueryVersion\x12\x1f.orchestrator.QueryVersionParam\x1a\".orchestrator.QueryVersionResponseB+Z)github.com/substra/orchestrator/lib/assetb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'info_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'Z)github.com/substra/orchestrator/lib/asset'
  _QUERYVERSIONPARAM._serialized_start=28
  _QUERYVERSIONPARAM._serialized_end=47
  _QUERYVERSIONRESPONSE._serialized_start=49
  _QUERYVERSIONRESPONSE._serialized_end=112
  _INFOSERVICE._serialized_start=114
  _INFOSERVICE._serialized_end=212
# @@protoc_insertion_point(module_scope)
