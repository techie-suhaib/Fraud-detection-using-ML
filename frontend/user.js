document.getElementById('userLoginForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const email = document.getElementById('userEmail').value;
    const pass = document.getElementById('userPass').value;
    const btn = document.getElementById('loginBtn');
    const msg = document.getElementById('msg');

    // Loading State
    btn.innerText = "Signing in...";
    btn.disabled = true;
    msg.style.display = "none";

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: pass
            })
        });

        const res = await response.json();

        if (!response.ok) {
            throw new Error(res.error || "Login failed");
        }

        msg.style.color = "#10b981";
        msg.innerText = "Login Successful! Redirecting...";
        msg.style.display = "block";
        
        // Set sessions
        localStorage.setItem("isLoggedIn", "true");
        localStorage.setItem("userRole", res.role);
        localStorage.setItem("userId", res.user_id);
        localStorage.setItem("userName", res.full_name);
        localStorage.setItem("userEmail", email);
        localStorage.setItem("userBalance", res.balance);

        setTimeout(() => {
            window.location.href = "index.html"; 
        }, 1000);

    } catch (err) {
        msg.style.color = "#ef4444";
        msg.innerText = err.message || "Invalid email or password.";
        msg.style.display = "block";
        btn.innerText = "Sign In";
        btn.disabled = false;
    }
});

// Setup registration trigger on "Create an account" link click
document.querySelector('.signup-text a').addEventListener('click', async function(e) {
    e.preventDefault();
    
    const emailInput = document.getElementById('userEmail');
    const passInput = document.getElementById('userPass');
    
    const email = emailInput.value.trim();
    const pass = passInput.value.trim();
    
    if (!email || !pass) {
        alert("Please fill in Email Address and Password first, then click 'Create an account' to register.");
        return;
    }
    
    const fullName = prompt("Welcome to GuardPay! Enter your Full Name to sign up:");
    if (!fullName) return;
    
    const phone = prompt("Enter your Phone Number:");
    if (!phone) return;
    
    const btn = document.getElementById('loginBtn');
    const msg = document.getElementById('msg');
    
    btn.innerText = "Registering...";
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                full_name: fullName,
                email: email,
                phone: phone,
                password: pass
            })
        });
        
        const res = await response.json();
        if (!response.ok) {
            throw new Error(res.error || "Registration failed");
        }
        
        alert(`Account created successfully for ${fullName}! You can now Sign In using your password.`);
        msg.style.color = "#10b981";
        msg.innerText = "Registration complete! Click Sign In to log in.";
        msg.style.display = "block";
        
    } catch (err) {
        alert(err.message || "Failed to register. Please try again.");
    } finally {
        btn.innerText = "Sign In";
        btn.disabled = false;
    }
});