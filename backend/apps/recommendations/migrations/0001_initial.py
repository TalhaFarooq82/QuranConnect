# apps/recommendations/migrations/0001_initial.py
# Generated migration — run: python manage.py migrate

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # This migration depends on the bookings Proposal model existing first
        ("bookings", "0002_alter_proposal_unique_together_job_awarded_teacher_and_more"),
    ]

    operations = [
        # Create ScoringConfig table
        migrations.CreateModel(
            name="ScoringConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("weight_rating",         models.FloatField(default=0.4,  help_text="Weight for tutor rating score (e.g. 0.40 = 40%)")),
                ("weight_responsiveness", models.FloatField(default=0.35, help_text="Weight for responsiveness score (e.g. 0.35 = 35%)")),
                ("weight_alignment",      models.FloatField(default=0.25, help_text="Weight for subject/budget alignment score (e.g. 0.25 = 25%)")),
                ("active",     models.BooleanField(default=True, help_text="Only one config can be active at a time")),
                ("note",       models.CharField(blank=True, max_length=200, help_text="Optional note: e.g. 'boosted responsiveness for Q2'")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name":        "Scoring configuration",
                "verbose_name_plural": "Scoring configurations",
            },
        ),

        # Create ProposalScore table
        migrations.CreateModel(
            name="ProposalScore",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "proposal",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_score",
                        to="bookings.proposal",
                    ),
                ),
                ("total_score",          models.FloatField(default=0.0)),
                ("rating_score",         models.FloatField(default=0.0)),
                ("responsiveness_score", models.FloatField(default=0.0)),
                ("alignment_score",      models.FloatField(default=0.0)),
                ("is_new_tutor",  models.BooleanField(default=False)),
                ("explanation",   models.TextField(blank=True)),
                ("scored_at",     models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-total_score"],
            },
        ),
    ]
