document.addEventListener('DOMContentLoaded', () => {
    // 1. Sidebar toggle logic
    const toggleBtns = document.querySelectorAll('.sidebarToggle, #sidebarToggle');
    const container = document.querySelector('.app-container');
    
    if (container) {
        // Restore collapsed state from localStorage
        if (localStorage.getItem('sidebar-collapsed') === 'true') {
            container.classList.add('sidebar-collapsed');
        }
        
        toggleBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                container.classList.toggle('sidebar-collapsed');
                const isCollapsed = container.classList.contains('sidebar-collapsed');
                localStorage.setItem('sidebar-collapsed', isCollapsed);
            });
        });
    }

    // 2. Login & User Session sidebar UI logic
    const isLoggedIn = localStorage.getItem("isLoggedIn");
    const loginLinks = document.getElementById('loginLinks');
    const userMenu   = document.getElementById('sidebarUserMenu');
    const sidebarLabel = document.getElementById('sidebarUserLabel');
    const userIcon = document.querySelector('#sidebarUserInfo i');

    if (isLoggedIn === "true") {
        const name = localStorage.getItem("userName") || "User";
        const role = localStorage.getItem("userRole") || "user";
        
        // Format role nicely (e.g. customer -> Customer, admin -> Admin)
        const roleLabel = role.charAt(0).toUpperCase() + role.slice(1);

        // Update name and role label
        if (sidebarLabel) {
            sidebarLabel.textContent = `${roleLabel}: ${name}`;
        }

        // Update icon and colors based on role
        if (userIcon) {
            if (role === 'admin') {
                userIcon.className = 'fas fa-user-shield';
                userIcon.style.color = '#f59e0b'; // Premium Amber/Gold for admin
            } else {
                userIcon.className = 'fas fa-user-circle';
                userIcon.style.color = 'var(--primary)'; // Default Primary for user/customer
            }
        }

        // Hide login links, show user menu
        if (loginLinks) loginLinks.style.display = 'none';
        if (userMenu)   userMenu.style.setProperty('display', 'flex', 'important');
    } else {
        // Not logged in
        if (loginLinks) loginLinks.style.setProperty('display', 'flex', 'important');
        if (userMenu)   userMenu.style.display = 'none';
    }

    // 3. Logout action
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('userRole');
            localStorage.removeItem('userName');
            localStorage.removeItem('userEmail');
            localStorage.removeItem('userId');
            localStorage.removeItem('userBalance');
            
            // Redirect to index.html on logout to show logged out state cleanly
            window.location.href = "index.html";
        });
    }
});
