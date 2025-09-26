from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class TuitionPayment(BaseModel):
    student_id: int
    username: str

class OTPVerification(BaseModel):
    username: str
    student_id: int
    otp: str