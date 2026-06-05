document.addEventListener('DOMContentLoaded', () => {
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
});
