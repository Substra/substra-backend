"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import collections.abc
import common_pb2
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import google.protobuf.timestamp_pb2
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _FunctionAction:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _FunctionActionEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_FunctionAction.ValueType], builtins.type):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    FUNCTION_ACTION_UNKNOWN: _FunctionAction.ValueType  # 0
    FUNCTION_ACTION_BUILDING: _FunctionAction.ValueType  # 1
    FUNCTION_ACTION_CANCELED: _FunctionAction.ValueType  # 2
    FUNCTION_ACTION_FAILED: _FunctionAction.ValueType  # 3
    FUNCTION_ACTION_READY: _FunctionAction.ValueType  # 4

class FunctionAction(_FunctionAction, metaclass=_FunctionActionEnumTypeWrapper): ...

FUNCTION_ACTION_UNKNOWN: FunctionAction.ValueType  # 0
FUNCTION_ACTION_BUILDING: FunctionAction.ValueType  # 1
FUNCTION_ACTION_CANCELED: FunctionAction.ValueType  # 2
FUNCTION_ACTION_FAILED: FunctionAction.ValueType  # 3
FUNCTION_ACTION_READY: FunctionAction.ValueType  # 4
global___FunctionAction = FunctionAction

class _FunctionStatus:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _FunctionStatusEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_FunctionStatus.ValueType], builtins.type):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    FUNCTION_STATUS_UNKNOWN: _FunctionStatus.ValueType  # 0
    FUNCTION_STATUS_WAITING: _FunctionStatus.ValueType  # 1
    FUNCTION_STATUS_BUILDING: _FunctionStatus.ValueType  # 2
    FUNCTION_STATUS_READY: _FunctionStatus.ValueType  # 3
    FUNCTION_STATUS_CANCELED: _FunctionStatus.ValueType  # 4
    FUNCTION_STATUS_FAILED: _FunctionStatus.ValueType  # 5

class FunctionStatus(_FunctionStatus, metaclass=_FunctionStatusEnumTypeWrapper): ...

FUNCTION_STATUS_UNKNOWN: FunctionStatus.ValueType  # 0
FUNCTION_STATUS_WAITING: FunctionStatus.ValueType  # 1
FUNCTION_STATUS_BUILDING: FunctionStatus.ValueType  # 2
FUNCTION_STATUS_READY: FunctionStatus.ValueType  # 3
FUNCTION_STATUS_CANCELED: FunctionStatus.ValueType  # 4
FUNCTION_STATUS_FAILED: FunctionStatus.ValueType  # 5
global___FunctionStatus = FunctionStatus

@typing_extensions.final
class FunctionInput(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KIND_FIELD_NUMBER: builtins.int
    MULTIPLE_FIELD_NUMBER: builtins.int
    OPTIONAL_FIELD_NUMBER: builtins.int
    kind: common_pb2.AssetKind.ValueType
    multiple: builtins.bool
    optional: builtins.bool
    def __init__(
        self,
        *,
        kind: common_pb2.AssetKind.ValueType = ...,
        multiple: builtins.bool = ...,
        optional: builtins.bool = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["kind", b"kind", "multiple", b"multiple", "optional", b"optional"]) -> None: ...

global___FunctionInput = FunctionInput

@typing_extensions.final
class FunctionOutput(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KIND_FIELD_NUMBER: builtins.int
    MULTIPLE_FIELD_NUMBER: builtins.int
    kind: common_pb2.AssetKind.ValueType
    multiple: builtins.bool
    def __init__(
        self,
        *,
        kind: common_pb2.AssetKind.ValueType = ...,
        multiple: builtins.bool = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["kind", b"kind", "multiple", b"multiple"]) -> None: ...

global___FunctionOutput = FunctionOutput

@typing_extensions.final
class Function(google.protobuf.message.Message):
    """Function represents the code which will be used
    to produce or test a model.
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing_extensions.final
    class MetadataEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        value: builtins.str
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: builtins.str = ...,
        ) -> None: ...
        def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]) -> None: ...

    @typing_extensions.final
    class InputsEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___FunctionInput: ...
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: global___FunctionInput | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["value", b"value"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]) -> None: ...

    @typing_extensions.final
    class OutputsEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___FunctionOutput: ...
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: global___FunctionOutput | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["value", b"value"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]) -> None: ...

    KEY_FIELD_NUMBER: builtins.int
    NAME_FIELD_NUMBER: builtins.int
    DESCRIPTION_FIELD_NUMBER: builtins.int
    FUNCTION_FIELD_NUMBER: builtins.int
    PERMISSIONS_FIELD_NUMBER: builtins.int
    OWNER_FIELD_NUMBER: builtins.int
    CREATION_DATE_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    INPUTS_FIELD_NUMBER: builtins.int
    OUTPUTS_FIELD_NUMBER: builtins.int
    STATUS_FIELD_NUMBER: builtins.int
    key: builtins.str
    name: builtins.str
    @property
    def description(self) -> common_pb2.Addressable: ...
    @property
    def function(self) -> common_pb2.Addressable: ...
    @property
    def permissions(self) -> common_pb2.Permissions: ...
    owner: builtins.str
    @property
    def creation_date(self) -> google.protobuf.timestamp_pb2.Timestamp: ...
    @property
    def metadata(self) -> google.protobuf.internal.containers.ScalarMap[builtins.str, builtins.str]: ...
    @property
    def inputs(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___FunctionInput]: ...
    @property
    def outputs(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___FunctionOutput]: ...
    status: global___FunctionStatus.ValueType
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        name: builtins.str = ...,
        description: common_pb2.Addressable | None = ...,
        function: common_pb2.Addressable | None = ...,
        permissions: common_pb2.Permissions | None = ...,
        owner: builtins.str = ...,
        creation_date: google.protobuf.timestamp_pb2.Timestamp | None = ...,
        metadata: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
        inputs: collections.abc.Mapping[builtins.str, global___FunctionInput] | None = ...,
        outputs: collections.abc.Mapping[builtins.str, global___FunctionOutput] | None = ...,
        status: global___FunctionStatus.ValueType = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["creation_date", b"creation_date", "description", b"description", "function", b"function", "permissions", b"permissions"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["creation_date", b"creation_date", "description", b"description", "function", b"function", "inputs", b"inputs", "key", b"key", "metadata", b"metadata", "name", b"name", "outputs", b"outputs", "owner", b"owner", "permissions", b"permissions", "status", b"status"]) -> None: ...

global___Function = Function

@typing_extensions.final
class NewFunction(google.protobuf.message.Message):
    """NewFunction is used to register an Function.
    It will be processed into an Function.
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing_extensions.final
    class MetadataEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        value: builtins.str
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: builtins.str = ...,
        ) -> None: ...
        def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]) -> None: ...

    @typing_extensions.final
    class InputsEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___FunctionInput: ...
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: global___FunctionInput | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["value", b"value"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]) -> None: ...

    @typing_extensions.final
    class OutputsEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___FunctionOutput: ...
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: global___FunctionOutput | None = ...,
        ) -> None: ...
        def HasField(self, field_name: typing_extensions.Literal["value", b"value"]) -> builtins.bool: ...
        def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]) -> None: ...

    KEY_FIELD_NUMBER: builtins.int
    NAME_FIELD_NUMBER: builtins.int
    DESCRIPTION_FIELD_NUMBER: builtins.int
    FUNCTION_FIELD_NUMBER: builtins.int
    NEW_PERMISSIONS_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    INPUTS_FIELD_NUMBER: builtins.int
    OUTPUTS_FIELD_NUMBER: builtins.int
    key: builtins.str
    name: builtins.str
    @property
    def description(self) -> common_pb2.Addressable: ...
    @property
    def function(self) -> common_pb2.Addressable: ...
    @property
    def new_permissions(self) -> common_pb2.NewPermissions: ...
    @property
    def metadata(self) -> google.protobuf.internal.containers.ScalarMap[builtins.str, builtins.str]: ...
    @property
    def inputs(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___FunctionInput]: ...
    @property
    def outputs(self) -> google.protobuf.internal.containers.MessageMap[builtins.str, global___FunctionOutput]: ...
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        name: builtins.str = ...,
        description: common_pb2.Addressable | None = ...,
        function: common_pb2.Addressable | None = ...,
        new_permissions: common_pb2.NewPermissions | None = ...,
        metadata: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
        inputs: collections.abc.Mapping[builtins.str, global___FunctionInput] | None = ...,
        outputs: collections.abc.Mapping[builtins.str, global___FunctionOutput] | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["description", b"description", "function", b"function", "new_permissions", b"new_permissions"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["description", b"description", "function", b"function", "inputs", b"inputs", "key", b"key", "metadata", b"metadata", "name", b"name", "new_permissions", b"new_permissions", "outputs", b"outputs"]) -> None: ...

global___NewFunction = NewFunction

@typing_extensions.final
class GetFunctionParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KEY_FIELD_NUMBER: builtins.int
    key: builtins.str
    def __init__(
        self,
        *,
        key: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["key", b"key"]) -> None: ...

global___GetFunctionParam = GetFunctionParam

@typing_extensions.final
class QueryFunctionsResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    FUNCTIONS_FIELD_NUMBER: builtins.int
    NEXT_PAGE_TOKEN_FIELD_NUMBER: builtins.int
    @property
    def Functions(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___Function]: ...
    next_page_token: builtins.str
    def __init__(
        self,
        *,
        Functions: collections.abc.Iterable[global___Function] | None = ...,
        next_page_token: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["Functions", b"Functions", "next_page_token", b"next_page_token"]) -> None: ...

global___QueryFunctionsResponse = QueryFunctionsResponse

@typing_extensions.final
class FunctionQueryFilter(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    COMPUTE_PLAN_KEY_FIELD_NUMBER: builtins.int
    compute_plan_key: builtins.str
    def __init__(
        self,
        *,
        compute_plan_key: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["compute_plan_key", b"compute_plan_key"]) -> None: ...

global___FunctionQueryFilter = FunctionQueryFilter

@typing_extensions.final
class QueryFunctionsParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PAGE_TOKEN_FIELD_NUMBER: builtins.int
    PAGE_SIZE_FIELD_NUMBER: builtins.int
    FILTER_FIELD_NUMBER: builtins.int
    page_token: builtins.str
    page_size: builtins.int
    @property
    def filter(self) -> global___FunctionQueryFilter: ...
    def __init__(
        self,
        *,
        page_token: builtins.str = ...,
        page_size: builtins.int = ...,
        filter: global___FunctionQueryFilter | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["filter", b"filter"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["filter", b"filter", "page_size", b"page_size", "page_token", b"page_token"]) -> None: ...

global___QueryFunctionsParam = QueryFunctionsParam

@typing_extensions.final
class UpdateFunctionParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KEY_FIELD_NUMBER: builtins.int
    NAME_FIELD_NUMBER: builtins.int
    key: builtins.str
    name: builtins.str
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        name: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "name", b"name"]) -> None: ...

global___UpdateFunctionParam = UpdateFunctionParam

@typing_extensions.final
class UpdateFunctionResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___UpdateFunctionResponse = UpdateFunctionResponse

@typing_extensions.final
class ApplyFunctionActionParam(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    FUNCTION_KEY_FIELD_NUMBER: builtins.int
    ACTION_FIELD_NUMBER: builtins.int
    function_key: builtins.str
    action: global___FunctionAction.ValueType
    def __init__(
        self,
        *,
        function_key: builtins.str = ...,
        action: global___FunctionAction.ValueType = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["action", b"action", "function_key", b"function_key"]) -> None: ...

global___ApplyFunctionActionParam = ApplyFunctionActionParam

@typing_extensions.final
class ApplyFunctionActionResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    def __init__(
        self,
    ) -> None: ...

global___ApplyFunctionActionResponse = ApplyFunctionActionResponse
