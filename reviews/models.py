from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class ProductPrediction(models.Model):
    product_id = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # assignment/locking
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_predictions')
    locked_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Prediction for product {self.product_id}"


class RejectionReasonPrediction(models.Model):
    CONF_CHOICES = (
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    )
    product_prediction = models.ForeignKey(ProductPrediction, on_delete=models.CASCADE, related_name='reasons')
    reason_id = models.IntegerField()
    confidence = models.CharField(max_length=16, choices=CONF_CHOICES)
    explanation = models.TextField()

    def __str__(self):
        return f"Reason {self.reason_id} ({self.confidence})"


class Review(models.Model):
    product_prediction = models.OneToOneField(ProductPrediction, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    summary_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Review of {self.product_prediction} by {self.reviewer}"


class ReviewDecision(models.Model):
    DECISION_CHOICES = (
        ('confirmed', 'Confirmed'),
        ('overridden', 'Overridden'),
    )
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='decisions')
    reason_prediction = models.ForeignKey(RejectionReasonPrediction, on_delete=models.CASCADE)
    decision = models.CharField(max_length=16, choices=DECISION_CHOICES)
    corrected_explanation = models.TextField(blank=True)

    def __str__(self):
        return f"Decision {self.decision} on reason {self.reason_prediction.reason_id}"
