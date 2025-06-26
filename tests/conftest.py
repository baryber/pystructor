import pytest
from sqlmodel import create_engine
from sqlmodel import SQLModel, Session, Field as SQLModelField
from sqlmodel._compat import SQLModelConfig
from pydantic import BaseModel, Field as PydanticField


@pytest.fixture(scope="session")
def engine():
    engine = create_engine("sqlite://", echo=False)
    return engine


@pytest.fixture(scope="function")
def session(engine):
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


class _FooSQLModelBase(SQLModel):
    name: str = SQLModelField(max_length=20, description="Name")
    password: str = SQLModelField(max_length=20, description="Password")
    email: str = SQLModelField(..., max_length=50, description="Email Address")

    constraint_positive_int: int | None = SQLModelField(default=10, gt=0)

    model_config = SQLModelConfig(
        validate_assignment=True,
        from_attributes=True
    )


class _FooSQLModelTable(_FooSQLModelBase, table=True):
    __tablename__ = "foo_table"

    id: int | None = SQLModelField(default=None, primary_key=True)


class _FooPydanticModel(BaseModel):
    id: int | None = PydanticField(default=None, primary_key=True)
    name: str = PydanticField(max_length=20, description="Name")
    password: str = PydanticField(max_length=20, description="Password")
    email: str = PydanticField(..., max_length=50, description="Email Address")

    constraint_positive_int: int | None = PydanticField(default=10, gt=0)


@pytest.fixture
def FooSQLModelBase():
    return _FooSQLModelBase


@pytest.fixture
def FooSQLModelTable():
    return _FooSQLModelTable


@pytest.fixture
def FooPydanticModel():
    return _FooPydanticModel


@pytest.fixture(params=[
    _FooSQLModelBase,
    _FooSQLModelTable,
])
def FooSLQModelClassParametrized(request):
    """Фикстура для параметризации тестов с различными SQLModel классами."""
    return request.param


@pytest.fixture(params=[
    _FooPydanticModel,
    _FooSQLModelBase,
    _FooSQLModelTable,
])
def FooModelParametrized(request):
    """Фикстура для параметризации тестов с различными моделями."""
    return request.param


@pytest.fixture
def create_data() -> dict:
    return {
        "name": "Test Name",
        "password": "TestPassword",
        "email": "test@example.com"
    }


@pytest.fixture
def update_data() -> dict:
    return {
        "name": "Updated Name",
        "password": "UpdatedPassword",
    }


@pytest.fixture
def read_data(create_data) -> dict:
    return {
        "id": 1,
        **create_data,
    }
