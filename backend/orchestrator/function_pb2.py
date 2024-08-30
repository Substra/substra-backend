# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: function.proto
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
    'function.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from . import common_pb2 as common__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0e\x66unction.proto\x12\x0corchestrator\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x0c\x63ommon.proto\"Z\n\rFunctionInput\x12%\n\x04kind\x18\x01 \x01(\x0e\x32\x17.orchestrator.AssetKind\x12\x10\n\x08multiple\x18\x02 \x01(\x08\x12\x10\n\x08optional\x18\x03 \x01(\x08\"I\n\x0e\x46unctionOutput\x12%\n\x04kind\x18\x01 \x01(\x0e\x32\x17.orchestrator.AssetKind\x12\x10\n\x08multiple\x18\x02 \x01(\x08\"\xc8\x05\n\x08\x46unction\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12.\n\x0b\x64\x65scription\x18\x04 \x01(\x0b\x32\x19.orchestrator.Addressable\x12*\n\x07\x61rchive\x18\x05 \x01(\x0b\x32\x19.orchestrator.Addressable\x12.\n\x0bpermissions\x18\x06 \x01(\x0b\x32\x19.orchestrator.Permissions\x12\r\n\x05owner\x18\x07 \x01(\t\x12\x31\n\rcreation_date\x18\x08 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x36\n\x08metadata\x18\x10 \x03(\x0b\x32$.orchestrator.Function.MetadataEntry\x12\x32\n\x06inputs\x18\x11 \x03(\x0b\x32\".orchestrator.Function.InputsEntry\x12\x34\n\x07outputs\x18\x12 \x03(\x0b\x32#.orchestrator.Function.OutputsEntry\x12,\n\x06status\x18\x13 \x01(\x0e\x32\x1c.orchestrator.FunctionStatus\x12(\n\x05image\x18\x14 \x01(\x0b\x32\x19.orchestrator.Addressable\x1a/\n\rMetadataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x1aJ\n\x0bInputsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12*\n\x05value\x18\x02 \x01(\x0b\x32\x1b.orchestrator.FunctionInput:\x02\x38\x01\x1aL\n\x0cOutputsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12+\n\x05value\x18\x02 \x01(\x0b\x32\x1c.orchestrator.FunctionOutput:\x02\x38\x01J\x04\x08\x03\x10\x04R\x08\x63\x61tegory\"\xc1\x04\n\x0bNewFunction\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12.\n\x0b\x64\x65scription\x18\x04 \x01(\x0b\x32\x19.orchestrator.Addressable\x12*\n\x07\x61rchive\x18\x05 \x01(\x0b\x32\x19.orchestrator.Addressable\x12\x35\n\x0fnew_permissions\x18\x06 \x01(\x0b\x32\x1c.orchestrator.NewPermissions\x12\x39\n\x08metadata\x18\x11 \x03(\x0b\x32\'.orchestrator.NewFunction.MetadataEntry\x12\x35\n\x06inputs\x18\x12 \x03(\x0b\x32%.orchestrator.NewFunction.InputsEntry\x12\x37\n\x07outputs\x18\x13 \x03(\x0b\x32&.orchestrator.NewFunction.OutputsEntry\x1a/\n\rMetadataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x1aJ\n\x0bInputsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12*\n\x05value\x18\x02 \x01(\x0b\x32\x1b.orchestrator.FunctionInput:\x02\x38\x01\x1aL\n\x0cOutputsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12+\n\x05value\x18\x02 \x01(\x0b\x32\x1c.orchestrator.FunctionOutput:\x02\x38\x01J\x04\x08\x03\x10\x04R\x08\x63\x61tegory\"\x1f\n\x10GetFunctionParam\x12\x0b\n\x03key\x18\x01 \x01(\t\"\\\n\x16QueryFunctionsResponse\x12)\n\tFunctions\x18\x01 \x03(\x0b\x32\x16.orchestrator.Function\x12\x17\n\x0fnext_page_token\x18\x02 \x01(\t\"/\n\x13\x46unctionQueryFilter\x12\x18\n\x10\x63ompute_plan_key\x18\x02 \x01(\t\"o\n\x13QueryFunctionsParam\x12\x12\n\npage_token\x18\x01 \x01(\t\x12\x11\n\tpage_size\x18\x02 \x01(\r\x12\x31\n\x06\x66ilter\x18\x03 \x01(\x0b\x32!.orchestrator.FunctionQueryFilter\"Z\n\x13UpdateFunctionParam\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12(\n\x05image\x18\x03 \x01(\x0b\x32\x19.orchestrator.Addressable\"\x18\n\x16UpdateFunctionResponse\"^\n\x18\x41pplyFunctionActionParam\x12\x14\n\x0c\x66unction_key\x18\x01 \x01(\t\x12,\n\x06\x61\x63tion\x18\x02 \x01(\x0e\x32\x1c.orchestrator.FunctionAction\"\x1d\n\x1b\x41pplyFunctionActionResponse*\xa0\x01\n\x0e\x46unctionAction\x12\x1b\n\x17\x46UNCTION_ACTION_UNKNOWN\x10\x00\x12\x1c\n\x18\x46UNCTION_ACTION_BUILDING\x10\x01\x12\x1c\n\x18\x46UNCTION_ACTION_CANCELED\x10\x02\x12\x1a\n\x16\x46UNCTION_ACTION_FAILED\x10\x03\x12\x19\n\x15\x46UNCTION_ACTION_READY\x10\x04*\xbd\x01\n\x0e\x46unctionStatus\x12\x1b\n\x17\x46UNCTION_STATUS_UNKNOWN\x10\x00\x12\x1b\n\x17\x46UNCTION_STATUS_WAITING\x10\x01\x12\x1c\n\x18\x46UNCTION_STATUS_BUILDING\x10\x02\x12\x19\n\x15\x46UNCTION_STATUS_READY\x10\x03\x12\x1c\n\x18\x46UNCTION_STATUS_CANCELED\x10\x04\x12\x1a\n\x16\x46UNCTION_STATUS_FAILED\x10\x05\x32\xbf\x03\n\x0f\x46unctionService\x12\x45\n\x10RegisterFunction\x12\x19.orchestrator.NewFunction\x1a\x16.orchestrator.Function\x12\x45\n\x0bGetFunction\x12\x1e.orchestrator.GetFunctionParam\x1a\x16.orchestrator.Function\x12Y\n\x0eQueryFunctions\x12!.orchestrator.QueryFunctionsParam\x1a$.orchestrator.QueryFunctionsResponse\x12Y\n\x0eUpdateFunction\x12!.orchestrator.UpdateFunctionParam\x1a$.orchestrator.UpdateFunctionResponse\x12h\n\x13\x41pplyFunctionAction\x12&.orchestrator.ApplyFunctionActionParam\x1a).orchestrator.ApplyFunctionActionResponseB+Z)github.com/substra/orchestrator/lib/assetb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'function_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z)github.com/substra/orchestrator/lib/asset'
  _globals['_FUNCTION_METADATAENTRY']._loaded_options = None
  _globals['_FUNCTION_METADATAENTRY']._serialized_options = b'8\001'
  _globals['_FUNCTION_INPUTSENTRY']._loaded_options = None
  _globals['_FUNCTION_INPUTSENTRY']._serialized_options = b'8\001'
  _globals['_FUNCTION_OUTPUTSENTRY']._loaded_options = None
  _globals['_FUNCTION_OUTPUTSENTRY']._serialized_options = b'8\001'
  _globals['_NEWFUNCTION_METADATAENTRY']._loaded_options = None
  _globals['_NEWFUNCTION_METADATAENTRY']._serialized_options = b'8\001'
  _globals['_NEWFUNCTION_INPUTSENTRY']._loaded_options = None
  _globals['_NEWFUNCTION_INPUTSENTRY']._serialized_options = b'8\001'
  _globals['_NEWFUNCTION_OUTPUTSENTRY']._loaded_options = None
  _globals['_NEWFUNCTION_OUTPUTSENTRY']._serialized_options = b'8\001'
  _globals['_FUNCTIONACTION']._serialized_start=2076
  _globals['_FUNCTIONACTION']._serialized_end=2236
  _globals['_FUNCTIONSTATUS']._serialized_start=2239
  _globals['_FUNCTIONSTATUS']._serialized_end=2428
  _globals['_FUNCTIONINPUT']._serialized_start=79
  _globals['_FUNCTIONINPUT']._serialized_end=169
  _globals['_FUNCTIONOUTPUT']._serialized_start=171
  _globals['_FUNCTIONOUTPUT']._serialized_end=244
  _globals['_FUNCTION']._serialized_start=247
  _globals['_FUNCTION']._serialized_end=959
  _globals['_FUNCTION_METADATAENTRY']._serialized_start=742
  _globals['_FUNCTION_METADATAENTRY']._serialized_end=789
  _globals['_FUNCTION_INPUTSENTRY']._serialized_start=791
  _globals['_FUNCTION_INPUTSENTRY']._serialized_end=865
  _globals['_FUNCTION_OUTPUTSENTRY']._serialized_start=867
  _globals['_FUNCTION_OUTPUTSENTRY']._serialized_end=943
  _globals['_NEWFUNCTION']._serialized_start=962
  _globals['_NEWFUNCTION']._serialized_end=1539
  _globals['_NEWFUNCTION_METADATAENTRY']._serialized_start=742
  _globals['_NEWFUNCTION_METADATAENTRY']._serialized_end=789
  _globals['_NEWFUNCTION_INPUTSENTRY']._serialized_start=791
  _globals['_NEWFUNCTION_INPUTSENTRY']._serialized_end=865
  _globals['_NEWFUNCTION_OUTPUTSENTRY']._serialized_start=867
  _globals['_NEWFUNCTION_OUTPUTSENTRY']._serialized_end=943
  _globals['_GETFUNCTIONPARAM']._serialized_start=1541
  _globals['_GETFUNCTIONPARAM']._serialized_end=1572
  _globals['_QUERYFUNCTIONSRESPONSE']._serialized_start=1574
  _globals['_QUERYFUNCTIONSRESPONSE']._serialized_end=1666
  _globals['_FUNCTIONQUERYFILTER']._serialized_start=1668
  _globals['_FUNCTIONQUERYFILTER']._serialized_end=1715
  _globals['_QUERYFUNCTIONSPARAM']._serialized_start=1717
  _globals['_QUERYFUNCTIONSPARAM']._serialized_end=1828
  _globals['_UPDATEFUNCTIONPARAM']._serialized_start=1830
  _globals['_UPDATEFUNCTIONPARAM']._serialized_end=1920
  _globals['_UPDATEFUNCTIONRESPONSE']._serialized_start=1922
  _globals['_UPDATEFUNCTIONRESPONSE']._serialized_end=1946
  _globals['_APPLYFUNCTIONACTIONPARAM']._serialized_start=1948
  _globals['_APPLYFUNCTIONACTIONPARAM']._serialized_end=2042
  _globals['_APPLYFUNCTIONACTIONRESPONSE']._serialized_start=2044
  _globals['_APPLYFUNCTIONACTIONRESPONSE']._serialized_end=2073
  _globals['_FUNCTIONSERVICE']._serialized_start=2431
  _globals['_FUNCTIONSERVICE']._serialized_end=2878
# @@protoc_insertion_point(module_scope)
