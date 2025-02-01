from pydantic import BaseModel


class PaymentData(BaseModel):
    email: str
    amount: int