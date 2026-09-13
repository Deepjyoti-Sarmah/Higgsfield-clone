from pydantic import BaseModel


class CreditsResponse(BaseModel):
    balance: int


class TopUpResponse(BaseModel):
    amount: int
    balance: int
