Digistore24 — Product Approval Support Tool (≤ 4 h)

## 🎯 Objective

Build a Django-based web application where:

- AI prediction results for product approvals are stored in the database.
- Supporters log in and automatically get assigned the oldest unreviewed prediction.
- They review the AI’s suggested rejection reasons and can optionally correct them.
- Their decision is saved to the database.

Focus is on a simple/usable frontend and clear data model, not complex backend logic.

## 🏢 Business Context

Digistore24 is automating product approvals with AI. Human supporters still review and validate AI-generated rejection reasons. This tool lets our team verify results efficiently while we move toward more automation.

## 🚀 Getting Started

Prerequisites:
- Python 3.11+
- Virtual environment recommended

Install and run (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py seed_predictions --reset
.\.venv\Scripts\python manage.py runserver
```

Open http://127.0.0.1:8000/

## 👤 Demo Accounts

- support / support123
- John / pass123
- Jane / pass123
- Anthony / pass123

Usernames are case-insensitive (e.g., JOHN == john). Passwords remain case-sensitive.

## 🔁 Resetting Data

To wipe review data and reseed demo content (schema is preserved):

```powershell
.\.venv\Scripts\python manage.py seed_predictions --reset
```

This deletes ReviewDecision, Review, RejectionReasonPrediction, and ProductPrediction rows, then recreates demo users and sample predictions.

## 🔌 API: Ingest Prediction

Endpoint: `POST /api/predictions/`

Example payload:

```json
{
  "product_id": "498589",
  "rejection_reasons": [
    {
      "reason_id": 266544,
      "confidence": "High",
      "explanation": "The sales page uses the term 'lifetime access', which is not permitted under our guidelines."
    },
    {
      "reason_id": 266583,
      "confidence": "Medium",
      "explanation": "The product may require ZFU registration due to its structure as a distance learning program."
    }
  ]
}
```

Returns: `201 Created` with `{ "id": <prediction_id> }` or validation errors.

## 🧭 Reviewer Flow

1) Login (Django auth). On success, you are redirected to the oldest unassigned, unreviewed prediction (`claim_next`).
2) Review the AI-proposed reasons:
   - Confirm ✅ or Override ❌ each reason
   - Optional corrected explanation
3) Submit. A `Review` and `ReviewDecision`s are saved, and you are sent to the next item (or a “No more” page).

Dashboard shows remaining items and your assigned count.

## 🗃️ Data Model (simplified)

- `ProductPrediction(product_id, created_at, assigned_to, locked_at, reviewed_at)`
- `RejectionReasonPrediction(product_prediction, reason_id, confidence, explanation)`
- `Review(product_prediction [OneToOne], reviewer, submitted_at, summary_notes)`
- `ReviewDecision(review, reason_prediction, decision, corrected_explanation)`

## 🔐 Authentication

- Case-insensitive username login via custom backend `reviews.auth_backends.CaseInsensitiveModelBackend` configured in `approvaltool/settings.py`.
- `LOGIN_REDIRECT_URL = 'claim_next'` ensures the oldest unassigned prediction is auto-assigned on login.

## 🛠️ Tech

- Django 5.x, SQLite (dev)
- Django REST Framework (ingest endpoint)
- Bootstrap 5 (CDN) for UI

## ⚠️ Notes

- This is a PoC; security and edge cases are minimal by design.
- Do not use in production without hardening.

— Digistore24 AI Team