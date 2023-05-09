# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: computeplan.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11\x63omputeplan.proto\x12\x0corchestrator\x1a\x1fgoogle/protobuf/timestamp.proto\"\x83\x04\n\x0b\x43omputePlan\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05owner\x18\x02 \x01(\t\x12\x31\n\rcreation_date\x18\x07 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x0b\n\x03tag\x18\x10 \x01(\t\x12\x0c\n\x04name\x18\x13 \x01(\t\x12\x39\n\x08metadata\x18\x11 \x03(\x0b\x32\'.orchestrator.ComputePlan.MetadataEntry\x12\x34\n\x10\x63\x61ncelation_date\x18\x12 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x30\n\x0c\x66\x61ilure_date\x18\x14 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x1a/\n\rMetadataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01J\x04\x08\x08\x10\tJ\x04\x08\t\x10\nJ\x04\x08\n\x10\x0bJ\x04\x08\x0b\x10\x0cJ\x04\x08\x0c\x10\rJ\x04\x08\x03\x10\x04J\x04\x08\x04\x10\x05J\x04\x08\x05\x10\x06J\x04\x08\x06\x10\x07R\rwaiting_countR\ntodo_countR\x0b\x64oing_countR\x0e\x63\x61nceled_countR\x0c\x66\x61iled_countR\ndone_countR\ntask_countR\x06statusR\x1a\x64\x65lete_intermediary_models\"\xc9\x01\n\x0eNewComputePlan\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x0b\n\x03tag\x18\x10 \x01(\t\x12\x0c\n\x04name\x18\x13 \x01(\t\x12<\n\x08metadata\x18\x11 \x03(\x0b\x32*.orchestrator.NewComputePlan.MetadataEntry\x1a/\n\rMetadataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01J\x04\x08\x12\x10\x13R\x1a\x64\x65lete_intermediary_models\"\"\n\x13GetComputePlanParam\x12\x0b\n\x03key\x18\x01 \x01(\t\"T\n\x14\x41pplyPlanActionParam\x12\x0b\n\x03key\x18\x01 \x01(\t\x12/\n\x06\x61\x63tion\x18\x02 \x01(\x0e\x32\x1f.orchestrator.ComputePlanAction\"\x19\n\x17\x41pplyPlanActionResponse\" \n\x0fPlanQueryFilter\x12\r\n\x05owner\x18\x01 \x01(\t\"g\n\x0fQueryPlansParam\x12\x12\n\npage_token\x18\x01 \x01(\t\x12\x11\n\tpage_size\x18\x02 \x01(\r\x12-\n\x06\x66ilter\x18\x03 \x01(\x0b\x32\x1d.orchestrator.PlanQueryFilter\"W\n\x12QueryPlansResponse\x12(\n\x05plans\x18\x01 \x03(\x0b\x32\x19.orchestrator.ComputePlan\x12\x17\n\x0fnext_page_token\x18\x02 \x01(\t\"3\n\x16UpdateComputePlanParam\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\"\x1b\n\x19UpdateComputePlanResponse\"!\n\x12IsPlanRunningParam\x12\x0b\n\x03key\x18\x01 \x01(\t\"+\n\x15IsPlanRunningResponse\x12\x12\n\nis_running\x18\x01 \x01(\x08*F\n\x11\x43omputePlanAction\x12\x17\n\x13PLAN_ACTION_UNKNOWN\x10\x00\x12\x18\n\x14PLAN_ACTION_CANCELED\x10\x01\x32\x88\x04\n\x12\x43omputePlanService\x12G\n\x0cRegisterPlan\x12\x1c.orchestrator.NewComputePlan\x1a\x19.orchestrator.ComputePlan\x12G\n\x07GetPlan\x12!.orchestrator.GetComputePlanParam\x1a\x19.orchestrator.ComputePlan\x12\\\n\x0f\x41pplyPlanAction\x12\".orchestrator.ApplyPlanActionParam\x1a%.orchestrator.ApplyPlanActionResponse\x12M\n\nQueryPlans\x12\x1d.orchestrator.QueryPlansParam\x1a .orchestrator.QueryPlansResponse\x12[\n\nUpdatePlan\x12$.orchestrator.UpdateComputePlanParam\x1a\'.orchestrator.UpdateComputePlanResponse\x12V\n\rIsPlanRunning\x12 .orchestrator.IsPlanRunningParam\x1a#.orchestrator.IsPlanRunningResponseB+Z)github.com/substra/orchestrator/lib/assetb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'computeplan_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'Z)github.com/substra/orchestrator/lib/asset'
  _COMPUTEPLAN_METADATAENTRY._options = None
  _COMPUTEPLAN_METADATAENTRY._serialized_options = b'8\001'
  _NEWCOMPUTEPLAN_METADATAENTRY._options = None
  _NEWCOMPUTEPLAN_METADATAENTRY._serialized_options = b'8\001'
  _COMPUTEPLANACTION._serialized_start=1329
  _COMPUTEPLANACTION._serialized_end=1399
  _COMPUTEPLAN._serialized_start=69
  _COMPUTEPLAN._serialized_end=584
  _COMPUTEPLAN_METADATAENTRY._serialized_start=353
  _COMPUTEPLAN_METADATAENTRY._serialized_end=400
  _NEWCOMPUTEPLAN._serialized_start=587
  _NEWCOMPUTEPLAN._serialized_end=788
  _NEWCOMPUTEPLAN_METADATAENTRY._serialized_start=353
  _NEWCOMPUTEPLAN_METADATAENTRY._serialized_end=400
  _GETCOMPUTEPLANPARAM._serialized_start=790
  _GETCOMPUTEPLANPARAM._serialized_end=824
  _APPLYPLANACTIONPARAM._serialized_start=826
  _APPLYPLANACTIONPARAM._serialized_end=910
  _APPLYPLANACTIONRESPONSE._serialized_start=912
  _APPLYPLANACTIONRESPONSE._serialized_end=937
  _PLANQUERYFILTER._serialized_start=939
  _PLANQUERYFILTER._serialized_end=971
  _QUERYPLANSPARAM._serialized_start=973
  _QUERYPLANSPARAM._serialized_end=1076
  _QUERYPLANSRESPONSE._serialized_start=1078
  _QUERYPLANSRESPONSE._serialized_end=1165
  _UPDATECOMPUTEPLANPARAM._serialized_start=1167
  _UPDATECOMPUTEPLANPARAM._serialized_end=1218
  _UPDATECOMPUTEPLANRESPONSE._serialized_start=1220
  _UPDATECOMPUTEPLANRESPONSE._serialized_end=1247
  _ISPLANRUNNINGPARAM._serialized_start=1249
  _ISPLANRUNNINGPARAM._serialized_end=1282
  _ISPLANRUNNINGRESPONSE._serialized_start=1284
  _ISPLANRUNNINGRESPONSE._serialized_end=1327
  _COMPUTEPLANSERVICE._serialized_start=1402
  _COMPUTEPLANSERVICE._serialized_end=1922
# @@protoc_insertion_point(module_scope)
