from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Entity(BaseModel):
    name: str = Field(..., title="name of the entity")
    type: str = Field(..., title="type of the entity")
    description: Optional[str] = Field(..., title="description of the entity")


class Relationship(BaseModel):
    from_entity: Entity = Field(..., title="starting entity for relationship")
    to_entity: Entity = Field(..., title="target entity for relationship")
    label: Optional[str] = Field(..., title="relationship label")
    strength: Optional[float] = Field(
        ..., title="strength of relationship", ge=0.0, le=1.0
    )


class ObjectType(Enum):
    ENTITY = "entity"
    RELATIONSHIP = "relationship"


class Object(BaseModel):
    type: ObjectType = Field(..., title="object type")
    object: Entity | Relationship = Field(..., title="object instance")


class Summary(BaseModel):
    summary: str = Field(..., title="summary of a community")
