# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: dataset.proto
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
    'dataset.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from . import datamanager_pb2 as datamanager__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rdataset.proto\x12\x0corchestrator\x1a\x11\x64\x61tamanager.proto\"\x8f\x01\n\x07\x44\x61taset\x12/\n\x0c\x64\x61ta_manager\x18\x01 \x01(\x0b\x32\x19.orchestrator.DataManager\x12\x18\n\x10\x64\x61ta_sample_keys\x18\x04 \x03(\tJ\x04\x08\x02\x10\x03J\x04\x08\x03\x10\x04R\x16train_data_sample_keysR\x15test_data_sample_keys\"\x1e\n\x0fGetDatasetParam\x12\x0b\n\x03key\x18\x01 \x01(\t2T\n\x0e\x44\x61tasetService\x12\x42\n\nGetDataset\x12\x1d.orchestrator.GetDatasetParam\x1a\x15.orchestrator.DatasetB+Z)github.com/substra/orchestrator/lib/assetb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'dataset_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z)github.com/substra/orchestrator/lib/asset'
  _globals['_DATASET']._serialized_start=51
  _globals['_DATASET']._serialized_end=194
  _globals['_GETDATASETPARAM']._serialized_start=196
  _globals['_GETDATASETPARAM']._serialized_end=226
  _globals['_DATASETSERVICE']._serialized_start=228
  _globals['_DATASETSERVICE']._serialized_end=312
# @@protoc_insertion_point(module_scope)
