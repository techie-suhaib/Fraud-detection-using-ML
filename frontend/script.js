// Helper: Get or create device fingerprint
if (!localStorage.getItem('deviceId')) {
    localStorage.setItem('deviceId', 'dev_' + Math.random().toString(36).substring(2, 11));
}

// Fetch and load dashboard stats
async function loadStats() {
    try {
        const response = await fetch('/api/dashboard/stats');
        const stats = await response.json();
        
        document.getElementById('totalScanned').innerText = stats.totalScanned.toLocaleString();
        document.getElementById('fraudBlocked').innerText = stats.fraudBlocked.toLocaleString();
        document.getElementById('trustScore').innerText = stats.trustScore;
    } catch (err) {
        console.error("Error loading dashboard stats:", err);
    }
}

// Run on load
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
});

// Form submission handler
document.getElementById('fraudForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const btn = document.getElementById('analyzeBtn');
    const title = document.getElementById('resultTitle');
    const text = document.getElementById('resultText');
    const icon = document.getElementById('statusIcon');
    const progress = document.getElementById('riskProgress');
    const container = document.getElementById('progressContainer');

    // Button loading animation
    btn.innerText = "Analyzing Risk Patterns...";
    btn.disabled = true;
    container.style.display = 'none';

    // Collect data
    const amount = parseFloat(document.getElementById('amount').value);
    const category = document.getElementById('category').value;
    const deviceStatus = document.getElementById('deviceStatus').value;
    const location = document.getElementById('location').value;
    
    let finalDeviceId = localStorage.getItem('deviceId');
    if (deviceStatus === 'new') {
        finalDeviceId = 'dev_new_' + Math.random().toString(36).substring(2, 11);
    }
    const userId = localStorage.getItem('userId') || '2'; // Default to test user ID

    // Map Category to Transaction Type
    let txnType = 'PAYMENT';
    if (category === 'banking') {
        txnType = 'TRANSFER';
    } else if (category === 'retail') {
        txnType = 'PAYMENT';
    }

    try {
        const response = await fetch('/api/transactions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                amount: amount,
                transaction_type: txnType,
                location: location,
                device_id: finalDeviceId,
                device_type: 'Desktop',
                os: 'Windows'
            })
        });

        const res = await response.json();
        
        if (!response.ok) {
            throw new Error(res.error || "Failed to analyze transaction");
        }

        // Simulate API delay for premium feels
        setTimeout(() => {
            const score = res.fraud_score;
            const isFraud = res.is_fraud;
            
            container.style.display = 'block';
            progress.style.width = score + "%";

            // Determine risk level based on backend is_fraud decision
            if (isFraud) {
                // High risk
                title.innerText = "High Risk Blocked";
                title.style.color = "#ef4444";
                
                let rulesMsg = res.rules_triggered && res.rules_triggered.length > 0 ? ` [Rules: ${res.rules_triggered.join(', ')}]` : '';
                text.innerText = `Danger: Risk Score is ${score}%. Potential fraudulent patterns detected.${rulesMsg}`;
                icon.innerHTML = '<i class="fas fa-exclamation-triangle" style="color:#ef4444"></i>';
                progress.style.backgroundColor = "#ef4444";
            } else {
                // Low/medium risk (considered safe)
                title.innerText = "Transaction Safe";
                title.style.color = "#10b981";
                text.innerText = `Verified: Risk Score is ${score}%. Transaction looks safe. Fund balance updated.`;
                icon.innerHTML = '<i class="fas fa-check-circle" style="color:#10b981"></i>';
                progress.style.backgroundColor = "#10b981";
                
                // Update cached balance
                if (res.new_balance !== undefined) {
                    localStorage.setItem("userBalance", res.new_balance);
                }
            }

            // Restore button and reload stats
            btn.innerText = "Analyze Risk";
            btn.disabled = false;
            loadStats();
        }, 1200);

    } catch (err) {
        console.error(err);
        btn.innerText = "Analyze Risk";
        btn.disabled = false;
        title.innerText = "Connection Error";
        title.style.color = "#ef4444";
        text.innerText = err.message || "Failed to connect to backend server. Make sure Flask app is running.";
        icon.innerHTML = '<i class="fas fa-times-circle" style="color:#ef4444"></i>';
    }
});