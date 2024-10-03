from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# class DocumentUpload(BaseModel):
#     filename: str
#     file_type: str

# class DocumentResponse(BaseModel):
#     id: int
#     filename: str
#     file_type: str
#     s3_url: str
#     parsed_content: Optional[str]




# Base schema for User
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True

# Base schema for Document
class DocumentBase(BaseModel):
    filename: str
    file_type: str
    s3_url: str
    parsed_content: str

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    owner: Optional[str] = None  # Optional field with default None
    upload_timestamp: Optional[datetime] = None  # Optional field with default None

    class Config:
        orm_mode = True

# Base schema for Query
class QueryBase(BaseModel):
    query_text: str

class QueryCreate(QueryBase):
    pass

class QueryResponse(QueryBase):
    id: int
    result: str
    query_timestamp: datetime
    user: UserResponse

    class Config:
        orm_mode = True

     