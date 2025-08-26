from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import ProductPrediction, RejectionReasonPrediction, Review, ReviewDecision
from .services import claim_oldest_available, ensure_assigned, submit_review


User = get_user_model()


class ServiceTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username="john", password="x")
        self.u2 = User.objects.create_user(username="jane", password="x")
        # Create two predictions with ordered created_at
        self.p1 = ProductPrediction.objects.create(product_id="A")
        self.p2 = ProductPrediction.objects.create(product_id="B")
        # Attach reasons
        RejectionReasonPrediction.objects.create(product_prediction=self.p1, reason_id=1, confidence="High", explanation="e1")
        RejectionReasonPrediction.objects.create(product_prediction=self.p2, reason_id=2, confidence="Medium", explanation="e2")

    def test_claim_oldest_available_in_order(self):
        a = claim_oldest_available(self.u1)
        b = claim_oldest_available(self.u2)
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertEqual(a.id, self.p1.id)
        self.assertEqual(b.id, self.p2.id)
        # No more left
        c = claim_oldest_available(self.u1)
        self.assertIsNone(c)

    def test_ensure_assigned(self):
        # Unassigned becomes assigned to u1
        ok = ensure_assigned(self.p1, self.u1)
        self.assertTrue(ok)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.assigned_to_id, self.u1.id)
        # Different user cannot take it
        ok2 = ensure_assigned(self.p1, self.u2)
        self.assertFalse(ok2)

    def test_submit_review_success_and_validation(self):
        # Assign and prepare post data
        ensure_assigned(self.p1, self.u1)
        r = list(self.p1.reasons.all())[0]
        post_data = {
            f"reason_{r.id}_decision": "confirmed",
            f"reason_{r.id}_explanation": "ok",
            "summary_notes": "done",
        }
        err = submit_review(self.p1, self.u1, post_data)
        self.assertIsNone(err)
        self.p1.refresh_from_db()
        self.assertIsNotNone(self.p1.reviewed_at)
        self.assertTrue(Review.objects.filter(product_prediction=self.p1, reviewer=self.u1).exists())
        self.assertTrue(ReviewDecision.objects.filter(reason_prediction=r).exists())

        # Validation: missing decision
        p = ProductPrediction.objects.create(product_id="C")
        RejectionReasonPrediction.objects.create(product_prediction=p, reason_id=3, confidence="Low", explanation="e3")
        ensure_assigned(p, self.u2)
        err2 = submit_review(p, self.u2, {"summary_notes": "x"})
        self.assertIsInstance(err2, str)
