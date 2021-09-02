from pydantic import BaseModel
from datetime import datetime

class StreamCreate(BaseModel):
    publicAddress: str
    solvestToken: int
    interval: int
    totalAmount: float
    startTime: datetime
    endTime: datetime
    investPda: str

    class Config:
        orm_mode = True


class SaveTransaction(BaseModel):
    publicKey: str
    tokenId: int
    transactionId: str
    side: str
    quantity: float
    source: str
    destination: str

    class Config:
        orm_mode = True