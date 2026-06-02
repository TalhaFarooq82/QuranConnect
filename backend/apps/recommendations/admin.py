# ============================================================
# apps/recommendations/admin.py
#
# Registers our models with Django Admin so you can:
#   - Tune scoring weights at /admin/recommendations/scoringconfig/
#   - View all calculated scores at /admin/recommendations/proposalscore/
# ============================================================

from django.contrib import admin
from .models import ScoringConfig, ProposalScore


@admin.register(ScoringConfig)
class ScoringConfigAdmin(admin.ModelAdmin):
    """
    Admin panel for tuning the AI weights.
    Go to: /admin/recommendations/scoringconfig/add/
    to create a new config with different weights.
    """

    list_display = [
        "id",
        "weight_rating",
        "weight_responsiveness",
        "weight_alignment",
        "active",
        "updated_at",
        "note",
    ]

    # These fields can be edited directly from the list view
    list_editable = ["weight_rating", "weight_responsiveness", "weight_alignment"]

    # Show a warning if weights don't add up to 1.0
    def save_model(self, request, obj, form, change):
        total = obj.weight_rating + obj.weight_responsiveness + obj.weight_alignment
        if abs(total - 1.0) > 0.01:
            from django.contrib import messages as django_messages
            django_messages.warning(
                request,
                f"⚠️ Weights sum to {total:.2f}, not 1.0. "
                "Scores may be inaccurate. Recommended: they sum to exactly 1.0."
            )
        super().save_model(request, obj, form, change)


@admin.register(ProposalScore)
class ProposalScoreAdmin(admin.ModelAdmin):
    """
    Read-only view of all calculated scores.
    Useful for debugging and monitoring the algorithm.
    """

    list_display = [

        "proposal",
        "total_score",
        "rating_score",
        "responsiveness_score",
        "alignment_score",
        "is_new_tutor",
        "scored_at",
    ]

    # Don't allow editing scores manually — they are calculated by the algorithm
    readonly_fields = [
        "proposal",
        "total_score",
        "rating_score",
        "responsiveness_score",
        "alignment_score",
        "is_new_tutor",
        "explanation",
        "scored_at",
    ]

    ordering = ["-total_score"]
