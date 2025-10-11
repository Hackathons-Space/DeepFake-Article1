from pydantic import BaseModel

class TextItem(BaseModel):
    text: str

class URLItem(BaseModel):
    url: str

class ClaimItem(BaseModel):
    claim: str
