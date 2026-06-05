// DOM Elements
const thresholdInput = document.getElementById('threshold');
const thresholdVal = document.getElementById('thresholdVal');
const blockIntInput = document.getElementById('blockInt');
const bannedList = document.getElementById('blacklist');
const activeModelInput = document.getElementById('activeModel');

// Sync threshold range slider label
thresholdInput.oninput = function() {
    thresholdVal.innerText = this.value + "%";
};

// Fetch security settings from database on load
async function loadSecuritySettings() {
    try {
        const response = await fetch('/api/security/settings');
        const settings = await response.json();
        
        // Auto block threshold
        if (settings.auto_block_threshold) {
            const val = parseFloat(settings.auto_block_threshold);
            thresholdInput.value = val;
            thresholdVal.innerText = val + "%";
        }
        
        // Active ML model
        if (settings.active_model && activeModelInput) {
            activeModelInput.value = settings.active_model;
        }
        
        // International blocking
        if (settings.block_international) {
            blockIntInput.checked = settings.block_international === 'true';
        }
        
        // Blacklisted accounts list
        if (settings.blacklist_accounts) {
            bannedList.innerHTML = "";
            const accounts = settings.blacklist_accounts.split(',');
            accounts.forEach(acc => {
                if (acc.trim()) {
                    addBlacklistItemToUI(acc.trim());
                }
            });
        }
    } catch (err) {
        console.error("Error loading security settings:", err);
    }
}

// Add account item to the DOM list helper
function addBlacklistItemToUI(account) {
    const li = document.createElement('li');
    li.dataset.account = account;
    li.innerHTML = `${account} <i class="fas fa-times" onclick="this.parentElement.remove()"></i>`;
    bannedList.appendChild(li);
}

// Click Ban Account button
function addBlacklist() {
    const input = document.getElementById('banAcc');
    const account = input.value.trim();
    
    if (account !== "") {
        // Prevent duplicates
        let exists = false;
        bannedList.querySelectorAll('li').forEach(li => {
            if (li.dataset.account === account) exists = true;
        });
        
        if (!exists) {
            addBlacklistItemToUI(account);
        }
        input.value = "";
    }
}

// Save all settings to backend MySQL
async function saveSettings() {
    const btn = document.querySelector('.save-btn');
    btn.innerText = "Saving...";
    btn.style.opacity = "0.7";
    btn.disabled = true;
    
    // Read blacklist accounts
    const accounts = [];
    bannedList.querySelectorAll('li').forEach(li => {
        accounts.push(li.dataset.account);
    });
    
    const settings = {
        auto_block_threshold: thresholdInput.value,
        active_model: activeModelInput ? activeModelInput.value : 'random_forest',
        block_international: blockIntInput.checked ? 'true' : 'false',
        blacklist_accounts: accounts.join(',')
    };

    try {
        const response = await fetch('/api/security/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });

        if (!response.ok) throw new Error("Failed to save settings");

        btn.innerText = "Changes Saved!";
        btn.style.backgroundColor = "#10b981";
        
        setTimeout(() => {
            btn.innerText = "Save Changes";
            btn.style.backgroundColor = "#3b82f6";
            btn.style.opacity = "1";
            btn.disabled = false;
        }, 2000);
        
    } catch (err) {
        console.error(err);
        btn.innerText = "Error Saving";
        btn.style.backgroundColor = "#ef4444";
        btn.disabled = false;
        
        setTimeout(() => {
            btn.innerText = "Save Changes";
            btn.style.backgroundColor = "#3b82f6";
            btn.style.opacity = "1";
        }, 2000);
    }
}

// Load on start
document.addEventListener('DOMContentLoaded', loadSecuritySettings);