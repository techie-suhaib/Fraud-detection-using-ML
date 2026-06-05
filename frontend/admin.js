document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const btn = document.getElementById('loginBtn');
    const errorMsg = document.getElementById('errorMessage');

    // UI Loading State
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
    btn.disabled = true;
    errorMsg.style.display = 'none';

    try {
        const response = await fetch('/api/admin/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const res = await response.json();

        if (!response.ok) {
            throw new Error(res.error || "Login failed");
        }

        // Success: Store simple session details and redirect
        localStorage.setItem("isLoggedIn", "true");
        localStorage.setItem("userRole", "admin");
        localStorage.setItem("userId", res.user_id);
        localStorage.setItem("userName", res.full_name);
        localStorage.setItem("userEmail", email);
        
        window.location.href = "index.html"; 

    } catch (err) {
        btn.innerHTML = 'Sign In';
        btn.disabled = false;
        errorMsg.innerText = err.message || "Invalid credentials. Please try again.";
        errorMsg.style.display = 'block';
    }
});