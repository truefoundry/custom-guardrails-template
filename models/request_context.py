from typing import Optional
from models.user import Subject
from models.metadata import Metadata
from pydantic import BaseModel

class RequestContext(dict):
    """
    RequestContext is a dictionary-like class for storing arbitrary request context.

    This class exists for type clarity and future extensibility.

    Attributes:
        user (Optional[Subject]): The user associated with the request context.
        metadata (Optional[Metadata]): Arbitrary metadata for the request context.
    """

    @property
    def user(self) -> Subject:
        return self.get("user")
    
    @property
    def metadata(self) -> Optional[Metadata]:
        return self.get("metadata")

    @metadata.setter
    def metadata(self, value: Metadata) -> None:
        self["metadata"] = value

    def __get_pydantic_core_schema__(self, handler):
        # Define a custom schema for RequestContext
        return handler.generate_schema(dict)
