# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: performance.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11performance.proto\x12\x0corchestrator\x1a\x1fgoogle/protobuf/timestamp.proto\"m\n\x0eNewPerformance\x12\x18\n\x10\x63ompute_task_key\x18\x01 \x01(\t\x12&\n\x1e\x63ompute_task_output_identifier\x18\x03 \x01(\t\x12\x19\n\x11performance_value\x18\x02 \x01(\x02\"\x9d\x01\n\x0bPerformance\x12\x18\n\x10\x63ompute_task_key\x18\x01 \x01(\t\x12&\n\x1e\x63ompute_task_output_identifier\x18\x06 \x01(\t\x12\x19\n\x11performance_value\x18\x02 \x01(\x02\x12\x31\n\rcreation_date\x18\x03 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\"Z\n\x16PerformanceQueryFilter\x12\x18\n\x10\x63ompute_task_key\x18\x01 \x01(\t\x12&\n\x1e\x63ompute_task_output_identifier\x18\x03 \x01(\t\"u\n\x16QueryPerformancesParam\x12\x12\n\npage_token\x18\x01 \x01(\t\x12\x11\n\tpage_size\x18\x02 \x01(\r\x12\x34\n\x06\x66ilter\x18\x03 \x01(\x0b\x32$.orchestrator.PerformanceQueryFilter\"e\n\x19QueryPerformancesResponse\x12/\n\x0cPerformances\x18\x01 \x03(\x0b\x32\x19.orchestrator.Performance\x12\x17\n\x0fnext_page_token\x18\x02 \x01(\t2\xc8\x01\n\x12PerformanceService\x12N\n\x13RegisterPerformance\x12\x1c.orchestrator.NewPerformance\x1a\x19.orchestrator.Performance\x12\x62\n\x11QueryPerformances\x12$.orchestrator.QueryPerformancesParam\x1a\'.orchestrator.QueryPerformancesResponseB+Z)github.com/substra/orchestrator/lib/assetb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'performance_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  _globals['DESCRIPTOR']._options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z)github.com/substra/orchestrator/lib/asset'
  _globals['_NEWPERFORMANCE']._serialized_start=68
  _globals['_NEWPERFORMANCE']._serialized_end=177
  _globals['_PERFORMANCE']._serialized_start=180
  _globals['_PERFORMANCE']._serialized_end=337
  _globals['_PERFORMANCEQUERYFILTER']._serialized_start=339
  _globals['_PERFORMANCEQUERYFILTER']._serialized_end=429
  _globals['_QUERYPERFORMANCESPARAM']._serialized_start=431
  _globals['_QUERYPERFORMANCESPARAM']._serialized_end=548
  _globals['_QUERYPERFORMANCESRESPONSE']._serialized_start=550
  _globals['_QUERYPERFORMANCESRESPONSE']._serialized_end=651
  _globals['_PERFORMANCESERVICE']._serialized_start=654
  _globals['_PERFORMANCESERVICE']._serialized_end=854
# @@protoc_insertion_point(module_scope)
