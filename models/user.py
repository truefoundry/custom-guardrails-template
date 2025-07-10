from enum import Enum
from typing import Optional
from pydantic import BaseModel

class SubjectType(str, Enum):
    user = 'user'
    team = 'team'
    serviceaccount = 'serviceaccount'

class Subject(BaseModel):
    subjectId: str
    subjectType: SubjectType
    subjectSlug: Optional[str] = None
    subjectDisplayName: Optional[str] = None