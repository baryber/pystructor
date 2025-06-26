from typing import (
    Type,
    Dict,
    Tuple,
    Iterable
)

from pydantic import BaseModel
from pydantic.fields import Field as PydanticField, FieldInfo as PydanticFieldInfo
from pydantic_core import PydanticUndefined

from sqlmodel import SQLModel
from sqlmodel.main import FieldInfo as SqlModelFieldInfo


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
