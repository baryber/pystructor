import pytest

from pydantic import BaseModel, Field, ValidationError
from sqlmodel import SQLModel

from pystructor import partial
from pystructor import omit
from pystructor import pick


@pytest.fixture(params=[
    omit,
    pick
])
def required_decorator(request):
    return request.param


def test_validation(FooSLQModelClassParametrized, required_decorator):

    @required_decorator(FooSLQModelClassParametrized)
    class Foo(BaseModel):
        additional_field: str = Field(description="Additional field")

    with pytest.raises(ValidationError) as error:
        Foo.model_validate({})

    errors = {err['loc'][0] for err in error.value.errors()}
    assert {"additional_field", "name", "email"} < errors


def test_partial_validation(FooSLQModelClassParametrized):

    @partial(FooSLQModelClassParametrized)
    class Foo(SQLModel):
        pass

    try:
        Foo.model_validate({})
    except ValidationError:
        pytest.fail("Partial validation should not raise ValidationError")


def test_partial_validation_with_required_field(FooSLQModelClassParametrized):
    @partial(FooSLQModelClassParametrized)
    class Foo(SQLModel):
        additional_field: str = Field(description="Additional field")

    with pytest.raises(ValidationError) as error:
        Foo.model_validate({})

    errors = {err['loc'][0] for err in error.value.errors()}
    assert {"additional_field"} == errors
