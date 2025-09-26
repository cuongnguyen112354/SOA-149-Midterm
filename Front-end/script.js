let endpoint = 'http://127.0.0.1:8000';
// let endpoint = 'https://soa-149-be.onrender.com';

document.getElementById('loginForm')?.addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        // Send login request to your endpoint
        const response = await fetch(`${endpoint}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Store customer data in localStorage
            const customerData = {
                username: result.username,
                full_name: result.full_name,
                available_balance: result.available_balance
            };
            localStorage.setItem('customerData', JSON.stringify(customerData));
            
            // Redirect to pay_tuition.html
            window.location.href = 'pay_tuition.html';
        } else {
            document.getElementById('error').style.display = 'block';
        }
    } catch (error) {
        console.error('Login error:', error);
        document.getElementById('error').style.display = 'block';
    }
});

// Load customer data on pay_tuition.html
window.onload = function() {
    if (window.location.pathname.includes('pay_tuition.html')) {
        const customerData = JSON.parse(localStorage.getItem('customerData'));
        if (customerData) {
            document.getElementById('customerName').textContent = customerData.full_name;
            document.getElementById('customerBalance').textContent = customerData.available_balance;
        } else {
            // Redirect to login if no customer data
            window.location.href = 'index.html';
        }
    }
};

document.getElementById('studentSearchForm')?.addEventListener('submit', async function(event) {
    event.preventDefault();

    const studentId = document.getElementById('studentId').value;
    
    try {
        // API call to search student
        const response = await fetch(`${endpoint}/student_id/${studentId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        if (response.ok) {
            // Display tuition data
            const tuitionInfo = document.getElementById('tuitionInfo');
            document.getElementById('studentName').textContent = result.name_student;
            document.getElementById('tuitionAmount').textContent = result.amount;
            document.getElementById('isPaid').textContent = result.is_paid ? 'Yes' : 'No';
            tuitionInfo.style.display = 'block';
        } else {
            alert('Student not found');
            document.getElementById('tuitionInfo').style.display = 'none';
        }
    } catch (error) {
        console.error('Search error:', error);
        alert('Error searching for student');
        document.getElementById('tuitionInfo').style.display = 'none';
    }
});

let otpTimerInterval = null; // Biến toàn cục để lưu interval

async function requestOTP() {
    const student_id = document.getElementById('studentId').value;
    const customerData = JSON.parse(localStorage.getItem('customerData'));
    
    try {
        // Dừng timer cũ nếu có
        if (otpTimerInterval) {
            clearInterval(otpTimerInterval);
            document.getElementById('otpTimer').textContent = '0';
        }

        const response = await fetch(`${endpoint}/pay_tuition/request_otp`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({student_id: parseInt(student_id), username: customerData.username})
        });
        const result = await response.json();
        if (response.ok) {
            alert(result.message);
            document.getElementById('otpPopup').style.display = 'flex';
            const expiresAt = result.expires_at * 1000;
            startOTPTimer(expiresAt);
        } else {
            alert('Failed to request OTP: ' + result.detail);
        }
    } catch (error) {
        console.error('OTP request error:', error);
        alert('Error requesting OTP');
    }
}

function startOTPTimer(expiresAt) {
    const timerElement = document.getElementById('otpTimer');
    // Dừng timer cũ nếu có
    if (otpTimerInterval) {
        clearInterval(otpTimerInterval);
    }

    otpTimerInterval = setInterval(() => {
        const now = new Date().getTime();
        const timeLeft = Math.max(0, Math.floor((expiresAt - now) / 1000));
        if (timeLeft <= 0) {
            clearInterval(otpTimerInterval);
            otpTimerInterval = null;
            timerElement.textContent = '0';
            closeOTPPopup();
            alert('OTP has expired. Please request a new one.');
            cancelOTP(); // Xóa OTP trên BE khi hết hạn
        } else {
            timerElement.textContent = timeLeft;
        }
    }, 1000);
}

async function verifyOTP(event) {
    event.preventDefault();
    const student_id = document.getElementById('studentId').value;
    const otp = document.getElementById('otpInput').value;
    const customerData = JSON.parse(localStorage.getItem('customerData'));
    
    try {
        const response = await fetch(`${endpoint}/pay_tuition/verify_otp`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({student_id: parseInt(student_id), username: customerData.username, otp: otp})
        });
        const result = await response.json();
        if (response.ok) {
            alert(result.message);
            customerData.available_balance = result.new_balance;
            localStorage.setItem('customerData', JSON.stringify(customerData));
            document.getElementById('customerBalance').textContent = customerData.available_balance;
            document.getElementById('isPaid').textContent = 'Yes';
            closeOTPPopup();
        } else {
            alert('Verification failed: ' + result.detail);
        }
    } catch (error) {
        console.error('Verification error:', error);
        alert('Error verifying OTP');
    }
}

function closeOTPPopup() {
    document.getElementById('otpPopup').style.display = 'none';
    document.getElementById('otpInput').value = '';
    if (otpTimerInterval) {
        clearInterval(otpTimerInterval);
        otpTimerInterval = null;
    }
    cancelOTP(); // Xóa OTP trên BE khi nhấn Cancel
}

async function cancelOTP() {
    const student_id = document.getElementById('studentId').value;
    const customerData = JSON.parse(localStorage.getItem('customerData'));
    try {
        const response = await fetch(`${endpoint}/pay_tuition/cancel_otp`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({student_id: parseInt(student_id), username: customerData.username})
        });
        if (response.ok) {
            console.log('OTP canceled on server');
        }
    } catch (error) {
        console.error('Cancel OTP error:', error);
    }
}

document.getElementById('otpForm')?.addEventListener('submit', verifyOTP);