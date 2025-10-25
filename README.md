
# 🏦 CS504070 Midterm Project: iBanking Tuition Payment System

This is the **midterm project** for the `CS504070 - Service-Oriented Architecture` course.
The goal is to build a complete **tuition payment module** that simulates an **iBanking** application, including:

✅ Backend API (FastAPI)
✅ Web-based Frontend
✅ PostgreSQL Database
✅ OTP Email Verification

---

## ✨ Features

### 🔐 User Authentication

* Customers log in using `username` and `password`.

### 📚 Tuition Lookup

* Allows authenticated users to search for any student's tuition using **Student ID (MSSV)**.

### 🧾 Two-Step OTP Payment Flow

**Step 1 — OTP Request**

* Verifies:

  * Customer `available_balance`
  * Tuition `is_paid` status

**Step 2 — OTP Verification**

* 6-digit OTP email delivery using `smtplib`
* 60-second expiration timer
* Backend verifies OTP correctness + expiry

### 💸 Transaction Processing

On success:

* Deduct payer balance
* Mark tuition `is_paid = true`
* Log transaction into database `payment_date`

### ⚔️ Concurrency Handling

* Prevents:

  * Double payment on the same tuition
  * Race conditions on balance deduction

### 🧹 Automatic OTP Cleanup

* Background thread removes expired OTPs from memory

---

## 🛠️ Tech Stack

| Component  | Technology              | Description                           |
| ---------- | ----------------------- | ------------------------------------- |
| Backend    | FastAPI (Python)        | Authentication, payment logic, OTP    |
| Database   | Supabase (PostgreSQL)   | `customer`, `tuition`, `payment_date` |
| Frontend   | HTML5, CSS3, JavaScript | Login & payment UI                    |
| Email      | smtplib (Python)        | Send OTP via Gmail SMTP               |
| Deployment | Uvicorn                 | ASGI server                           |

---

## 🧬 System Design

### 🗄️ Entity-Relationship Diagram (ERD)

> System uses **3 primary tables**:

**customer**

* Stores user account info

**tuition**

* Stores student tuition debt status

**payment_date**

* Logs successful transactions (relationship: *Make*)

---

## 📜 API Documentation (Swagger)

FastAPI automatically generates interactive documentation.

Once running:

```
http://127.0.0.1:8000/docs
```

---

## 🔌 API Endpoints

| Method | Endpoint                   | Function           | Input             | Output                                     |
| ------ | -------------------------- | ------------------ | ----------------- | ------------------------------------------ |
| POST   | `/login`                   | Authenticate user  | `LoginRequest`    | `{username, full_name, available_balance}` |
| GET    | `/student_id/{student_id}` | Get tuition info   | –                 | `{name_student, amount, is_paid}`          |
| POST   | `/pay_tuition/request_otp` | Request OTP        | `TuitionPayment`  | `{message, expires_at}`                    |
| POST   | `/pay_tuition/verify_otp`  | Verify OTP & pay   | `OTPVerification` | `{message, new_balance}`                   |
| POST   | `/pay_tuition/cancel_otp`  | Cancel pending OTP | `TuitionPayment`  | `{message}`                                |

---

## ⚙️ Installation & Setup

### ✅ Prerequisites

* Python `3.8+`
* Supabase account
* Gmail account (App Password for SMTP)

---

### 1️⃣ Backend Setup

Clone the repository:

```bash
git clone https://your-repo-url.git
cd your-project-folder
```

Create virtual environment:

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/Mac**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### 2️⃣ Environment Variables

Create a `.env` file:

```
SUPABASE_URL=https://your-supabase-url.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Email config
EMAIL_ADDRESS=your-gmail@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
```

---

### 3️⃣ Database (Supabase)

Go to Supabase dashboard:

* Open **SQL Editor**
* Run your `CREATE TABLE` scripts

  * `customer`
  * `tuition`
  * `payment_date`

Add sample rows to test.

---

### 4️⃣ Run the Backend

```bash
uvicorn main:app --reload
```

Backend is available at:

```
http://127.0.0.1:8000
```

Swagger Docs:

```
http://127.0.0.1:8000/docs
```

---

## 🖥️ Frontend Setup

Ensure the endpoint in `script.js` is correct:

```js
const endpoint = "http://127.0.0.1:8000";
```

Launch UI:

* Simply open `index.html` in any browser
* No frontend server required

---

## 🧯 Concurrency Handling

Backend handles:

* Race conditions during payment
* Checking balance **at verification time**, not request time
* Preventing multiple payments on the same tuition ID

---

## 📦 Project Folder Structure (suggested)

```
├── main.py
├── otp_handler.py
├── models.py
├── database.py
├── .env
├── requirements.txt
├── frontend/
│   ├── index.html
│   ├── payment.html
│   ├── style.css
│   └── script.js
└── README.md
```

---

## 📧 OTP Email Sample

```
Your OTP for tuition payment is: 482193
This code expires in 60 seconds.
Do NOT share this code with anyone.
```

---

## ✅ Summary

This project demonstrates:

* Service-Oriented Architecture principles
* REST API design
* Secure authentication
* In-memory OTP flow
* Email integration
* Transactional safety
* Race condition mitigation

---

## 🙌 Author

> *Feel free to add your name, class, student ID here.*

---

## ⭐ If you like this project…

Consider giving a ⭐ on GitHub!
