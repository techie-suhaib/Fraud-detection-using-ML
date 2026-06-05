// Fetch and display transaction list from database
async function loadTransactions() {
    const tbody = document.getElementById("txnLogBody");
    if (!tbody) return;
    
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center;"><i class="fas fa-spinner fa-spin"></i> Loading transaction logs...</td></tr>`;

    try {
        const response = await fetch('/api/transactions');
        const transactions = await response.json();

        if (transactions.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center;">No transactions analyzed yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = ""; // Clear loader
        transactions.forEach(txn => {
            const score = txn.fraud_score;
            const isFraud = txn.is_fraud;
            
            // Risk level class
            let riskClass = 'low';
            if (score > 70) {
                riskClass = 'high';
            } else if (score > 40) {
                riskClass = 'medium';
            }

            const rowHTML = `
                <tr>
                    <td>${txn.transaction_time}</td>
                    <td>#TXN-${txn.transaction_id}</td>
                    <td>${txn.full_name} (${txn.transaction_type})</td>
                    <td>$${txn.amount.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td><span class="risk-badge ${riskClass}">${score}%</span></td>
                    <td><span class="${isFraud ? 'status-blocked' : 'status-verified'}">${isFraud ? 'Blocked' : 'Verified'}</span></td>
                </tr>
            `;
            tbody.insertAdjacentHTML('beforeend', rowHTML);
        });

    } catch (err) {
        console.error("Error loading transactions:", err);
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #ef4444;"><i class="fas fa-times-circle"></i> Error loading logs. Connect to API.</td></tr>`;
    }
}

// Search utility
function searchTable() {
    const input = document.getElementById("txnSearch");
    const filter = input.value.toUpperCase();
    const table = document.getElementById("txnTable");
    const tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        const idCol = tr[i].getElementsByTagName("td")[1]; // Transaction ID
        const nameCol = tr[i].getElementsByTagName("td")[2]; // User Name / Type
        
        if (idCol || nameCol) {
            const txtValue = (idCol.textContent || idCol.innerText) + 
                             (nameCol.textContent || nameCol.innerText);
            
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    }
}

// Export Table to CSV
document.querySelector('.export-btn').addEventListener('click', function() {
    const table = document.getElementById("txnTable");
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Header
    const headers = Array.from(table.querySelectorAll("th")).map(th => th.innerText);
    csvContent += headers.join(",") + "\r\n";
    
    // Rows
    const rows = table.querySelectorAll("tbody tr");
    rows.forEach(row => {
        const cols = Array.from(row.querySelectorAll("td")).map(td => td.innerText.replace(/,/g, ''));
        csvContent += cols.join(",") + "\r\n";
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "transaction_logs.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});

// Load on start
document.addEventListener('DOMContentLoaded', loadTransactions);