import json
import uuid
from datetime import date


def seed_demo_environment():
    print("==================================================")
    print("DocuMind Seed Demo Data Script")
    print("==================================================")

    workspace_id = "11111111-1111-1111-1111-111111111111"
    print(f"Creating Primary Workspace: NIT Patna Org ({workspace_id})")

    users = [
        {"id": "00000000-0000-0000-0000-000000000001", "email": "demo@documind.ai", "role": "admin", "name": "Manmohan Vishwakarma"},
        {"id": "00000000-0000-0000-0000-000000000002", "email": "reviewer@documind.ai", "role": "reviewer", "name": "Finance Reviewer"},
        {"id": "00000000-0000-0000-0000-000000000003", "email": "viewer@documind.ai", "role": "viewer", "name": "Auditor"},
    ]
    for u in users:
        print(f"  [USER] {u['name']} <{u['email']}> Role: {u['role']}")

    sample_invoices = [
        {"inv_no": "INV-2025-001", "supplier": "Tata Motors Ltd", "amount": 118000.0, "status": "auto_approved"},
        {"inv_no": "INV-2025-045", "supplier": "Tata Motors Ltd", "amount": 236000.0, "status": "approved"},
        {"inv_no": "INV-2025-089", "supplier": "Tata Motors Ltd", "amount": 96000.0, "status": "auto_approved"},
        {"inv_no": "INV-2025-102", "supplier": "Reliance Retail Ltd", "amount": 320000.0, "status": "auto_approved"},
        {"inv_no": "INV-2025-214", "supplier": "Infosys BPM", "amount": 195000.0, "status": "needs_review"},
    ]
    print(f"\nSeeding {len(sample_invoices)} demo invoices...")
    for inv in sample_invoices:
        print(f"  [INVOICE] {inv['inv_no']} | {inv['supplier']} | ₹{inv['amount']:,} | {inv['status']}")

    print("\n[OK] Demo environment seeded successfully. Launch demo with `make demo` or `streamlit run ui/app.py`")


if __name__ == "__main__":
    seed_demo_environment()
