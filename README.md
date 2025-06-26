# Pystructor

![Python Support](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Pydantic Version](https://img.shields.io/badge/pydantic-v2-orange.svg)
![SQLModel Version](https://img.shields.io/badge/sqlmodel-0.0.24+-purple.svg)

Pystructor is a Python library inspired by TypeScript, featuring handy decorators for transforming Pydantic models and SQLModel entities, along with automatic CRUD schema generation. It aims to simplify data model manipulation and reduce boilerplate code in your Python applications.

## Features

*   **TypeScript-inspired Decorators**: Easily transform Pydantic/SQLModel classes.
    *   `@partial(Model)`: Makes all fields in `Model` optional.
    *   `@omit(Model, 'field1', 'field2')`: Excludes specified fields from `Model`.
    *   `@pick(Model, 'field1', 'field2')`: Selects only specified fields from `Model`.
*   **Automatic CRUD Schema Generation**: Quickly generate `Create`, `Read`, and `Update` Pydantic schemas from your SQLModel table definitions using `generate_crud_schemas`.
*   **Type Safety**: Leverages Pydantic's robust type checking.
*   **Extensible**: Customize generated schemas by including or excluding specific fields.

## Requirements

*   Python 3.8+
*   Pydantic >=2.0.0, <3.0.0
*   SQLModel >=0.0.24
*   SQLAlchemy >=2.0, <3.0

## Installation

You can install Pystructor directly from its Git repository:

```bash
pip install git+https://github.com/preposition17/pystructor.git
```

If you want to install a specific branch, tag, or commit:
```bash
# Install from 'main' branch
pip install git+https://github.com/preposition17/pystructor.git@main

# Install version 'v0.1.0' (if tagged)
pip install git+https://github.com/preposition17/pystructor.git@v0.1.0
```

## Usage

### Decorators for Model Transformation

Pystructor provides decorators to easily create variations of your Pydantic models or SQLModel entities.

```python
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import SQLModel, Field as SQLModelField
from pystructor import partial, omit, pick
from datetime import datetime

# Define a base model (can be Pydantic BaseModel or SQLModel)
class UserBase(SQLModel):
    id: int | None = SQLModelField(default=None, primary_key=True)
    username: str
    email: str
    full_name: str | None = None
    hashed_password: str

# 1. @partial - Make all fields optional
@partial(UserBase)
class UserUpdate(SQLModel):
    # All fields from UserBase are now optional (id, username, email, full_name, hashed_password)
    # You can add new fields or override existing ones if needed
    updated_at: datetime = PydanticField(default_factory=datetime.utcnow)

# Example:
user_update_instance = UserUpdate(username="new_username") # email, full_name, etc. are optional
print(UserUpdate.model_fields["email"].is_required()) # Output: False
print(UserUpdate.model_fields["updated_at"].is_required()) # Output: True (unless default is provided)


# 2. @omit - Exclude specified fields
@omit(UserBase, "hashed_password", "id")
class UserCreate(SQLModel):
    # "hashed_password" and "id" are excluded from UserBase
    # New fields specific to creation can be added
    password_confirmation: str = PydanticField(...)

# Example:
user_create_instance = UserCreate(
    username="testuser",
    email="test@example.com",
    password_confirmation="securepassword123"
)
assert "hashed_password" not in UserCreate.model_fields
assert "id" not in UserCreate.model_fields
assert "password_confirmation" in UserCreate.model_fields


# 3. @pick - Select only specified fields
@pick(UserBase, "id", "username", "email", "full_name")
class UserPublic(SQLModel):
    # Only "id", "username", "email", "full_name" are included from UserBase
    # "hashed_password" is excluded
    # You can add other public-specific fields
    profile_views: int = 0

# Example:
user_public_instance = UserPublic(id=1, username="testuser", email="test@example.com")
assert "hashed_password" not in UserPublic.model_fields
assert "username" in UserPublic.model_fields
assert "profile_views" in UserPublic.model_fields
```

### Automatic CRUD Schema Generation

Generate `Create`, `Read`, and `Update` Pydantic schemas for your SQLModel tables with a single function call.

```python
from sqlmodel import SQLModel, Field
from pystructor import generate_crud_schemas, IncludeFieldsType
from typing import Annotated, List

# 1. Define your SQLModel table
class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="Item name")
    description: str | None = Field(default=None)
    price: float
    secret_token: str # A field we might want to exclude from reads
    owner_id: int | None = Field(default=None) # foreign_key="user.id" (assuming User model)

# 2. Generate CRUD schemas
# By default:
# - CreateSchema: Excludes 'id'.
# - ReadSchema: Excludes fields named 'password'. Other fields are included.
# - UpdateSchema: Makes all fields optional.

ItemCreate, ItemRead, ItemUpdate = generate_crud_schemas(Item)

# Example:
new_item_data = ItemCreate(name="Awesome Gadget", price=99.99, secret_token="supersecret")
item_from_db = ItemRead(id=1, name="Awesome Gadget", price=99.99, secret_token="supersecret", owner_id=1)
update_for_item = ItemUpdate(price=89.99) # Only update price, other fields are optional

# 3. Customizing generated schemas
# You can include additional fields or exclude more fields.

# Example: Exclude 'secret_token' from ItemRead and 'owner_id' from ItemCreate
# Also, add a computed field to ItemRead.
# (Note: For related models, you'd typically use Pydantic's nested models or SQLModel's Relationship features,
# then customize the Read schema if needed. `include_to_read` is for adding/modifying fields at the schema level.)

include_extra_to_read: IncludeFieldsType = {
    "is_expensive": (bool, Field(default=False)) # Example additional field
    # For a truly computed field based on other model fields, you might use @computed_field from Pydantic
    # or pass a validator/method if Pystructor supports it for callables.
    # The current `IncludeFieldsType` supports type and FieldInfo.
}

CustomItemCreate, CustomItemRead, CustomItemUpdate = generate_crud_schemas(
    Item,
    exclude_from_create=["owner_id"],
    exclude_from_read=["secret_token"],
    include_to_read=include_extra_to_read
)

# Now:
# - CustomItemCreate will not have 'owner_id'.
# - CustomItemRead will not have 'secret_token' but will have 'is_expensive'.
# - CustomItemUpdate will have all original fields as optional.

# Example usage of custom schemas:
# custom_create_data = CustomItemCreate(name="My Item", price=10.0, secret_token="abc")
# custom_read_data = CustomItemRead(id=1, name="My Item", price=10.0, owner_id=1, is_expensive=False)
# print(hasattr(custom_read_data, "secret_token")) # False
# print(hasattr(custom_read_data, "is_expensive")) # True
```

## Planned Features / Future Work

Pystructor is actively developing. Here are some features planned for future releases:

*   `@required(Model)`: Make all fields in `Model` required.
*   `@readonly(Model)`: Make model fields immutable (similar to Pydantic's `frozen=True`).
*   `@non_nullable(Model)`: Remove `Optional` / `None` from field types.
*   `@deep_partial(Model)`: Recursively apply `partial` to nested models.
*   `@exclude_type(Model, TypeToExclude)`: Exclude a specific type from Union types in fields.
*   `@merge(ModelA, ModelB)`: Merge fields from two models.
*   `@as_form(Model)`: Utility to easily convert Pydantic models to FastAPI Form dependencies.
*   Enhanced customization for `generate_crud_schemas`, including support for callables/computed fields more directly.

## Contributing

Contributions are welcome! If you have suggestions, bug reports, or want to contribute code, please feel free to:

1.  Open an issue on the project's Git repository.
2.  Fork the repository and submit a pull request.

Please ensure your code follows the existing style and includes tests for new features or bug fixes.

## License

Pystructor is licensed under the [MIT License](LICENSE). (Note: You'll need to add a LICENSE file to your repository, or remove this link if not applicable).

## Project Links

*   Homepage / Repository: [https://github.com/preposition17/pystructor](https://github.com/preposition17/pystructor)