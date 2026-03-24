"""Two-level metadata schema definitions shared across services."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MetadataSchemaType(str, Enum):
    """Supported original-metadata schema types."""

    DUBLIN_CORE = "dublin_core"
    DATACITE = "datacite"
    OPENAIRE4 = "openaire4"
    JATS = "jats"
    OTHER = "other"


class AlternateIdentifierL1(BaseModel):
    """Alternate identifier inside Level-1 metadata."""

    schema_: str = Field(..., alias="schema", description="Identifier schema")
    value: str = Field(..., description="Identifier value")

    model_config = {"populate_by_name": True}


class OriginalMetadataRef(BaseModel):
    """Reference to the original Level-2 metadata."""

    schema_: str = Field(..., alias="schema", description="Original metadata schema")
    cid: Optional[str] = Field(None, description="Internal CID for the original metadata")

    model_config = {"populate_by_name": True}


LEVEL1_SCHEMA_URI = "https://dark.la-referencia.info/schemas/ark-metadata/v1"
LEVEL1_SCHEMA_VERSION = "1.0"


class Level1Metadata(BaseModel):
    """Minimal public metadata persisted as the Level-1 record."""

    schema_uri: str = Field(default=LEVEL1_SCHEMA_URI, alias="$schema")
    schema_version: str = Field(default=LEVEL1_SCHEMA_VERSION)
    ark: Optional[str] = Field(None, description="Full ARK identifier")

    title: str = Field(..., description="Resource title")
    authors: list[str] = Field(..., min_length=1, description="List of author names")
    year: int = Field(..., description="Publication year")

    publisher: Optional[str] = Field(None)
    resource_type: Optional[str] = Field(None)
    language: Optional[str] = Field(None)
    abstract: Optional[str] = Field(None)
    subjects: Optional[list[str]] = Field(None)
    rights: Optional[str] = Field(None)
    alternate_identifiers: Optional[list[AlternateIdentifierL1]] = Field(None)
    alternate_urls: Optional[list[str]] = Field(None)
    original_metadata: OriginalMetadataRef = Field(...)
    created_at: Optional[datetime] = Field(None)
    updated_at: Optional[datetime] = Field(None)

    model_config = {"populate_by_name": True}
