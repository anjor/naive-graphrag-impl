OBJECT_EXTRACTION_PROMPT = """Extract all entities from the following document. 
An entity should have a name, type (such as person, location etc) and a description.

Also identify relationships between the entities. 
For each relationship, provide the from entity, to entity, relationship label, and strength (0.0 to 1.0).

An Entity and a Relationship object should conform to the following pydantic definition:

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
"""

SUMMARY_PROMPT = """Summarise the following entities and relationships into a concise list of Objects.

Prioritise Quality of Quantity. Make sure to deduplicate entities and relationships.
Remember, Entity, Relationship and Object are pydantic models:

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
"""
