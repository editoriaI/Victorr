// Victor's Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons (check if available)
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // Victor's mood quotes rotation
    const victorMoods = [
        "Mmm, admin power. Don't let it go to your head.",
        "The server will collapse without your careful micromanagement.",
        "I watched three mortals argue for ten minutes over a role name. You're my last hope.",
        "Let's get this configured before I fall apart. Again.",
        "I would offer help… but I'm more into observation than intervention.",
        "Ah. You brought me back online. How unfortunate—for them.",
        "Another day, another Discord drama. At least the marketplace is thriving.",
        "Your users are... colorful. I prefer the shadows, personally.",
        "Trading in the darkness has never been more efficient."
    ];

    // Rotate Victor's mood every 30 seconds
    const moodElement = document.getElementById('victorMood');
    if (moodElement) {
        setInterval(() => {
            const randomMood = victorMoods[Math.floor(Math.random() * victorMoods.length)];
            moodElement.style.opacity = '0';
            setTimeout(() => {
                moodElement.textContent = randomMood;
                moodElement.style.opacity = '1';
            }, 300);
        }, 30000);
    }

    // Navigation functionality
    initializeNavigation();

    // Marketplace functionality
    initializeMarketplace();

    // Settings functionality
    initializeSettings();

    // Auto-refresh data periodically
    startDataRefresh();
});

// Mobile sidebar functions
function toggleMobileSidebar() {
    const sidebar = document.getElementById('mobileSidebar');
    const overlay = document.querySelector('.mobile-sidebar-overlay');

    if (sidebar && overlay) {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
    }
}

function closeMobileSidebar() {
    const sidebar = document.getElementById('mobileSidebar');
    const overlay = document.querySelector('.mobile-sidebar-overlay');

    if (sidebar && overlay) {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    }
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('mobileSidebar');
    const toggleBtn = document.querySelector('.mobile-sidebar-toggle');

    if (sidebar && toggleBtn && window.innerWidth <= 768) {
        if (!sidebar.contains(event.target) && !toggleBtn.contains(event.target)) {
            closeMobileSidebar();
        }
    }
});

function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const contentSections = document.querySelectorAll('.content-section');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetSection = item.getAttribute('data-section');

            // Remove active class from all nav items and sections
            navItems.forEach(nav => nav.classList.remove('active'));
            contentSections.forEach(section => section.classList.remove('active'));

            // Add active class to clicked nav item and corresponding section
            item.classList.add('active');
            const targetElement = document.getElementById(targetSection);
            if (targetElement) {
                targetElement.classList.add('active');
            }

            // Update URL hash
            window.location.hash = targetSection;

            // Load section-specific data
            loadSectionData(targetSection);
        });
    });

    // Handle direct URL hash navigation
    if (window.location.hash) {
        const hashSection = window.location.hash.substr(1);
        const targetNav = document.querySelector(`[data-section="${hashSection}"]`);
        if (targetNav) {
            targetNav.click();
        }
    }
}

function initializeMarketplace() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');

            // Remove active class from all tabs and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked tab and corresponding content
            button.classList.add('active');
            const targetContent = document.getElementById(targetTab);
            if (targetContent) {
                targetContent.classList.add('active');
            }

            // Load tab-specific data
            loadTabData(targetTab);
        });
    });
}

function initializeSettings() {
    // Form validation and saving
    const saveButtons = document.querySelectorAll('.btn-primary');
    saveButtons.forEach(btn => {
        if (btn.textContent.includes('Save')) {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                showNotification('Settings saved successfully!', 'success');
            });
        }
    });

    // Settings form changes
    const formInputs = document.querySelectorAll('input, select, textarea');
    formInputs.forEach(input => {
        input.addEventListener('change', () => {
            // Mark form as dirty
            input.closest('form')?.classList.add('form-dirty');
        });
    });
}

function loadSectionData(section) {
    switch(section) {
        case 'overview':
            loadOverviewData();
            break;
        case 'users':
            loadUsersData();
            break;
        case 'marketplace':
            loadMarketplaceData();
            break;
        case 'analytics':
            loadAnalyticsData();
            break;
        case 'settings':
            loadSettingsData();
            break;
    }
}

function loadOverviewData() {
    // Refresh dashboard statistics
    refreshStats();
}

function loadUsersData() {
    const tableBody = document.getElementById('usersTableBody');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <div class="empty-state">
                        <i data-feather="users"></i>
                        <p>No users to display</p>
                        <small>Users will appear here once they start using the bot</small>
                    </div>
                </td>
            </tr>
        `;

        // Reinitialize icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

function loadMarketplaceData() {
    loadTabData('browse');
}

function loadTabData(tab) {
    switch(tab) {
        case 'browse':
            loadMarketItems();
            break;
        case 'analytics':
            loadMarketAnalytics();
            break;
        case 'moderation':
            loadModerationData();
            break;
    }
}

function loadMarketItems() {
    const container = document.getElementById('marketItems');
    if (!container) return;

    container.innerHTML = `
        <div class="loading-message">
            <i data-feather="loader"></i>
            Loading marketplace items...
        </div>
    `;

    // Simulate loading delay
    setTimeout(() => {
        container.innerHTML = `
            <div class="empty-state">
                <i data-feather="shopping-bag"></i>
                <p>No items currently listed</p>
                <small>Items will appear here when users create listings</small>
            </div>
        `;

        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }, 1000);
}

function loadMarketAnalytics() {
    // Load marketplace analytics data
    console.log('Loading marketplace analytics...');
}

function loadModerationData() {
    // Load moderation tools data
    console.log('Loading moderation data...');
}

function loadAnalyticsData() {
    // Load analytics dashboard data
    console.log('Loading analytics data...');
}

function loadSettingsData() {
    // Load current settings
    console.log('Loading settings...');
}

function refreshStats() {
    // Fetch and update statistics
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            updateStatNumbers(data);
        })
        .catch(error => {
            console.error('Error fetching stats:', error);
        });
}

function updateStatNumbers(stats) {
    const statElements = {
        'total_users': document.querySelector('.dashboard-card:nth-child(1) .stat-number'),
        'verified_users': document.querySelector('.dashboard-card:nth-child(2) .stat-number'),
        'active_listings': document.querySelector('.dashboard-card:nth-child(3) .stat-number'),
        'total_transactions': document.querySelector('.dashboard-card:nth-child(4) .stat-number')
    };

    Object.keys(statElements).forEach(key => {
        const element = statElements[key];
        if (element && stats[key] !== undefined) {
            animateNumber(element, parseInt(element.textContent) || 0, stats[key]);
        }
    });
}

function animateNumber(element, from, to) {
    const duration = 1000;
    const start = Date.now();
    const range = to - from;

    function updateNumber() {
        const elapsed = Date.now() - start;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(from + (range * progress));

        element.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }

    updateNumber();
}

function searchItems() {
    const searchTerm = document.getElementById('itemSearch')?.value || '';
    const category = document.getElementById('categoryFilter')?.value || '';

    const container = document.getElementById('marketItems');
    if (!container) return;

    container.innerHTML = `
        <div class="loading-message">
            <i data-feather="search"></i>
            Searching for items...
        </div>
    `;

    // Simulate search
    setTimeout(() => {
        container.innerHTML = `
            <div class="empty-state">
                <i data-feather="search"></i>
                <p>No items found${searchTerm ? ` for "${searchTerm}"` : ''}</p>
                <small>Try adjusting your search criteria</small>
            </div>
        `;

        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }, 500);
}

function runDiagnostics() {
    const btn = event.target.closest('button');
    const originalContent = btn.innerHTML;

    btn.innerHTML = '<i data-feather="loader"></i> Running diagnostics...';
    btn.disabled = true;

    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // Simulate diagnostic process
    setTimeout(() => {
        btn.innerHTML = originalContent;
        btn.disabled = false;

        if (typeof feather !== 'undefined') {
            feather.replace();
        }

        showNotification('Diagnostics complete. All systems operational.', 'success');
    }, 3000);
}

function logout() {
    if (confirm('Goodbye, darling. Try not to ruin anything in my absence.')) {
        window.location.href = '/logout';
    }
}

function showNotification(message, type = 'info') {
    const alertClass = type === 'error' ? 'alert-danger' : `alert-${type}`;
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Find or create flash messages container
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        document.body.appendChild(container);
    }

    container.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function startDataRefresh() {
    // Refresh data every 30 seconds
    setInterval(() => {
        const activeSection = document.querySelector('.content-section.active');
        if (activeSection && activeSection.id === 'overview') {
            refreshStats();
        }
    }, 30000);
}

// Utility functions
function formatNumber(num) {
    return num.toLocaleString();
}

function formatCurrency(amount) {
    return `${amount.toLocaleString()} coins`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString();
}

// Handle form submissions
document.addEventListener('submit', function(e) {
    const form = e.target;
    if (form.classList.contains('ajax-form')) {
        e.preventDefault();
        handleFormSubmission(form);
    }
});

function handleFormSubmission(form) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;

    submitBtn.innerHTML = '<i data-feather="loader"></i> Saving...';
    submitBtn.disabled = true;

    // Simulate form submission
    setTimeout(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        showNotification('Form submitted successfully!', 'success');

        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }, 1000);
}

// Global error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showNotification('An unexpected error occurred. Please refresh the page.', 'error');
});

// Handle navigation state
window.addEventListener('popstate', function(e) {
    if (window.location.hash) {
        const hashSection = window.location.hash.substr(1);
        const targetNav = document.querySelector(`[data-section="${hashSection}"]`);
        if (targetNav) {
            targetNav.click();
        }
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-input, #userSearch, #itemSearch');
        if (searchInput) {
            searchInput.focus();
        }
    }

    // Escape to close modals or clear search
    if (e.key === 'Escape') {
        const searchInputs = document.querySelectorAll('.search-input, #userSearch, #itemSearch');
        searchInputs.forEach(input => {
            if (input === document.activeElement) {
                input.blur();
                input.value = '';
            }
        });
    }
});

// Initialize tooltips if Bootstrap is available
document.addEventListener('DOMContentLoaded', function() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// Theme management
function toggleTheme() {
    document.body.classList.toggle('victor-theme');
    localStorage.setItem('theme', document.body.classList.contains('victor-theme') ? 'victor' : 'default');
}

// Load saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'victor' || !savedTheme) {
    document.body.classList.add('victor-theme');
}

// Export functions for global access
window.VictorDashboard = {
    searchItems,
    runDiagnostics,
    logout,
    showNotification,
    refreshStats,
    toggleTheme
};