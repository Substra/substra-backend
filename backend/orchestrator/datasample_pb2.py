# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: datasample.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10\x64\x61tasample.proto\x12\x0corchestrator\x1a\x1fgoogle/protobuf/timestamp.proto\"\x9b\x01\n\nDataSample\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x19\n\x11\x64\x61ta_manager_keys\x18\x02 \x03(\t\x12\r\n\x05owner\x18\x03 \x01(\t\x12\x11\n\ttest_only\x18\x04 \x01(\x08\x12\x10\n\x08\x63hecksum\x18\x05 \x01(\t\x12\x31\n\rcreation_date\x18\x06 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\"\\\n\rNewDataSample\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x19\n\x11\x64\x61ta_manager_keys\x18\x02 \x03(\t\x12\x11\n\ttest_only\x18\x03 \x01(\x08\x12\x10\n\x08\x63hecksum\x18\x04 \x01(\t\"H\n\x18RegisterDataSamplesParam\x12,\n\x07samples\x18\x01 \x03(\x0b\x32\x1b.orchestrator.NewDataSample\"M\n\x1bRegisterDataSamplesResponse\x12.\n\x0c\x64\x61ta_samples\x18\x01 \x03(\x0b\x32\x18.orchestrator.DataSample\"A\n\x16UpdateDataSamplesParam\x12\x0c\n\x04keys\x18\x01 \x03(\t\x12\x19\n\x11\x64\x61ta_manager_keys\x18\x02 \x03(\t\"\x1b\n\x19UpdateDataSamplesResponse\"%\n\x15\x44\x61taSampleQueryFilter\x12\x0c\n\x04keys\x18\x01 \x03(\t\"s\n\x15QueryDataSamplesParam\x12\x12\n\npage_token\x18\x01 \x01(\t\x12\x11\n\tpage_size\x18\x02 \x01(\r\x12\x33\n\x06\x66ilter\x18\x03 \x01(\x0b\x32#.orchestrator.DataSampleQueryFilter\"c\n\x18QueryDataSamplesResponse\x12.\n\x0c\x64\x61ta_samples\x18\x01 \x03(\x0b\x32\x18.orchestrator.DataSample\x12\x17\n\x0fnext_page_token\x18\x02 \x01(\t\"!\n\x12GetDataSampleParam\x12\x0b\n\x03key\x18\x01 \x01(\t2\x8f\x03\n\x11\x44\x61taSampleService\x12h\n\x13RegisterDataSamples\x12&.orchestrator.RegisterDataSamplesParam\x1a).orchestrator.RegisterDataSamplesResponse\x12\x62\n\x11UpdateDataSamples\x12$.orchestrator.UpdateDataSamplesParam\x1a\'.orchestrator.UpdateDataSamplesResponse\x12_\n\x10QueryDataSamples\x12#.orchestrator.QueryDataSamplesParam\x1a&.orchestrator.QueryDataSamplesResponse\x12K\n\rGetDataSample\x12 .orchestrator.GetDataSampleParam\x1a\x18.orchestrator.DataSampleB+Z)github.com/substra/orchestrator/lib/assetb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'datasample_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'Z)github.com/substra/orchestrator/lib/asset'
  _globals['_DATASAMPLE']._serialized_start=68
  _globals['_DATASAMPLE']._serialized_end=223
  _globals['_NEWDATASAMPLE']._serialized_start=225
  _globals['_NEWDATASAMPLE']._serialized_end=317
  _globals['_REGISTERDATASAMPLESPARAM']._serialized_start=319
  _globals['_REGISTERDATASAMPLESPARAM']._serialized_end=391
  _globals['_REGISTERDATASAMPLESRESPONSE']._serialized_start=393
  _globals['_REGISTERDATASAMPLESRESPONSE']._serialized_end=470
  _globals['_UPDATEDATASAMPLESPARAM']._serialized_start=472
  _globals['_UPDATEDATASAMPLESPARAM']._serialized_end=537
  _globals['_UPDATEDATASAMPLESRESPONSE']._serialized_start=539
  _globals['_UPDATEDATASAMPLESRESPONSE']._serialized_end=566
  _globals['_DATASAMPLEQUERYFILTER']._serialized_start=568
  _globals['_DATASAMPLEQUERYFILTER']._serialized_end=605
  _globals['_QUERYDATASAMPLESPARAM']._serialized_start=607
  _globals['_QUERYDATASAMPLESPARAM']._serialized_end=722
  _globals['_QUERYDATASAMPLESRESPONSE']._serialized_start=724
  _globals['_QUERYDATASAMPLESRESPONSE']._serialized_end=823
  _globals['_GETDATASAMPLEPARAM']._serialized_start=825
  _globals['_GETDATASAMPLEPARAM']._serialized_end=858
  _globals['_DATASAMPLESERVICE']._serialized_start=861
  _globals['_DATASAMPLESERVICE']._serialized_end=1260
# @@protoc_insertion_point(module_scope)
