from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import LoginRequest, TuitionPayment, OTPVerification
from database import supabase
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import threading
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Giả lập bộ nhớ tạm cho OTP
otp_storage = {}

# Cấu hình email
EMAIL_ADDRESS = "cuongnguyen32179@gmail.com"
EMAIL_PASSWORD = "cpvbtprovrgqklkg"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_otp_email(email: str, otp: str):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg['Subject'] = "Your OTP for Tuition Payment"
    
    body = f"Your OTP is {otp}. It is valid for 60 seconds."
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {e}")
    
# Hàm dọn dẹp OTP hết hạn
def cleanup_expired_otps():
    while True:
        current_time = time.time()
        expired_keys = [key for key, value in otp_storage.items() if value["expires_at"] < current_time]
        for key in expired_keys:
            del otp_storage[key]
        time.sleep(10)  # Kiểm tra mỗi 10 giây

# Khởi chạy thread dọn dẹp khi ứng dụng khởi động
threading.Thread(target=cleanup_expired_otps, daemon=True).start()

@app.get("/customers")
async def get_customers(limit: int = 100, offset: int = 0):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database client initialization failed")
    
    try:
        response = supabase.table("customer").select("*").range(offset, offset + limit - 1).execute()
        customers = response.data
        return [
            {
                "customer_id": customer["customer_id"],
                "username": customer["username"],
                "password": customer["password"],
                "email": customer["email"],
                "available_balance": customer["available_balance"]
            }
            for customer in customers
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

@app.get("/customers/{customer_id}")
async def get_customer(customer_id: int):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database client initialization failed")
    
    try:
        response = supabase.table("customer").select("*").eq("customer_id", customer_id).execute()
        customer = response.data
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {
            "customer_id": customer[0]["customer_id"],
            "username": customer[0]["username"],
            "password": customer[0]["password"],
            "email": customer[0]["email"],
            "available_balance": customer[0]["available_balance"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

@app.post("/login")
async def login(login_data: LoginRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database client initialization failed")
    
    try:
        response = supabase.table("customer").select("*").eq("username", login_data.username).eq("password", login_data.password).execute()
        customer = response.data
        if not customer:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        return {
            "username": customer[0]["username"],
            "full_name": customer[0]["full_name"],
            "available_balance": customer[0]["available_balance"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")
    
@app.get("/student_id/{student_id}")
async def get_student_id(student_id: int):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database client initialization failed")
    
    try:
        response = supabase.table("tuition").select("*").eq("student_id", student_id).execute()
        tuition = response.data
        if not tuition:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        return {
            "name_student": tuition[0]["name_student"],
            "amount": tuition[0]["amount"],
            "is_paid": tuition[0]["is_paid"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")

@app.post("/pay_tuition/request_otp")
async def request_otp(tuition_payment: TuitionPayment):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database client initialization failed")
    
    try:
        # Fetch tuition details
        tuition_response = supabase.table("tuition").select("*").eq("student_id", tuition_payment.student_id).execute()
        tuition = tuition_response.data
        if not tuition:
            raise HTTPException(status_code=404, detail="Tuition record not found")
        
        tuition_record = tuition[0]
        if tuition_record["is_paid"]:
            raise HTTPException(status_code=400, detail="Tuition already paid")
        
        amount_due = tuition_record["amount"]
        
        # Fetch customer details
        customer_response = supabase.table("customer").select("*").eq("username", tuition_payment.username).execute()
        customer = customer_response.data
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_record = customer[0]
        if customer_record["available_balance"] < amount_due:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Generate unique OTP with only numbers (6 digits)
        otp = generate_unique_otp()
        otp_storage[f"{tuition_payment.username}_{tuition_payment.student_id}"] = {
            "otp": otp,
            "expires_at": time.time() + 60  # OTP expires in 60 seconds
        }
        
        # Send OTP to customer email
        send_otp_email(customer_record["email"], otp)
        
        return {
            "message": "OTP sent to your email. Please verify within 60 seconds.",
            "expires_at": otp_storage[f"{tuition_payment.username}_{tuition_payment.student_id}"]["expires_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OTP generation failed: {e}")

def generate_unique_otp():
    max_attempts = 100  # Giới hạn số lần thử để tránh vòng lặp vô hạn
    attempts = 0
    while attempts < max_attempts:
        otp = str(random.randint(0, 999999)).zfill(6)
        if otp not in [value["otp"] for value in otp_storage.values()]:
            return otp
        attempts += 1
    raise Exception("Unable to generate unique OTP after multiple attempts")

@app.post("/pay_tuition/verify_otp")
async def verify_otp(otp_verification: OTPVerification):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database client initialization failed")
    
    try:
        # Check OTP
        key = f"{otp_verification.username}_{otp_verification.student_id}"
        if key not in otp_storage:
            raise HTTPException(status_code=400, detail="OTP not found or expired")
        
        stored_otp = otp_storage[key]
        if time.time() > stored_otp["expires_at"]:
            del otp_storage[key]
            raise HTTPException(status_code=400, detail="OTP expired")
        
        if stored_otp["otp"] != otp_verification.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # Fetch tuition details
        tuition_response = supabase.table("tuition").select("*").eq("student_id", otp_verification.student_id).execute()
        tuition = tuition_response.data
        if not tuition:
            raise HTTPException(status_code=404, detail="Tuition record not found")
        
        tuition_record = tuition[0]
        if tuition_record["is_paid"]:
            raise HTTPException(status_code=400, detail="Tuition already paid")
        
        amount_due = tuition_record["amount"]
        
        # Fetch customer details
        customer_response = supabase.table("customer").select("*").eq("username", otp_verification.username).execute()
        customer = customer_response.data
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_record = customer[0]
        if customer_record["available_balance"] < amount_due:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Deduct amount from customer's balance
        new_balance = customer_record["available_balance"] - amount_due
        supabase.table("customer").update({"available_balance": new_balance}).eq("username", otp_verification.username).execute()
        supabase.table("payment_date").insert(
            {
                "tuition_fee_id": tuition_record["tuition_fee_id"], 
                "customer_id": customer_record["customer_id"]
            }
        ).execute()

        # Mark tuition as paid
        supabase.table("tuition").update({"is_paid": True}).eq("student_id", otp_verification.student_id).execute()
        
        # Clean up OTP
        del otp_storage[key]
        
        return {"message": "Tuition payment successful", "new_balance": new_balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment failed: {e}")
    
@app.post("/pay_tuition/cancel_otp")
async def cancel_otp(tuition_payment: TuitionPayment):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database client initialization failed")
    
    try:
        key = f"{tuition_payment.username}_{tuition_payment.student_id}"
        if key in otp_storage:
            del otp_storage[key]
            return {"message": "OTP canceled successfully"}
        raise HTTPException(status_code=404, detail="No active OTP found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel OTP: {e}")