from django.contrib import admin
from .models import ProductPrediction, RejectionReasonPrediction, Review, ReviewDecision


class RejectionReasonPredictionInline(admin.TabularInline):
    model = RejectionReasonPrediction
    extra = 0


@admin.register(ProductPrediction)
class ProductPredictionAdmin(admin.ModelAdmin):
    list_display = ("id", "product_id", "assigned_to", "created_at", "reviewed_at")
    list_filter = ("assigned_to", "reviewed_at")
    search_fields = ("product_id",)
    inlines = [RejectionReasonPredictionInline]


class ReviewDecisionInline(admin.TabularInline):
    model = ReviewDecision
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "product_prediction", "reviewer", "submitted_at")
    inlines = [ReviewDecisionInline]

