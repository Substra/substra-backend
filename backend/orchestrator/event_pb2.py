# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: event.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from . import function_pb2 as function__pb2
from . import common_pb2 as common__pb2
from . import computeplan_pb2 as computeplan__pb2
from . import computetask_pb2 as computetask__pb2
from . import datamanager_pb2 as datamanager__pb2
from . import datasample_pb2 as datasample__pb2
from . import failure_report_pb2 as failure__report__pb2
from . import model_pb2 as model__pb2
from . import organization_pb2 as organization__pb2
from . import performance_pb2 as performance__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0b\x65vent.proto\x12\x0corchestrator\x1a\x0e\x66unction.proto\x1a\x0c\x63ommon.proto\x1a\x11\x63omputeplan.proto\x1a\x11\x63omputetask.proto\x1a\x11\x64\x61tamanager.proto\x1a\x10\x64\x61tasample.proto\x1a\x14\x66\x61ilure_report.proto\x1a\x0bmodel.proto\x1a\x12organization.proto\x1a\x11performance.proto\x1a\x1fgoogle/protobuf/timestamp.proto\"\xb3\x06\n\x05\x45vent\x12\n\n\x02id\x18\x01 \x01(\t\x12\x11\n\tasset_key\x18\x02 \x01(\t\x12+\n\nasset_kind\x18\x03 \x01(\x0e\x32\x17.orchestrator.AssetKind\x12+\n\nevent_kind\x18\x04 \x01(\x0e\x32\x17.orchestrator.EventKind\x12\x0f\n\x07\x63hannel\x18\x05 \x01(\t\x12-\n\ttimestamp\x18\x06 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12*\n\x08\x66unction\x18\x07 \x01(\x0b\x32\x16.orchestrator.FunctionH\x00\x12\x31\n\x0c\x63ompute_plan\x18\x08 \x01(\x0b\x32\x19.orchestrator.ComputePlanH\x00\x12\x31\n\x0c\x63ompute_task\x18\t \x01(\x0b\x32\x19.orchestrator.ComputeTaskH\x00\x12\x31\n\x0c\x64\x61ta_manager\x18\n \x01(\x0b\x32\x19.orchestrator.DataManagerH\x00\x12/\n\x0b\x64\x61ta_sample\x18\x0b \x01(\x0b\x32\x18.orchestrator.DataSampleH\x00\x12\x35\n\x0e\x66\x61ilure_report\x18\x0c \x01(\x0b\x32\x1b.orchestrator.FailureReportH\x00\x12$\n\x05model\x18\r \x01(\x0b\x32\x13.orchestrator.ModelH\x00\x12\x32\n\x0corganization\x18\x0e \x01(\x0b\x32\x1a.orchestrator.OrganizationH\x00\x12\x30\n\x0bperformance\x18\x0f \x01(\x0b\x32\x19.orchestrator.PerformanceH\x00\x12I\n\x19\x63ompute_task_output_asset\x18\x10 \x01(\x0b\x32$.orchestrator.ComputeTaskOutputAssetH\x00\x12\x33\n\x08metadata\x18\x12 \x03(\x0b\x32!.orchestrator.Event.MetadataEntry\x1a/\n\rMetadataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x42\x07\n\x05\x61sset\"\x90\x01\n\x10QueryEventsParam\x12\x12\n\npage_token\x18\x01 \x01(\t\x12\x11\n\tpage_size\x18\x02 \x01(\r\x12.\n\x06\x66ilter\x18\x03 \x01(\x0b\x32\x1e.orchestrator.EventQueryFilter\x12%\n\x04sort\x18\x04 \x01(\x0e\x32\x17.orchestrator.SortOrder\"\xc4\x02\n\x10\x45ventQueryFilter\x12\x11\n\tasset_key\x18\x01 \x01(\t\x12+\n\nasset_kind\x18\x02 \x01(\x0e\x32\x17.orchestrator.AssetKind\x12+\n\nevent_kind\x18\x03 \x01(\x0e\x32\x17.orchestrator.EventKind\x12>\n\x08metadata\x18\x04 \x03(\x0b\x32,.orchestrator.EventQueryFilter.MetadataEntry\x12)\n\x05start\x18\x05 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\'\n\x03\x65nd\x18\x06 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x1a/\n\rMetadataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"S\n\x13QueryEventsResponse\x12#\n\x06\x65vents\x18\x01 \x03(\x0b\x32\x13.orchestrator.Event\x12\x17\n\x0fnext_page_token\x18\x02 \x01(\t\"0\n\x16SubscribeToEventsParam\x12\x16\n\x0estart_event_id\x18\x01 \x01(\t*j\n\tEventKind\x12\x11\n\rEVENT_UNKNOWN\x10\x00\x12\x17\n\x13\x45VENT_ASSET_CREATED\x10\x01\x12\x17\n\x13\x45VENT_ASSET_UPDATED\x10\x02\x12\x18\n\x14\x45VENT_ASSET_DISABLED\x10\x03\x32\xb2\x01\n\x0c\x45ventService\x12P\n\x0bQueryEvents\x12\x1e.orchestrator.QueryEventsParam\x1a!.orchestrator.QueryEventsResponse\x12P\n\x11SubscribeToEvents\x12$.orchestrator.SubscribeToEventsParam\x1a\x13.orchestrator.Event0\x01\x42+Z)github.com/substra/orchestrator/lib/assetb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'event_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'Z)github.com/substra/orchestrator/lib/asset'
  _EVENT_METADATAENTRY._options = None
  _EVENT_METADATAENTRY._serialized_options = b'8\001'
  _EVENTQUERYFILTER_METADATAENTRY._options = None
  _EVENTQUERYFILTER_METADATAENTRY._serialized_options = b'8\001'
  _EVENTKIND._serialized_start=1672
  _EVENTKIND._serialized_end=1778
  _EVENT._serialized_start=242
  _EVENT._serialized_end=1061
  _EVENT_METADATAENTRY._serialized_start=1005
  _EVENT_METADATAENTRY._serialized_end=1052
  _QUERYEVENTSPARAM._serialized_start=1064
  _QUERYEVENTSPARAM._serialized_end=1208
  _EVENTQUERYFILTER._serialized_start=1211
  _EVENTQUERYFILTER._serialized_end=1535
  _EVENTQUERYFILTER_METADATAENTRY._serialized_start=1005
  _EVENTQUERYFILTER_METADATAENTRY._serialized_end=1052
  _QUERYEVENTSRESPONSE._serialized_start=1537
  _QUERYEVENTSRESPONSE._serialized_end=1620
  _SUBSCRIBETOEVENTSPARAM._serialized_start=1622
  _SUBSCRIBETOEVENTSPARAM._serialized_end=1670
  _EVENTSERVICE._serialized_start=1781
  _EVENTSERVICE._serialized_end=1959
# @@protoc_insertion_point(module_scope)
