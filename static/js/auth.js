// Authentication related JavaScript

// Password visibility toggle
function togglePasswordVisibility(inputId, iconId) {
    const passwordInput = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Password strength meter
function checkPasswordStrength(password) {
    // Initialize variables
    let strength = 0;
    const meter = document.getElementById('passwordStrengthMeter');
    const text = document.getElementById('passwordStrengthText');
    
    if (!meter || !text) return; // Exit if elements don't exist
    
    // Check password length
    if (password.length >= 8) strength += 25;
    
    // Check for mixed case
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength += 25;
    
    // Check for numbers
    if (password.match(/\d/)) strength += 25;
    
    // Check for special characters
    if (password.match(/[^a-zA-Z\d]/)) strength += 25;
    
    // Update the strength meter
    meter.style.width = strength + '%';
    
    // Change color based on strength
    if (strength < 25) {
        meter.className = 'password-strength bg-danger';
        text.textContent = 'Very Weak';
        text.className = 'text-danger';
    } else if (strength < 50) {
        meter.className = 'password-strength bg-warning';
        text.textContent = 'Weak';
        text.className = 'text-warning';
    } else if (strength < 75) {
        meter.className = 'password-strength bg-info';
        text.textContent = 'Moderate';
        text.className = 'text-info';
    } else {
        meter.className = 'password-strength bg-success';
        text.textContent = 'Strong';
        text.className = 'text-success';
    }
}

// Check password and confirmation match
function checkPasswordMatch() {
    const password = document.getElementById('password');
    const confirm = document.getElementById('confirmPassword');
    const message = document.getElementById('passwordMatchMessage');
    
    if (!password || !confirm || !message) return;
    
    if (password.value === confirm.value) {
        message.textContent = 'Passwords match';
        message.className = 'text-success small';
    } else {
        message.textContent = 'Passwords do not match';
        message.className = 'text-danger small';
    }
}

// Setup event listeners when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Password strength checker
    const passwordInput = document.getElementById('password') || document.getElementById('newPassword');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            checkPasswordStrength(this.value);
        });
    }
    
    // Password matching checker
    const confirmInput = document.getElementById('confirmPassword');
    if (confirmInput) {
        confirmInput.addEventListener('input', checkPasswordMatch);
        if (passwordInput) {
            passwordInput.addEventListener('input', checkPasswordMatch);
        }
    }
});
