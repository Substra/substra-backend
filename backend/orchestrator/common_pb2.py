# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: common.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0c\x63ommon.proto\x12\x0corchestrator\"8\n\x0b\x41\x64\x64ressable\x12\x10\n\x08\x63hecksum\x18\x01 \x01(\t\x12\x17\n\x0fstorage_address\x18\x02 \x01(\t\"d\n\x0bPermissions\x12)\n\x07process\x18\x01 \x01(\x0b\x32\x18.orchestrator.Permission\x12*\n\x08\x64ownload\x18\x02 \x01(\x0b\x32\x18.orchestrator.Permission\"4\n\nPermission\x12\x0e\n\x06public\x18\x01 \x01(\x08\x12\x16\n\x0e\x61uthorized_ids\x18\x02 \x03(\t\"8\n\x0eNewPermissions\x12\x0e\n\x06public\x18\x01 \x01(\x08\x12\x16\n\x0e\x61uthorized_ids\x18\x02 \x03(\t*\xbe\x02\n\tAssetKind\x12\x11\n\rASSET_UNKNOWN\x10\x00\x12\x16\n\x12\x41SSET_ORGANIZATION\x10\x01\x12\x15\n\x11\x41SSET_DATA_SAMPLE\x10\x03\x12\x16\n\x12\x41SSET_DATA_MANAGER\x10\x04\x12\x12\n\x0e\x41SSET_FUNCTION\x10\x05\x12\x16\n\x12\x41SSET_COMPUTE_TASK\x10\x06\x12\x16\n\x12\x41SSET_COMPUTE_PLAN\x10\x07\x12\x0f\n\x0b\x41SSET_MODEL\x10\x08\x12\x15\n\x11\x41SSET_PERFORMANCE\x10\t\x12\x18\n\x14\x41SSET_FAILURE_REPORT\x10\n\x12#\n\x1f\x41SSET_COMPUTE_TASK_OUTPUT_ASSET\x10\x0b\x12\x18\n\x14\x41SSET_PROFILING_STEP\x10\x0c\"\x04\x08\x02\x10\x02*\x0c\x41SSET_METRIC*;\n\tSortOrder\x12\x0f\n\x0bUNSPECIFIED\x10\x00\x12\r\n\tASCENDING\x10\x01\x12\x0e\n\nDESCENDING\x10\x02\x42+Z)github.com/substra/orchestrator/lib/assetb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'common_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'Z)github.com/substra/orchestrator/lib/asset'
  _globals['_ASSETKIND']._serialized_start=303
  _globals['_ASSETKIND']._serialized_end=621
  _globals['_SORTORDER']._serialized_start=623
  _globals['_SORTORDER']._serialized_end=682
  _globals['_ADDRESSABLE']._serialized_start=30
  _globals['_ADDRESSABLE']._serialized_end=86
  _globals['_PERMISSIONS']._serialized_start=88
  _globals['_PERMISSIONS']._serialized_end=188
  _globals['_PERMISSION']._serialized_start=190
  _globals['_PERMISSION']._serialized_end=242
  _globals['_NEWPERMISSIONS']._serialized_start=244
  _globals['_NEWPERMISSIONS']._serialized_end=300
# @@protoc_insertion_point(module_scope)
