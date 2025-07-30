import inspect
import warnings
from functools import cached_property
from typing import (
    Type,
    Dict,
    Tuple,
    Iterable, Any
)

from pydantic import BaseModel
from pydantic._internal._decorators import PydanticDescriptorProxy
from pydantic.fields import Field as PydanticField, FieldInfo as PydanticFieldInfo
from pydantic_core import PydanticUndefined

from sqlmodel import SQLModel
from sqlmodel.main import FieldInfo as SqlModelFieldInfo


_RESERVED_BASE_ATTRS: set[str] = (
    set(dir(BaseModel)) |
    set(dir(SQLModel))
)
_ALLOWED_DUNDERS: set[str] = {"__str__", "__repr__", "__hash__", "__iter__"}
_DECORATED_VALIDATOR_TYPES = ["validators", "field_validators", "root_validators", "model_validators"]


def get_fields(
        model_cls: Type[BaseModel | SQLModel],
        exclude_fields: Iterable[str] = None,
        include_fields: Iterable[str] = None
) -> Dict[str, Tuple[Type, PydanticFieldInfo | SqlModelFieldInfo]]:
    exclude_fields = exclude_fields or []
    fields = {}
    for name, info in model_cls.model_fields.items():
        if name not in exclude_fields:
            if info.default is PydanticUndefined or info.default is ...:
                new_info = PydanticFieldInfo.merge_field_infos(info, default=PydanticUndefined)
            else:
                new_info = info
            fields[name] = (info.annotation, new_info)
    if include_fields:
        fields = {name: fields[name] for name in include_fields}
    return fields


def get_validators(
    model_cls: Type[BaseModel | SQLModel],
) -> Dict[str, PydanticDescriptorProxy]:
    validators = {}

    __pydantic_decorators__ = getattr(model_cls, "__pydantic_decorators__", None)

    if __pydantic_decorators__ is None:
        warnings.warn(f"Model {model_cls.__name__} does not have '__pydantic_decorators__' attr. ")
        return {}

    for validator_type in _DECORATED_VALIDATOR_TYPES:
        validators.update(
            {
                name: PydanticDescriptorProxy(wrapped=dec.func, decorator_info=dec.info, shim=None)
                for name, dec in getattr(__pydantic_decorators__, validator_type).items()
            }
        )

    return validators


def is_user_method(name: str, obj: Any) -> bool:
    if name in _RESERVED_BASE_ATTRS:
        return False
    if name.startswith("model_"):  # pydantic internals
        return False
    if name.startswith("_") and name not in _ALLOWED_DUNDERS:
        return False

    if getattr(obj, "__pydantic_validator__", None) is not None:
        return False
    if getattr(obj, "__pydantic_serializer__", None) is not None:
        return False

    # Разрешаем: обычные функции, classmethod/staticmethod, property/cached_property
    if inspect.isfunction(obj):
        return True
    if isinstance(obj, (classmethod, staticmethod, property, cached_property)):
        return True

    return False


def collect_user_members(src: type) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, obj in src.__dict__.items():
        if is_user_method(name, obj):
            out[name] = obj
    return out


def merge_init_signature(dst_cls: type[BaseModel | SQLModel]) -> None:
    params: list[inspect.Parameter] = []
    for fname, field in dst_cls.model_fields.items():
        default = (field.default
                   if field.default is not None and field.default is not ...  # noqa
                   else inspect._empty)
        params.append(
            inspect.Parameter(
                fname,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=default,
                annotation=field.annotation,
            )
        )
    dst_cls.__signature__ = inspect.Signature(parameters=params)  # type: ignore[attr-defined]


def augment_dir(dst_cls: type, extra_names: Iterable[str]) -> None:
    extra = set(extra_names)

    # если автор уже переопределял __dir__, сохраним поведение
    original_dir = getattr(dst_cls, "__dir__", None)

    def __dir__(self):  # type: ignore[override]
        base = set()  # type: ignore[var-annotated]
        if original_dir is not None:
            try:
                base = set(original_dir(self))  # type: ignore[misc]
            except TypeError:
                # если original_dir — нативный, без self; fallback
                base = set(type(self).__dict__.keys()) | set(dir(type(self)))
        return sorted(base | extra | set(dst_cls.model_fields.keys()))

    dst_cls.__dir__ = __dir__  # type: ignore[assignment]


def finalize_model(result_cls: type[BaseModel | SQLModel],
                   base_cls: type[BaseModel | SQLModel],
                   new_cls: type[BaseModel | SQLModel]) -> type[BaseModel | SQLModel]:
    copied_names: list[str] = []
    for src in (base_cls, new_cls):
        members = collect_user_members(src)
        for name, obj in members.items():
            # не трогаем имена полей
            if name in result_cls.model_fields:
                continue
            setattr(result_cls, name, obj)
            if name not in copied_names:
                copied_names.append(name)

    # гарантируем/обновляем сигнатуру конструктора
    merge_init_signature(result_cls)
    # улучшаем dir()
    augment_dir(result_cls, copied_names)

    # аккуратно сольём docstring: новый — приоритетный, базовый — как доп. секция
    base_doc = (base_cls.__doc__ or "").strip()
    new_doc = (new_cls.__doc__ or "").strip()
    if base_doc and new_doc:
        result_cls.__doc__ = f"{new_doc}\n\n---\nInherited from {base_cls.__name__}:\n{base_doc}"
    elif new_doc or base_doc:
        result_cls.__doc__ = new_doc or base_doc

    return result_cls
