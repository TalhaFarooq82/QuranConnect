# ============================================================
# apps/recommendations/models.py
#
# Two models live here:
#
#   1. ScoringConfig  — lets admin change algorithm weights
#                       from Django Admin without touching code
#
#   2. ProposalScore  — stores the calculated score for each proposal
#                       so the page loads fast (no re-calculation on every visit)
# ============================================================

from django.db import models


class ScoringConfig(models.Model):
    """
    Stores the weights used by the scoring algorithm.
    You can change these from Django Admin at any time.

    RULE: All three weights should add up to 1.0.
    Example: rating=0.40, responsiveness=0.35, alignment=0.25 → sum = 1.0

    Only ONE row should have active=True at a time.
    When you save a new active config, old ones are automatically deactivated.
    """

    # The three weights — how much each signal matters
    weight_rating         = models.FloatField(
        default=0.40,
        help_text="Weight for tutor rating score (e.g. 0.40 = 40%)"
    )
    weight_responsiveness = models.FloatField(
        default=0.35,
        help_text="Weight for responsiveness score (e.g. 0.35 = 35%)"
    )
    weight_alignment      = models.FloatField(
        default=0.25,
        help_text="Weight for subject/budget alignment score (e.g. 0.25 = 25%)"
    )

    active     = models.BooleanField(
        default=True,
        help_text="Only one config can be active at a time"
    )
    note       = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional note: e.g. 'boosted responsiveness for Q2'"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Scoring configuration"
        verbose_name_plural = "Scoring configurations"

    def __str__(self):
        return (
            f"Config: rating={self.weight_rating}, "
            f"response={self.weight_responsiveness}, "
            f"align={self.weight_alignment} "
            f"({'ACTIVE' if self.active else 'inactive'})"
        )

    def save(self, *args, **kwargs):
        # When this config is set to active, deactivate all others.
        # This ensures only one config is ever active at a time.
        if self.active:
            ScoringConfig.objects.exclude(pk=self.pk).update(active=False)
        super().save(*args, **kwargs)


class ProposalScore(models.Model):
    """
    Stores the AI-calculated score for each proposal.

    WHY cache it here?
      The scoring calculation touches multiple database tables.
      If you recalculate on every page load, it will be slow.
      Instead, we calculate once and store the result here.
      The score is refreshed whenever a proposal is updated.

    This table is linked one-to-one with Proposal:
      one proposal → one score row
    """

    proposal = models.OneToOneField(
        "bookings.Proposal",       # links to your existing Proposal model
        on_delete=models.CASCADE,  # if proposal deleted, delete score too
        related_name="ai_score"    # lets you do: proposal.ai_score.total_score
    )

    # The main combined score (0.0 to 1.0)
    total_score = models.FloatField(default=0.0)

    # Individual sub-scores (also 0.0 to 1.0 each)
    rating_score         = models.FloatField(default=0.0)
    responsiveness_score = models.FloatField(default=0.0)
    alignment_score      = models.FloatField(default=0.0)

    # Whether this teacher got a new-tutor boost
    is_new_tutor = models.BooleanField(default=False)

    # Human-readable sentence explaining the score
    explanation = models.TextField(blank=True)

    # When was this score last calculated?
    scored_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Default ordering: highest score first
        ordering = ["-total_score"]

    def __str__(self):
        return f"Score {self.total_score:.2f} for Proposal #{self.proposal_id}"

    def score_as_percent(self):
        """Returns the score as a 0-100 integer for easy display in templates."""
        return int(self.total_score * 100)

    def rating_as_percent(self):
        return int(self.rating_score * 100)

    def responsiveness_as_percent(self):
        return int(self.responsiveness_score * 100)

    def alignment_as_percent(self):
        return int(self.alignment_score * 100)
