from typing import (
    Type,
    TypeVar,
    Dict,
    Tuple,
    Any,
)

from sqlmodel import SQLModel
from sqlmodel.main import FieldInfo

from pydantic import BaseModel, create_model

from .utils import get_fields


ModelT = TypeVar("ModelT", BaseModel, SQLModel)


def partial(model_cls: Type[ModelT]):

    def decorator(new_cls: Type[BaseModel | SQLModel]) -> Type[ModelT]:

        if not issubclass(model_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{model_cls} must be subclass of {BaseModel} or {SQLModel}")

        if not issubclass(new_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{new_cls} must be subclass of {BaseModel} or {SQLModel}")

        base_fields = get_fields(model_cls)
        new_fields = get_fields(new_cls)

        for name, (typ, finfo) in base_fields.items():
            # делаем каждое поле Optional
            typ = typ | None
            finfo.default = None
            base_fields[name] = (typ, finfo)  # type: ignore

        return create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            **{
                **base_fields,
                **new_fields
            }
        )

    return decorator


def omit(model_cls: Type[ModelT], *fields: str):

    def decorator(new_cls: Type[BaseModel | SQLModel]) -> Type[ModelT]:

        if not issubclass(model_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{model_cls} must be subclass of {BaseModel} or {SQLModel}")

        if not issubclass(new_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{new_cls} must be subclass of {BaseModel} or {SQLModel}")

        base_fields = get_fields(model_cls, exclude_fields=fields)
        new_fields = get_fields(new_cls)

        return create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            **{
                **base_fields,
                **new_fields
            }
        )

    return decorator


def pick(model_cls: Type[ModelT], *fields: str):

    def decorator(new_cls: Type[BaseModel | SQLModel]) -> Type[ModelT]:

        if not issubclass(model_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{model_cls} must be subclass of {BaseModel} or {SQLModel}")

        if not issubclass(new_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{new_cls} must be subclass of {BaseModel} or {SQLModel}")

        base_fields = get_fields(model_cls, include_fields=fields)
        new_fields: Dict[str, Tuple[Any, FieldInfo]] = get_fields(new_cls)

        return create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            **{
                **base_fields,
                **new_fields
            }
        )

    return decorator


def required(model_cls: Type[ModelT]):
    # TODO: Implement required decorator
    raise NotImplementedError


def readonly(model_cls: Type[ModelT]):
    # TODO: Implement readonly decorator (frozen=True in Pydantic v2)
    raise NotImplementedError


def non_nullable(model_cls: Type[ModelT]):
    # TODO: Implement non_nullable decorator
    raise NotImplementedError


def deep_partial(model_cls: Type[ModelT]):
    # TODO: Implement deep_partial decorator
    raise NotImplementedError


def exclude_type(model_cls: Type[ModelT], type_: Any):
    # TODO: Implement exclude_type decorator
    """
    .. highlight:: python
    .. code-block:: python
        class Bar(BaseModel):
            data: str | int | None

        @exclude_type(Bar, None)
        class BarNonNullable: pass

    :param model_cls:
    :param type_:
    :return:
    """
    raise NotImplementedError


def merge(model_cls: Type[ModelT], other_cls: Type[ModelT]):
    # TODO: Implement merge decorator
    raise NotImplementedError


# --- Ideas ---


def as_form(model_cls: Type[ModelT]):
    # TODO: Implement as_form decorator, turn into FastAPI Form
    raise NotImplementedError