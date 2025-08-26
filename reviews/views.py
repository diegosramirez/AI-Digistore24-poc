import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib.auth import logout
from django.http import Http404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import ProductPrediction, RejectionReasonPrediction, Review, ReviewDecision
from .services import claim_oldest_available, ensure_assigned, submit_review
from .serializers import ProductPredictionSerializer

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
def ingest_prediction(request):
    try:
        serializer = ProductPredictionSerializer(data=request.data)
        if serializer.is_valid():
            prediction = serializer.save()
            logger.info(f"Created prediction {prediction.id} for product {prediction.product_id}")
            return Response({"id": prediction.id}, status=status.HTTP_201_CREATED)
        logger.warning(f"Invalid prediction data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating prediction: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
@transaction.atomic
def claim_next(request):
    # If user already has an assigned but unreviewed prediction, go there first
    existing = (
        ProductPrediction.objects.select_for_update()
        .filter(assigned_to=request.user, reviewed_at__isnull=True)
        .order_by("created_at")
        .first()
    )
    if existing:
        return redirect("review_prediction", pk=existing.pk)

    pred = claim_oldest_available(request.user)
    if not pred:
        return render(request, "reviews/no_more.html")
    return redirect("review_prediction", pk=pred.pk)


@login_required
@transaction.atomic
def review_prediction(request, pk: int):
    pred = get_object_or_404(ProductPrediction.objects.select_for_update(), pk=pk)
    if pred.reviewed_at is not None:
        # Already reviewed, go claim next
        return redirect("claim_next")

    # Only allow assigned reviewer or assign if unassigned
    if not ensure_assigned(pred, request.user):
        # Not allowed to review someone else's task
        return redirect("claim_next")

    reasons = list(pred.reasons.all())

    if request.method == "POST":
        error = submit_review(pred, request.user, request.POST)
        if error:
            context = {"prediction": pred, "reasons": reasons, "error": error}
            return render(request, "reviews/review_form.html", context)
        return redirect("claim_next")

    context = {"prediction": pred, "reasons": reasons}
    return render(request, "reviews/review_form.html", context)


@login_required
def dashboard(request):
    remaining = ProductPrediction.objects.filter(reviewed_at__isnull=True).count()
    my_assigned = ProductPrediction.objects.filter(assigned_to=request.user, reviewed_at__isnull=True).count()
    total = ProductPrediction.objects.count()
    return render(request, "reviews/dashboard.html", {"remaining": remaining, "my_assigned": my_assigned, "total": total})


def logout_view(request):
    """Explicit logout then redirect to login."""
    logout(request)
    return redirect('login')
