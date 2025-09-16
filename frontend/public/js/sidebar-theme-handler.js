/**
 * Global Sidebar and Theme Container Handler
 * Ensures theme selector adjusts properly with sidebar state across all pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Override global toggleSidebar function to handle theme containers
    if (typeof window.toggleSidebar === 'function') {
        const originalToggleSidebar = window.toggleSidebar;
        
        window.toggleSidebar = function() {
            // Call original function
            originalToggleSidebar();
            
            // Additional theme container handling
            handleThemeContainerResize();
        };
    } else {
        // Create toggleSidebar function if it doesn't exist
        window.toggleSidebar = function() {
            const sb = document.querySelector('.sidebar');
            const btn = document.getElementById('toggleSidebarBtn');
            const showBtn = document.getElementById('showSidebarBtn');
            const sections = document.querySelectorAll('section,.embeding-box,.params-row,.plots-container,.content-section');
            
            if (sb && sb.classList.contains('hidden')) {
                // Show sidebar
                sb.classList.remove('hidden');
                sections.forEach(s => {
                    s.style.marginLeft = '250px';
                    s.style.width = '80%';
                });
                if (btn) btn.style.display = 'block';
                if (showBtn) showBtn.style.display = 'none';
            } else {
                // Hide sidebar
                if (sb) sb.classList.add('hidden');
                sections.forEach(s => {
                    s.style.marginLeft = '20px';
                    s.style.width = '95%';
                });
                if (btn) btn.style.display = 'none';
                if (showBtn) showBtn.style.display = 'block';
            }
            
            handleThemeContainerResize();
        };
    }
    
    function handleThemeContainerResize() {
        const themeContainer = document.querySelector('.theme-selector-container');
        const sidebar = document.querySelector('.sidebar');
        
        if (themeContainer) {
            if (sidebar && sidebar.classList.contains('hidden')) {
                // Sidebar hidden
                themeContainer.style.marginLeft = '20px';
                themeContainer.style.width = '95%';
            } else {
                // Sidebar visible
                themeContainer.style.marginLeft = '220px';
                themeContainer.style.width = '83%';
            }
        }
    }
    
    // Initial setup
    handleThemeContainerResize();
    
    // Watch for sidebar changes
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    handleThemeContainerResize();
                }
            });
        });
        
        observer.observe(sidebar, {
            attributes: true,
            attributeFilter: ['class']
        });
    }
});