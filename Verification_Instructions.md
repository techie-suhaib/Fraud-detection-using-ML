# Verification Instructions

## Scenario Table

| # | Amount | Location | Device | Expected outcome |
|---|--------|----------|--------|------------------|
| 1 | 150 | Local | Same Device (Linked) | Transaction Safe |
| 2 | 200 | Local | New Device (Unlinked) | Transaction Safe + “New Device Login” badge |
| 3 | 10 → 10 → 50 (same device) | Local | Same Device (Linked) | High Risk Blocked (High Velocity) |
| 4 | 12 000 | Local | Same Device (Linked) | High Risk Blocked (High Amount Anomaly) |
| 5 (warning) | 100 | International | Same Device (Linked) | Transaction Safe with “Unusual Location” warning (no block) |
| 6 (blocked) | 100 | International | Same Device (Linked) after you enable “Block International Payments” (see admin steps) | High Risk Blocked (International Payment Blocked) |
| 7 (blocked) | 50 | Local | Same Device (Linked) after you add user 2 to the blacklist | High Risk Blocked (Blacklisted Account) |

## Admin Steps
1. Open `http://127.0.0.1:5000/admin.html` and login with **admin@fraudguard.ai / admin123**. You will be redirected to the dashboard.
2. Click the **Security** link → `security.html`.
3. Turn **ON** “Block International Payments”.
4. In **Account Blacklist**, enter `2` (the test user’s ID) and click **Ban Account**.
5. Click **Save Changes** – a “Changes Saved!” toast should appear.
6. Logout via the top‑right button to return to the login screen.

## User Flow Verification
1. Return to the user interface (`http://127.0.0.1:5000/user.html`).
2. Re‑run scenarios 5 & 6 now that the admin settings are active and confirm the expected outcomes.

## Transaction Log Check
- Open `http://127.0.0.1:5000/transaction.html`.
- Verify the transaction table records all actions performed, showing the correct **Risk Level** and **Status** badges.

---
*Export this document to PDF (e.g., using your editor’s “Print → Save as PDF” feature).*
