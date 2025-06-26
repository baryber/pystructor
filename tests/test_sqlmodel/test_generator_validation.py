import pytest
from pydantic import ValidationError

from pystructor import generate_crud_schemas


def test_crud_schema_validation(FooSLQModelClassParametrized):
    CreateSchema, ReadSchema, UpdateSchema = generate_crud_schemas(FooSLQModelClassParametrized)

    with pytest.raises(ValidationError) as e_create:
        CreateSchema.model_validate({})
    errors = {err['loc'][0] for err in e_create.value.errors()}
    assert {"name", "password", "email"} <= errors

    with pytest.raises(ValidationError) as e_read:
        ReadSchema.model_validate({})
    errors = {err['loc'][0] for err in e_read.value.errors()}
    assert {"name", "email"} <= errors

    try:
        UpdateSchema.model_validate({})
    except ValidationError:
        pytest.fail("UpdateSchema не должен вызывать ValidationError при пустом вводе")
