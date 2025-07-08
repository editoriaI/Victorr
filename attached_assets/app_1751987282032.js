// Victor's Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Fix access dashboard button
    const accessButton = document.getElementById('accessDashboard');
    if (accessButton) {
        accessButton.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/auth/discord';
        });
    }
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
        "Ah. You brought me back online. How unfortunate—for them."
    ];

    // Rotate Victor's mood every 30 seconds
    setInterval(() => {
        const moodElement = document.getElementById('victorMood');
        if (moodElement) {
            const randomMood = victorMoods[Math.floor(Math.random() * victorMoods.length)];
            moodElement.style.opacity = '0';
            setTimeout(() => {
                moodElement.textContent = randomMood;
                moodElement.style.opacity = '1';
            }, 300);
        }
    }, 30000);

    // Navigation functionality
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
            document.getElementById(targetSection).classList.add('active');

            // Update URL hash
            window.location.hash = targetSection;
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

    // Embed builder functionality
    const embedTitle = document.getElementById('embedTitle');
    const embedDescription = document.getElementById('embedDescription');
    const previewTitle = document.getElementById('previewTitle');
    const previewDescription = document.getElementById('previewDescription');

    if (embedTitle && previewTitle) {
        embedTitle.addEventListener('input', () => {
            previewTitle.textContent = embedTitle.value || 'Your title here';
        });
    }

    if (embedDescription && previewDescription) {
        embedDescription.addEventListener('input', () => {
            previewDescription.textContent = embedDescription.value || 'Your description here';
        });
    }

    // Command toggle functionality
    const toggleSwitches = document.querySelectorAll('.toggle-switch input');
    toggleSwitches.forEach(toggle => {
        toggle.addEventListener('change', () => {
            // Simulate API call to update command status
            console.log(`Command ${toggle.closest('.command-card').querySelector('h3').textContent} ${toggle.checked ? 'enabled' : 'disabled'}`);

            // Add visual feedback
            const card = toggle.closest('.command-card');
            card.style.transform = 'scale(0.98)';
            setTimeout(() => {
                card.style.transform = 'scale(1)';
            }, 150);
        });
    });

    // Role builder functionality
    const addRoleBtn = document.querySelector('.add-role-btn');
    if (addRoleBtn) {
        addRoleBtn.addEventListener('click', () => {
            const roleBlocks = document.querySelector('.role-blocks');
            const newRoleBlock = document.createElement('div');
            newRoleBlock.className = 'role-block';
            newRoleBlock.innerHTML = `
                <input type="text" placeholder="🎭" class="emoji-input">
                <input type="text" placeholder="Role Name" class="role-name">
                <span class="role-description">Another role for the collection.</span>
                <button class="remove-role-btn" onclick="removeRole(this)">×</button>
            `;
            roleBlocks.appendChild(newRoleBlock);
        });
    }

    // Mood selector functionality
    const moodOptions = document.querySelectorAll('input[name="mood"]');
    moodOptions.forEach(option => {
        option.addEventListener('change', () => {
            const selectedMood = option.value;
            console.log(`Victor's mood changed to: ${selectedMood}`);

            // Update onboarding message placeholder based on mood
            const messageTextarea = document.getElementById('onboardingMessage');
            if (messageTextarea) {
                const moodMessages = {
                    sarcastic: "Welcome to {server}, {user}. Don't break anything, or do. Victor's watching.",
                    warm: "Hello {user}! Welcome to our cozy little {server}! We're so happy you're here! 💕",
                    professional: "Welcome to {server}, {user}. Please review the rules and enjoy your stay.",
                    cryptic: "You have entered {server}. The shadows welcome you, {user}. Stay."
                };
                messageTextarea.placeholder = moodMessages[selectedMood] || messageTextarea.placeholder;
            }
        });
    });

    // Save configurations (placeholder functionality)
    const saveButtons = document.querySelectorAll('.save-btn, .apply-btn');
    saveButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Show temporary success message
            showNotification('Settings saved successfully!', 'success');
        });
    });
});

// Global functions
function runDiagnostics() {
    const btn = event.target;
    const originalText = btn.innerHTML;

    btn.innerHTML = '<i data-feather="loader"></i> Running...';
    btn.disabled = true;
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // Simulate diagnostic process
    setTimeout(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        showNotification('Diagnostics complete. All systems operational.', 'success');
    }, 3000);
}

function removeRole(button) {
    button.closest('.role-block').remove();
}

function logout() {
    if (confirm('Goodbye, darling. Try not to ruin anything in my absence.')) {
        window.location.href = '/logout';
    }
}

// Dashboard JavaScript functionality

// Navigation between sections
function showSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => section.classList.remove('active'));

    // Hide all nav items
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));

    // Show selected section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Highlight nav item
    const targetNav = document.querySelector(`[data-section="${sectionId}"]`);
    if (targetNav) {
        targetNav.classList.add('active');
    }

    // Load marketplace data if marketplace section is shown
    if (sectionId === 'marketplace') {
        loadMarketplaceData();
    }
}

// Marketplace tab functionality
function initializeMarketplaceTabs() {
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
            document.getElementById(targetTab).classList.add('active');

            // Load tab-specific data
            loadTabData(targetTab);
        });
    });
}

// Load marketplace data
function loadMarketplaceData() {
    loadTabData('browse');
}

// Load tab-specific data
function loadTabData(tab) {
    switch(tab) {
        case 'browse':
            loadMarketItems();
            break;
        case 'mylistings':
            loadUserListings();
            break;
        case 'transactions':
            loadUserTransactions();
            break;
    }
}

// Load market items
async function loadMarketItems() {
    const container = document.getElementById('marketItems');
    container.innerHTML = '<div class="loading-message">Loading market items...</div>';

    try {
        // This would connect to your bot's marketplace API
        const mockItems = [
            { id: 1, name: 'Gothic Dress', price: 5000, seller: 'VictorsFan', category: 'clothing' },
            { id: 2, name: 'Dark Crown', price: 12000, seller: 'ShadowQueen', category: 'accessories' },
            { id: 3, name: 'Vampire Cape', price: 8000, seller: 'NightWalker', category: 'clothing' }
        ];

        displayMarketItems(mockItems);
    } catch (error) {
        container.innerHTML = '<div class="loading-message">Error loading market items</div>';
    }
}

// Display market items
function displayMarketItems(items) {
    const container = document.getElementById('marketItems');

    if (items.length === 0) {
        container.innerHTML = '<div class="loading-message">No items found</div>';
        return;
    }

    const itemsHTML = items.map(item => `
        <div class="market-item">
            <div class="item-name">${item.name}</div>
            <div class="item-price">${item.price.toLocaleString()} coins</div>
            <div class="item-seller">Sold by: ${item.seller}</div>
            <button class="buy-btn" onclick="buyItem(${item.id})">Buy Now</button>
        </div>
    `).join('');

    container.innerHTML = itemsHTML;
}

// Load user listings
async function loadUserListings() {
    const container = document.getElementById('userListings');
    container.innerHTML = '<div class="loading-message">Loading your listings...</div>';

    // Mock user listings
    const mockListings = [
        { id: 1, name: 'My Gothic Dress', price: 5000, status: 'active', created: '2024-01-15' }
    ];

    const listingsHTML = mockListings.map(listing => `
        <div class="market-item">
            <div class="item-name">${listing.name}</div>
            <div class="item-price">${listing.price.toLocaleString()} coins</div>
            <div class="item-seller">Status: ${listing.status}</div>
            <button class="buy-btn" onclick="removeListing(${listing.id})">Remove</button>
        </div>
    `).join('');

    container.innerHTML = listingsHTML || '<div class="loading-message">No active listings</div>';
}

// Load user transactions
async function loadUserTransactions() {
    const container = document.getElementById('userTransactions');
    container.innerHTML = '<div class="loading-message">Loading transaction history...</div>';

    // Mock transactions
    const mockTransactions = [
        { id: 1, item: 'Dark Crown', amount: 12000, type: 'purchase', date: '2024-01-14' },
        { id: 2, item: 'Gothic Dress', amount: 5000, type: 'sale', date: '2024-01-13' }
    ];

    const transactionsHTML = mockTransactions.map(tx => `
        <div class="transaction-item">
            <div class="transaction-details">
                <h4>${tx.item}</h4>
                <p>${tx.type} on ${tx.date}</p>
            </div>
            <div class="transaction-amount">
                ${tx.type === 'purchase' ? '-' : '+'}${tx.amount.toLocaleString()} coins
            </div>
        </div>
    `).join('');

    container.innerHTML = transactionsHTML || '<div class="loading-message">No transactions found</div>';
}

// Create new listing
function createListing() {
    const itemName = document.getElementById('itemName').value;
    const itemPrice = document.getElementById('itemPrice').value;
    const itemCategory = document.getElementById('itemCategory').value;
    const itemDescription = document.getElementById('itemDescription').value;

    if (!itemName || !itemPrice) {
        alert('Please fill in item name and price');
        return;
    }

    // This would send to your bot's API
    console.log('Creating listing:', { itemName, itemPrice, itemCategory, itemDescription });
    alert('Listing created successfully! (This is a demo)');

    // Clear form
    document.getElementById('itemName').value = '';
    document.getElementById('itemPrice').value = '';
    document.getElementById('itemDescription').value = '';
}

// Buy item
function buyItem(itemId) {
    // This would connect to your bot's purchase API
    console.log('Buying item:', itemId);
    alert('Purchase successful! (This is a demo)');
    loadMarketItems(); // Refresh items
}

// Remove listing
function removeListing(listingId) {
    // This would connect to your bot's API
    console.log('Removing listing:', listingId);
    alert('Listing removed! (This is a demo)');
    loadUserListings(); // Refresh listings
}

function showVerificationCases() {
    showNotification('Verification cases viewer coming soon!', 'info');
}

function showUserReports() {
    showNotification('User reports system coming soon!', 'info');
}

function showAIModeration() {
    showNotification('AI moderation features coming soon!', 'info');
}

function showSupport() {
    window.open('https://discord.gg/your-support-server', '_blank');
}

function showDonate() {
    showNotification('Thank you for considering supporting Victor!', 'success');
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;

    // Add notification styles if not already present
    if (!document.querySelector('.notification-styles')) {
        const styles = document.createElement('style');
        styles.className = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: var(--bg-secondary);
                color: var(--text-primary);
                padding: 1rem 1.5rem;
                border-radius: 8px;
                border: 1px solid var(--border-color);
                box-shadow: var(--shadow);
                z-index: 1000;
                display: flex;
                align-items: center;
                gap: 1rem;
                animation: slideIn 0.3s ease;
            }
            .notification.success {
                border-color: var(--accent-pink);
                background: linear-gradient(135deg, var(--bg-secondary), #2A1A2A);
            }
            .notification button {
                background: none;
                border: none;
                color: var(--text-muted);
                cursor: pointer;
                font-size: 1.2rem;
                padding: 0;
                line-height: 1;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(styles);
    }

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Handle window resize for responsive navigation
window.addEventListener('resize', () => {
    if (window.innerWidth <= 768) {
        // Mobile navigation adjustments
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.style.position = 'relative';
        }
    }
});

// Initialize Feather icons when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (window.feather) {
        feather.replace();
    }

    // Initialize marketplace tabs
    initializeMarketplaceTabs();

    // Handle nav clicks
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.getAttribute('data-section');
            if (section) {
                showSection(section);
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Auth tab switching
        const authTabs = document.querySelectorAll('.auth-tab');
        const authContents = document.querySelectorAll('.auth-content');

        authTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.getAttribute('data-tab');

                // Remove active class from all tabs and contents
                authTabs.forEach(t => t.classList.remove('active'));
                authContents.forEach(c => c.classList.remove('active'));

                // Add active class to clicked tab and corresponding content
                tab.classList.add('active');
                document.getElementById(targetTab).classList.add('active');
            });
        });

        // Discord authentication buttons
        const discordLogin = document.getElementById('discordLogin');
        const discordSignup = document.getElementById('discordSignup');

        if (discordLogin) {
            discordLogin.addEventListener('click', function() {
                window.location.href = '/auth/discord';
            });
        }

        if (discordSignup) {
            discordSignup.addEventListener('click', function() {
                window.location.href = '/auth/discord';
            });
        }

        // Manual login form
        const manualLogin = document.getElementById('manualLogin');
        if (manualLogin) {
            manualLogin.addEventListener('submit', function(e) {
                e.preventDefault();
                showNotification('Manual login coming soon! Please use Discord authentication for now.', 'info');
            });
        }

        // Manual signup form
        const manualSignup = document.getElementById('manualSignup');
        if (manualSignup) {
            manualSignup.addEventListener('submit', function(e) {
                e.preventDefault();
                const password = e.target.querySelector('input[type="password"]').value;
                const confirmPassword = e.target.querySelectorAll('input[type="password"]')[1].value;

                if (password !== confirmPassword) {
                    showNotification('Passwords do not match!', 'error');
                    return;
                }

                showNotification('Account creation coming soon! Please use Discord authentication for now.', 'info');
            });
        }
});