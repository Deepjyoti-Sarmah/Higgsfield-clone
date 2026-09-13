from pydantic import BaseModel


class CreditsResponse(BaseModel):
    balance: int
