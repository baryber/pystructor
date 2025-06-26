import pytest

from pydantic import BaseModel, Field

from pystructor import partial
from pystructor import omit
from pystructor import pick


@pytest.mark.parametrize(
    ("decorator"),
    (partial, omit, pick)
)
def test_no_pydantic(FooModelParametrized, decorator):

    with pytest.raises(TypeError):
        @decorator(FooModelParametrized)
        class PartialFooModel:
            required_field: str = Field(...)

    with pytest.raises(TypeError):

        class BarModel:
            a: str

        @decorator(BarModel)
        class PartialFooModel(BaseModel):
            required_field: str
