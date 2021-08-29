from pydantic import BaseModel

class StreamCreate(BaseModel):
    publicAddress: str
    solvesToken: int
    interval: str

    class Config:
        orm_mode = True