"""
Base class for serializable components.
"""

import json
from dataclasses import Field, dataclass, field
from enum import Enum
from functools import wraps
from typing import (Any, Callable, Dict, List, Optional, Type, TypeVar, Union,
                    get_type_hints)

T = TypeVar("T", bound="SerializableComponent")


class ValidatedField:
    """Field with validation."""

    def __init__(
        self,
        validator: Callable[[Any], bool],
        error_message: str = None,
        default: Any = None,
    ):
        self.validator = validator
        self.error_message = error_message
        self.default = default

    def __call__(self, value: Any) -> bool:
        return self.validator(value)

    def __get__(self, obj, objtype=None):
        """Get the field value."""
        if obj is None:
            return self
        return obj.__dict__.get(self.name, self.default)

    def __set__(self, obj, value):
        """Set and validate the field value."""
        if not self.validator(value):
            error_message = self.error_message or f"Validation failed for {self.name}"
            raise ValueError(error_message)
        obj.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        """Store the field name."""
        self.name = name

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.default

    def from_dict(self, data: Any) -> Any:
        """Create from dictionary after deserialization."""
        if not self.validator(data):
            error_message = (
                self.error_message or f"Validation failed during deserialization"
            )
            raise ValueError(error_message)
        return data


def validate_field(
    validator: Callable[[Any], bool], error_message: str = None, default: Any = None
) -> ValidatedField:
    """
    Create a validated field.

    Args:
        validator: Function that takes a value and returns True if valid
        error_message: Optional custom error message
        default: Default value for the field
    """
    return ValidatedField(validator, error_message, default)


def range_validator(
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    default: Any = None,
) -> ValidatedField:
    """
    Create a validator for numeric range.

    Args:
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        default: Default value for the field
    """

    def validator(value: Any) -> bool:
        if not isinstance(value, (int, float)):
            return False
        if min_value is not None and value < min_value:
            return False
        if max_value is not None and value > max_value:
            return False
        return True

    return validate_field(
        validator, f"Value must be between {min_value} and {max_value}", default
    )


def length_validator(
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    default: Any = None,
) -> ValidatedField:
    """
    Create a validator for string/list/dict length.

    Args:
        min_length: Minimum allowed length (inclusive)
        max_length: Maximum allowed length (inclusive)
        default: Default value for the field
    """

    def validator(value: Any) -> bool:
        if not hasattr(value, "__len__"):
            return False
        length = len(value)
        if min_length is not None and length < min_length:
            return False
        if max_length is not None and length > max_length:
            return False
        return True

    return validate_field(
        validator, f"Length must be between {min_length} and {max_length}", default
    )


def custom_validator(
    validator: Callable[[Any], bool], error_message: str, default: Any = None
) -> ValidatedField:
    """
    Create a custom validator.

    Args:
        validator: Function that takes a value and returns True if valid
        error_message: Error message to display if validation fails
        default: Default value for the field
    """
    return validate_field(validator, error_message, default)


@dataclass
class SerializableComponent:
    """Base class for components that can be serialized."""

    def __post_init__(self):
        """Validate fields after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate component data.
        Raises ValueError if validation fails.
        """
        for name, value in self.__dict__.items():
            field_def = self.__class__.__dict__.get(name)
            if isinstance(field_def, ValidatedField):
                if not field_def(value):
                    error_message = (
                        field_def.error_message or f"Validation failed for {name}"
                    )
                    raise ValueError(error_message)

            # Validate nested SerializableComponent
            if isinstance(value, SerializableComponent):
                value.validate()

            # Validate lists
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, SerializableComponent):
                        item.validate()

            # Validate dictionaries
            if isinstance(value, dict):
                for v in value.values():
                    if isinstance(v, SerializableComponent):
                        v.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary for serialization."""
        data = {}

        for name, value in self.__dict__.items():
            field_def = self.__class__.__dict__.get(name)

            # Handle ValidatedField
            if isinstance(field_def, ValidatedField):
                data[name] = value
                continue

            # Handle None values
            if value is None:
                data[name] = None
                continue

            # Handle Enum values
            if isinstance(value, Enum):
                data[name] = {
                    "__enum__": value.__class__.__name__,
                    "name": value.name,
                    "value": value.value,
                }
                continue

            # Handle nested SerializableComponent
            if isinstance(value, SerializableComponent):
                data[name] = value.to_dict()
                continue

            # Handle lists of SerializableComponent
            if isinstance(value, list):
                data[name] = [
                    item.to_dict() if isinstance(item, SerializableComponent) else item
                    for item in value
                ]
                continue

            # Handle dictionaries
            if isinstance(value, dict):
                data[name] = {
                    str(k): v.to_dict() if isinstance(v, SerializableComponent) else v
                    for k, v in value.items()
                }
                continue

            # Handle basic types
            data[name] = value

        return {
            "__type__": self.__class__.__name__,
            "__module__": self.__class__.__module__,
            "data": data,
        }

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create component from dictionary after deserialization."""
        if isinstance(data, cls):
            return data

        if not isinstance(data, dict):
            raise ValueError(f"Invalid data format for {cls.__name__}: {data}")

        component_data = data.get("data", data)
        if not isinstance(component_data, dict):
            raise ValueError(f"Invalid component data format: {component_data}")

        # Get field definitions
        field_defs = {
            name: value
            for name, value in cls.__dict__.items()
            if isinstance(value, ValidatedField)
        }

        converted_data = {}
        for name, value in component_data.items():
            field_def = field_defs.get(name)

            # Handle None values
            if value is None:
                converted_data[name] = None
                continue

            # Handle ValidatedField
            if field_def is not None:
                converted_data[name] = field_def.from_dict(value)
                continue

            # Handle Enum values
            if isinstance(value, dict) and "__enum__" in value:
                enum_class = globals().get(value["__enum__"])
                if enum_class and issubclass(enum_class, Enum):
                    converted_data[name] = enum_class[value["name"]]
                continue

            # Handle nested SerializableComponent
            if isinstance(value, dict) and "__type__" in value:
                component_class = globals().get(value["__type__"])
                if component_class and issubclass(
                    component_class, SerializableComponent
                ):
                    converted_data[name] = component_class.from_dict(value)
                continue

            # Handle lists
            if isinstance(value, list):
                converted_data[name] = [
                    item.from_dict()
                    if isinstance(item, dict) and "__type__" in item
                    else item
                    for item in value
                ]
                continue

            # Handle dictionaries
            if isinstance(value, dict):
                converted_data[name] = {
                    k: v.from_dict() if isinstance(v, dict) and "__type__" in v else v
                    for k, v in value.items()
                }
                continue

            # Handle basic types
            converted_data[name] = value

        return cls(**converted_data)

    def clone(self: T) -> T:
        """Create a deep copy of the component."""
        return self.__class__.from_dict(self.to_dict())

    def merge(self: T, other: T) -> None:
        """Merge another component's data into this one."""
        if not isinstance(other, self.__class__):
            raise TypeError(f"Cannot merge {type(other)} into {type(self)}")

        other_dict = other.to_dict()["data"]
        for key, value in other_dict.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)
