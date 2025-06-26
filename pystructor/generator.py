from typing import Any, Dict, List, Union, Tuple, Optional, Callable, Annotated, ForwardRef, Type, TypeVar, get_origin, get_args

from sqlmodel import SQLModel
from sqlmodel.main import FieldInfo

from pydantic import create_model
from pydantic.fields import FieldInfo as PydanticFieldInfo
from pydantic._internal._model_construction import ModelMetaclass

from sqlalchemy.orm.attributes import InstrumentedAttribute

from .utils import get_fields


ModelT = TypeVar("ModelT", bound=SQLModel)
IncludeFieldType = Union[
    str,
    Annotated[Any, FieldInfo],
    Tuple[Type, FieldInfo],
    Type
]
IncludeFieldsType = Dict[str, IncludeFieldType]

CREATE_SCHEMA_EXCLUDE_FIELDS = ["id"]
READ_SCHEMA_EXCLUDE_FIELDS = ["password"]


def _to_exclude(
    field_name: str,
    exclude_fields: List[Union[str, InstrumentedAttribute]]
) -> bool:
    for ex in exclude_fields:
        if isinstance(ex, str) and field_name == ex:
            return True
        if isinstance(ex, InstrumentedAttribute) and field_name == ex.key:
            return True
    return False


def _parse_field_definition(field_def: Any) -> Tuple[Any, FieldInfo]:
    # Разбираем разные варианты определения дополнительных полей
    # 1) кортеж (тип, FieldInfo)
    if isinstance(field_def, tuple):
        if len(field_def) != 2:
            raise ValueError("Tuple must be (Type, FieldInfo).")
        field_type, field_info = field_def
        if isinstance(field_type, str):
            field_type = ForwardRef(field_type)
        if not isinstance(field_info, (FieldInfo, PydanticFieldInfo)):
            raise TypeError("Second element must be FieldInfo.")
        field_info.annotation = field_type
        return field_type, field_info

    # 2) строка -> ForwardRef
    if isinstance(field_def, str):
        t = ForwardRef(field_def)
        return t, FieldInfo(annotation=t)

    # 3) Annotated[Type, FieldInfo]
    origin = get_origin(field_def)
    if origin is Annotated:
        args = get_args(field_def)
        if not args:
            raise ValueError("Annotated[] без аргументов.")
        field_type = args[0]
        finfo = next((a for a in args[1:] if isinstance(a, FieldInfo)), FieldInfo())
        if isinstance(field_type, str):
            field_type = ForwardRef(field_type)
        finfo.annotation = field_type
        return field_type, finfo

    # 4) просто тип
    if isinstance(field_def, type):
        return field_def, FieldInfo(annotation=field_def)

    raise TypeError(f"Неподдерживаемый тип: {field_def!r}")


def rebuild_models(models: List[Type[ModelT]]) -> List[Type[ModelT]]:
    for m in models:
        m.__module__ = "src.models"
        m.model_rebuild()
    return models


def rebuild_all_models(_locals: Dict[str, Any]) -> None:
    for cls in _locals.values():
        if isinstance(cls, ModelMetaclass):
            cls.model_rebuild(_types_namespace=_locals)


def generate_create_schema(
    base_name: str,
    fields: Dict[str, Tuple[Type, FieldInfo]],
    include_fields: Optional[Dict[str, Tuple[Type, FieldInfo]]] = None,
    exclude_fields: Optional[List[Union[str, InstrumentedAttribute]]] = None
) -> Type[ModelT]:
    include_fields = include_fields or {}
    exclude = CREATE_SCHEMA_EXCLUDE_FIELDS + (exclude_fields or [])

    create_fields: Dict[str, Tuple[Any, FieldInfo]] = {
        name: (typ, finfo)
        for name, (typ, finfo) in fields.items()
        if not _to_exclude(name, exclude)
    }

    # добавляем user-defined поля
    for name, (typ, finfo) in include_fields.items():
        create_fields[name] = (typ, finfo)

    return create_model(f"{base_name}Create", **create_fields)  # type: ignore


def generate_read_schema(
    base_name: str,
    fields: Dict[str, Tuple[Type, FieldInfo]],
    include_fields: Optional[IncludeFieldsType] = None,
    exclude_fields: Optional[List[InstrumentedAttribute]] = None
) -> Type[ModelT]:
    include_fields = include_fields or {}
    exclude = READ_SCHEMA_EXCLUDE_FIELDS + (exclude_fields or [])

    read_fields = {
        name: (typ, finfo)
        for name, (typ, finfo) in fields.items()
        if not _to_exclude(name, exclude)
    }

    for name, field_def in include_fields.items():
        typ, finfo = _parse_field_definition(field_def)
        read_fields[name] = (typ, finfo)

    return create_model(f"{base_name}Read", **read_fields)  # type: ignore


def generate_update_schema(
    base_name: str,
    fields: Dict[str, Tuple[Type, FieldInfo]],
    include_fields: Optional[IncludeFieldsType] = None,
    exclude_fields: Optional[List[InstrumentedAttribute]] = None
) -> Type[ModelT]:
    include_fields = include_fields or {}
    exclude = exclude_fields or []

    update_fields: Dict[str, Tuple[Any, FieldInfo]] = {}
    for name, (typ, finfo) in fields.items():
        if _to_exclude(name, exclude):
            continue
        # делаем каждое поле Optional
        finfo.default = None  # type: ignore
        update_fields[name] = (typ, finfo)

    for name, field_def in include_fields.items():
        typ, finfo = _parse_field_definition(field_def)
        finfo.default = None  # type: ignore
        update_fields[name] = (typ, finfo)

    return create_model(f"{base_name}Update", **update_fields)  # type: ignore


def generate_crud_schemas(
    table_cls: Type[ModelT],
    include_to_read: Optional[IncludeFieldsType] = None,
    include_to_update: Optional[IncludeFieldsType] = None,
    include_to_create: Optional[Dict[str, Tuple[Type, FieldInfo]]] = None,
    exclude_from_create: Optional[List[InstrumentedAttribute]] = None,
    exclude_from_read: Optional[List[InstrumentedAttribute]] = None,
    exclude_from_update: Optional[List[InstrumentedAttribute]] = None,
    include_callables: Optional[List[Callable]] = None
) -> Tuple[Type[ModelT], Type[ModelT], Type[ModelT]]:
    base_name = table_cls.__name__.replace("Base", "")

    all_fields = get_fields(table_cls)

    CreateSchema = generate_create_schema(
        base_name=base_name,
        fields=all_fields,
        include_fields=include_to_create,
        exclude_fields=exclude_from_create
    )
    ReadSchema = generate_read_schema(
        base_name=base_name,
        fields=all_fields,
        include_fields=include_to_read,
        exclude_fields=exclude_from_read
    )
    UpdateSchema = generate_update_schema(
        base_name=base_name,
        fields=all_fields,
        include_fields=include_to_update,
        exclude_fields=exclude_from_update
    )

    if include_callables:
        for fn in include_callables:
            setattr(CreateSchema, fn.__name__, fn)
            setattr(ReadSchema, fn.__name__, fn)
            setattr(UpdateSchema, fn.__name__, fn)

    return CreateSchema, ReadSchema, UpdateSchema
