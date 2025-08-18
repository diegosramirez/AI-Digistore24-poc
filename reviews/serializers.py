from rest_framework import serializers
from .models import ProductPrediction, RejectionReasonPrediction


class RejectionReasonPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RejectionReasonPrediction
        fields = ["reason_id", "confidence", "explanation"]


class ProductPredictionSerializer(serializers.ModelSerializer):
    rejection_reasons = RejectionReasonPredictionSerializer(many=True, write_only=True)

    class Meta:
        model = ProductPrediction
        fields = ["product_id", "rejection_reasons"]

    def create(self, validated_data):
        reasons = validated_data.pop("rejection_reasons", [])
        prediction = ProductPrediction.objects.create(**validated_data)
        objs = [
            RejectionReasonPrediction(
                product_prediction=prediction,
                reason_id=item["reason_id"],
                confidence=item["confidence"],
                explanation=item.get("explanation", ""),
            )
            for item in reasons
        ]
        if objs:
            RejectionReasonPrediction.objects.bulk_create(objs)
        return prediction
