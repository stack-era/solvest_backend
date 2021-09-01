from pydantic import BaseModel

class StreamCreate(BaseModel):
    publicAddress: str
    solvesToken: int
    interval: str
    quantity: float

    class Config:
        orm_mode = True


class SaveTransaction(BaseModel):
    publicKey: str
    tokenId: int
    transactionId: str
    side: str
    quantity: float

    class Config:
        orm_mode = True