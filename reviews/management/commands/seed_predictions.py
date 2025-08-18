from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from reviews.models import ProductPrediction, RejectionReasonPrediction, Review, ReviewDecision


class Command(BaseCommand):
    help = "Seed database with demo user(s) and sample predictions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing review data (predictions, reasons, reviews, decisions) before seeding",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        if options.get("reset"):
            # Delete in dependency order
            ReviewDecision.objects.all().delete()
            Review.objects.all().delete()
            RejectionReasonPrediction.objects.all().delete()
            ProductPrediction.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing review data."))
        # Create demo supporter users
        user_specs = [
            ("support", "support123"),
            ("John", "pass123"),
            ("Jane", "pass123"),
            ("Anthony", "pass123"),
        ]
        for uname, pwd in user_specs:
            user, created = User.objects.get_or_create(username=uname)
            # Ensure deterministic password
            user.set_password(pwd)
            user.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created user '{uname}'"))
            else:
                self.stdout.write(f"Updated password for user '{uname}'")

        samples = [
            {
                "product_id": "498589",
                "rejection_reasons": [
                    {
                        "reason_id": 266544,
                        "confidence": "High",
                        "explanation": "The sales page uses the term 'lifetime access', which is not permitted under our guidelines.",
                    },
                    {
                        "reason_id": 266583,
                        "confidence": "Medium",
                        "explanation": "The product may require ZFU registration due to its structure as a distance learning program.",
                    },
                ],
            },
            {
                "product_id": "501234",
                "rejection_reasons": [
                    {
                        "reason_id": 123456,
                        "confidence": "Low",
                        "explanation": "Claimed ROI is not sufficiently substantiated on the sales page.",
                    }
                ],
            },
        ]

        created = 0
        for s in samples:
            if ProductPrediction.objects.filter(product_id=s["product_id"]).exists():
                continue
            pred = ProductPrediction.objects.create(product_id=s["product_id"])
            RejectionReasonPrediction.objects.bulk_create([
                RejectionReasonPrediction(
                    product_prediction=pred,
                    reason_id=item["reason_id"],
                    confidence=item["confidence"],
                    explanation=item.get("explanation", ""),
                )
                for item in s["rejection_reasons"]
            ])
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} product predictions"))
