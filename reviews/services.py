from __future__ import annotations

from typing import Optional
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import ProductPrediction, RejectionReasonPrediction, Review, ReviewDecision

User = get_user_model()


def claim_oldest_available(user: User) -> Optional[ProductPrediction]:
    """Atomically claim the oldest unassigned, unreviewed prediction for the user.

    Returns the claimed ProductPrediction or None if none is available.
    """
    with transaction.atomic():
        while True:
            candidate_id = (
                ProductPrediction.objects
                .filter(assigned_to__isnull=True, reviewed_at__isnull=True)
                .order_by("created_at")
                .values_list("id", flat=True)
                .first()
            )
            if not candidate_id:
                return None

            updated = (
                ProductPrediction.objects
                .filter(id=candidate_id, assigned_to__isnull=True, reviewed_at__isnull=True)
                .update(assigned_to=user, locked_at=timezone.now())
            )
            if updated:
                return ProductPrediction.objects.get(id=candidate_id)
            # else: someone else claimed it; retry


def ensure_assigned(pred: ProductPrediction, user: User) -> bool:
    """Ensure the given prediction is assigned to the user if possible.

    Returns True if the user is allowed to proceed with this prediction; False otherwise.
    If unassigned, assigns to the user. If assigned to a different user, returns False.
    Does not change reviewed_at.
    """
    if pred.assigned_to is None:
        pred.assigned_to = user
        pred.locked_at = timezone.now()
        pred.save(update_fields=["assigned_to", "locked_at"])
        return True
    if pred.assigned_to_id == user.id:
        return True
    return False


def submit_review(pred: ProductPrediction, user: User, post_data: dict) -> Optional[str]:
    """Validate and persist a review for the given prediction.

    Returns None on success. Returns an error message string if validation fails.
    """
    reasons = list(pred.reasons.all())
    decisions_to_create = []

    # Validate presence of decisions per reason
    for r in reasons:
        decision = post_data.get(f"reason_{r.id}_decision")
        corrected = post_data.get(f"reason_{r.id}_explanation", "")
        if decision not in {"confirmed", "overridden"}:
            return "Please choose a decision for every reason."
        decisions_to_create.append((r, decision, corrected))

    with transaction.atomic():
        review = Review.objects.create(
            product_prediction=pred,
            reviewer=user,
            summary_notes=post_data.get("summary_notes", ""),
        )
        ReviewDecision.objects.bulk_create([
            ReviewDecision(
                review=review,
                reason_prediction=r,
                decision=decision,
                corrected_explanation=corrected,
            )
            for (r, decision, corrected) in decisions_to_create
        ])
        pred.reviewed_at = timezone.now()
        pred.save(update_fields=["reviewed_at"])

    return None
