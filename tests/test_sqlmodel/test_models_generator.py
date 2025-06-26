import pytest

from pydantic import Field
from pydantic import ValidationError

from pystructor import generate_crud_schemas


def test_create_schema_excludes_id(FooSLQModelClassParametrized):
    CreateSchema, _, _ = generate_crud_schemas(FooSLQModelClassParametrized)
    assert "id" not in CreateSchema.model_fields


def test_read_schema_excludes_password(FooSLQModelClassParametrized):
    _, ReadSchema, _ = generate_crud_schemas(FooSLQModelClassParametrized)
    assert "password" not in ReadSchema.model_fields
    # поля name и id есть
    assert "name" in ReadSchema.model_fields
    assert "email" in ReadSchema.model_fields

    if "id" in FooSLQModelClassParametrized.model_fields:
        assert "id" in ReadSchema.model_fields


def test_update_schema_optional_fields(FooSLQModelClassParametrized):
    _, _, UpdateSchema = generate_crud_schemas(FooSLQModelClassParametrized)
    # все поля обязательные стали optional
    assert UpdateSchema.model_fields["name"].is_required() is False
    assert UpdateSchema.model_fields["password"].is_required() is False


def test_schemas_descriptions(FooSLQModelClassParametrized):
    crud_schemas = generate_crud_schemas(FooSLQModelClassParametrized)
    for schema in crud_schemas:
        assert schema.model_fields["name"].description == "Name"

        if "Read" not in schema.__name__:
            # password есть только в create и update
            assert schema.model_fields["password"].description == "Password"


def test_include_additional_field_to_read(
        FooSLQModelClassParametrized,
        read_data
):
    def compute():
        return 10

    _, ReadSchema, _ = generate_crud_schemas(
        FooSLQModelClassParametrized,
        include_to_read={
            "computed": (int, Field(default_factory=compute))
        }
    )
    # дополнительное поле есть и default работает
    inst = ReadSchema(**read_data)
    assert inst.computed == 10


def test_constraints(FooSLQModelClassParametrized):
    _, ReadSchema, _ = generate_crud_schemas(
        FooSLQModelClassParametrized,
    )

    read_schema = ReadSchema.schema()

    assert read_schema["properties"]["name"]["maxLength"] == 20
