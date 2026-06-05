// DOM Elements
const fullNameInput = document.querySelector('.settings-form .form-group:nth-child(1) input');
const emailInput = document.querySelector('.settings-form .form-group:nth-child(2) input');

// Tab Switching Logic
function showTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from menu items
    document.querySelectorAll('.settings-nav li').forEach(li => {
        li.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabId).classList.add('active');
    
    // Highlight menu item
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }
}

// Toggle API Key Visibility
function toggleKey() {
    const keyInput = document.getElementById('apiKey');
    const icon = event.target;
    
    if (keyInput.type === "password") {
        keyInput.type = "text";
        icon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        keyInput.type = "password";
        icon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

// Notification Simulation & Profile Update
function notifySave() {
    const btn = event.target;
    const originalText = btn.innerText;
    
    btn.innerText = "Saving...";
    btn.style.opacity = "0.7";
    
    // Read values
    const newName = fullNameInput.value.trim();
    const newEmail = emailInput.value.trim();
    
    if (newName) localStorage.setItem("userName", newName);
    if (newEmail) localStorage.setItem("userEmail", newEmail);
    
    setTimeout(() => {
        btn.innerText = "Settings Updated!";
        btn.style.backgroundColor = "#10b981"; // Success Green
        
        setTimeout(() => {
            btn.innerText = originalText;
            btn.style.backgroundColor = "#3b82f6"; // Reset Blue
            btn.style.opacity = "1";
        }, 2000);
    }, 1000);
}

// Load current user details on start
document.addEventListener('DOMContentLoaded', () => {
    const userName = localStorage.getItem("userName") || "Admin User";
    const userEmail = localStorage.getItem("userEmail") || "admin@fraudguard.ai";
    const userRole = localStorage.getItem("userRole") || "admin";
    
    if (fullNameInput) fullNameInput.value = userName;
    if (emailInput) emailInput.value = userEmail;
    
    // Customize header for customer vs admin
    const profileHeaderH3 = document.querySelector('#profile h3');
    if (profileHeaderH3) {
        profileHeaderH3.innerText = userRole === 'admin' ? 'Admin Profile' : 'Customer Profile';
    }
});