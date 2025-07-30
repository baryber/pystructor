import inspect
from typing import (
    Any,
    TypeVar,
    get_args,
    get_origin,
)

from pydantic import BaseModel, ConfigDict, create_model
from pydantic_core import PydanticUndefined
from sqlmodel import SQLModel
from sqlmodel.main import FieldInfo

from .utils import get_fields, finalize_model, get_validators


try:
    from fastapi import Form
except ImportError:
    Form = None


ModelT = TypeVar("ModelT", BaseModel, SQLModel)


def partial(model_cls: type[ModelT]):

    def decorator(new_cls: type[BaseModel | SQLModel]) -> type[ModelT]:

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

        model = create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            **{
                **base_fields,
                **new_fields
            },
            __validators__={
                **get_validators(model_cls),
                **get_validators(new_cls)
            }
        )
        return finalize_model(model, model_cls, new_cls)  # type: ignore[return-value]

    return decorator


def omit(model_cls: type[ModelT], *fields: str):

    def decorator(new_cls: type[BaseModel | SQLModel]) -> type[ModelT]:

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
            },
            __validators__={
                **get_validators(model_cls),
                **get_validators(new_cls)
            }
        )

    return decorator


def copy(model_cls: type[ModelT]):
    def decorator(new_cls: type[BaseModel | SQLModel]) -> type[ModelT]:

        if not issubclass(model_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{model_cls} must be subclass of {BaseModel} or {SQLModel}")

        if not issubclass(new_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{new_cls} must be subclass of {BaseModel} or {SQLModel}")

        base_fields = get_fields(model_cls)
        new_fields = get_fields(new_cls)

        model = create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            **{
                **base_fields,
                **new_fields
            },
            __validators__={
                **get_validators(model_cls),
                **get_validators(new_cls)
            }
        )
        return finalize_model(model, model_cls, new_cls)  # type: ignore[return-value]

    return decorator


def pick(model_cls: type[ModelT], *fields: str):

    def decorator(new_cls: type[BaseModel | SQLModel]) -> type[ModelT]:

        if not issubclass(model_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{model_cls} must be subclass of {BaseModel} or {SQLModel}")

        if not issubclass(new_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{new_cls} must be subclass of {BaseModel} or {SQLModel}")

        base_fields = get_fields(model_cls, include_fields=fields)
        new_fields: dict[str, tuple[Any, FieldInfo]] = get_fields(new_cls)

        return create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            **{
                **base_fields,
                **new_fields
            },
            __validators__={
                **get_validators(model_cls),
                **get_validators(new_cls)
            }
        )

    return decorator


def required(model_cls: type[ModelT]):
    def decorator(new_cls: type[BaseModel | SQLModel]) -> type[ModelT]:

        if not issubclass(model_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{model_cls} must be subclass of {BaseModel} or {SQLModel}")

        if not issubclass(new_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{new_cls} must be subclass of {BaseModel} or {SQLModel}")

        base_fields = get_fields(model_cls)
        new_fields = get_fields(new_cls)

        for name, (typ, finfo) in base_fields.items():
            finfo.default = PydanticUndefined  # make field required
            base_fields[name] = (typ, finfo)

        return create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            **{
                **base_fields,
                **new_fields
            },
            __validators__={
                **get_validators(model_cls),
                **get_validators(new_cls)
            }
        )

    return decorator


def readonly(model_cls: type[ModelT]):
    def decorator(new_cls: type[BaseModel | SQLModel]) -> type[ModelT]:

        if not issubclass(model_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{model_cls} must be subclass of {BaseModel} or {SQLModel}")

        if not issubclass(new_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{new_cls} must be subclass of {BaseModel} or {SQLModel}")

        base_fields = get_fields(model_cls)
        new_fields = get_fields(new_cls)

        return create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            __config__=ConfigDict(frozen=True),
            **{
                **base_fields,
                **new_fields
            },
            __validators__={
                **get_validators(model_cls),
                **get_validators(new_cls)
            }
        )

    return decorator


def non_nullable(model_cls: type[ModelT]):
    def decorator(new_cls: type[BaseModel | SQLModel]) -> type[ModelT]:

        if not issubclass(model_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{model_cls} must be subclass of {BaseModel} or {SQLModel}")

        if not issubclass(new_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{new_cls} must be subclass of {BaseModel} or {SQLModel}")

        base_fields = get_fields(model_cls)
        new_fields = get_fields(new_cls)

        for name, (typ, finfo) in base_fields.items():
            origin = get_origin(typ)
            if origin is None:
                args = ()
            else:
                args = get_args(typ)

            if args:
                args = tuple(a for a in args if a is not type(None))  # noqa: E721
                if len(args) == 1:
                    typ = args[0]
                else:
                    typ = origin[args]
            if finfo.default is None:
                finfo.default = PydanticUndefined
            base_fields[name] = (typ, finfo)

        return create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            **{
                **base_fields,
                **new_fields
            },
            __validators__={
                **get_validators(model_cls),
                **get_validators(new_cls)
            }
        )

    return decorator


def deep_partial(model_cls: type[ModelT]):
    def _partialize_model(cls: type[ModelT]) -> type[ModelT]:
        fields = get_fields(cls)
        for fname, (ftype, finfo) in fields.items():
            if isinstance(ftype, type) and issubclass(ftype, (BaseModel, SQLModel)):
                ftype = _partialize_model(ftype)
            finfo.default = None
            ftype = ftype | None
            fields[fname] = (ftype, finfo)
        return create_model(f"{cls.__name__}Partial", **fields)  # type: ignore

    def decorator(new_cls: type[BaseModel | SQLModel]) -> type[ModelT]:
        if not issubclass(model_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{model_cls} must be subclass of {BaseModel} or {SQLModel}")
        if not issubclass(new_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{new_cls} must be subclass of {BaseModel} or {SQLModel}")

        base_partial = _partialize_model(model_cls)
        base_fields = get_fields(base_partial)
        new_fields = get_fields(new_cls)

        return create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            **{
                **base_fields,
                **new_fields
            },
            __validators__={
                **get_validators(model_cls),
                **get_validators(new_cls)
            }
        )

    return decorator


def exclude_type(model_cls: type[ModelT], type_: Any):
    """Remove specific type from Union annotations."""

    def decorator(new_cls: type[BaseModel | SQLModel]) -> type[ModelT]:
        if not issubclass(model_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{model_cls} must be subclass of {BaseModel} or {SQLModel}")

        if not issubclass(new_cls, (BaseModel, SQLModel)):
            raise TypeError(f"{new_cls} must be subclass of {BaseModel} or {SQLModel}")

        base_fields = get_fields(model_cls)
        new_fields = get_fields(new_cls)

        for name, (typ, finfo) in base_fields.items():
            origin = get_origin(typ)
            if origin is None:
                args = ()
            else:
                args = get_args(typ)
            if args:
                new_args = tuple(a for a in args if a is not type_)
                if len(new_args) != len(args):
                    if not new_args:
                        typ = Any
                    elif len(new_args) == 1:
                        typ = new_args[0]
                    else:
                        typ = origin[new_args]
                    base_fields[name] = (typ, finfo)

        return create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            **{
                **base_fields,
                **new_fields
            },
            __validators__={
                **get_validators(model_cls),
                **get_validators(new_cls)
            }
        )

    return decorator


def merge(model_cls: type[ModelT], other_cls: type[ModelT]):
    def decorator(new_cls: type[BaseModel | SQLModel]) -> type[ModelT]:

        for cls in (model_cls, other_cls, new_cls):
            if not issubclass(cls, (BaseModel, SQLModel)):
                raise TypeError(f"{cls} must be subclass of {BaseModel} or {SQLModel}")

        base_fields = get_fields(model_cls)
        other_fields = get_fields(other_cls)
        new_fields = get_fields(new_cls)

        return create_model(
            new_cls.__name__,
            __doc__=new_cls.__doc__,
            __base__=new_cls,
            __module__=new_cls.__module__,
            **{
                **base_fields,
                **other_fields,
                **new_fields,
            },
            __validators__={
                **get_validators(model_cls),
                **get_validators(new_cls)
            }
        )

    return decorator


def as_form(model_cls: type[ModelT]):
    if Form is None:
        raise ImportError("FastAPI is required to use the `as_form` decorator, run `pip isntall fastapi` command.")

    if not issubclass(model_cls, (BaseModel, SQLModel)):
        raise TypeError(f"{model_cls} must be subclass of {BaseModel} or {SQLModel}")

    def _as_form(**data: Any) -> ModelT:  # type: ignore
        return model_cls(**data)  # type: ignore

    params = []
    for name, field in model_cls.model_fields.items():
        default = field.default if field.default is not PydanticUndefined else ...
        form_field = Form(default)
        params.append(
            inspect.Parameter(
                name,
                inspect.Parameter.POSITIONAL_ONLY,
                default=form_field,
                annotation=field.annotation,
            )
        )

    _as_form.__signature__ = inspect.Signature(parameters=params)  # type: ignore
    model_cls.as_form = _as_form
    return model_cls
