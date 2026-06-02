# ============================================================
# apps/recommendations/services.py
#
# This file is the "glue" between the scorer and the database.
#
# The scorer (scorer.py) just does math — it doesn't touch the DB.
# This service calls the scorer AND saves results to ProposalScore.
#
# Your views just call: get_ranked_proposals(job)
# and get back a ready-to-use list for the template.
# ============================================================

from apps.bookings.models import Proposal, Conversation
from .scorer import TutorRecommender
from .models import ProposalScore


def get_ranked_proposals(job):
    """
    The main function your view will call.

    Takes a Job object, returns a list of dicts, each containing:
      {
        "proposal":  <Proposal object>,
        "score":     <ProposalScore object>,
        "conversation": <Conversation or None>,
      }

    The list is sorted best-first (highest AI score at the top).

    Example usage in views.py:
        from apps.recommendations.services import get_ranked_proposals
        ranked = get_ranked_proposals(job)
        return render(request, "template.html", {"ranked": ranked})
    """

    # Get all pending AND awarded proposals for this job
    # (we show all of them, not just pending ones)
    proposals = (
        Proposal.objects
        .filter(job=job)
        .select_related("teacher")   # avoids N+1 queries
        .order_by("-created_at")
    )

    if not proposals.exists():
        return []

    # Run the AI scorer on all proposals
    recommender = TutorRecommender(job)
    scored_list = recommender.rank_proposals(proposals)

    # Save each score to the database (so it's cached for future loads)
    _save_scores_to_db(scored_list)

    # Build the final list with proposal + score + conversation all together
    result = []
    for tutor_score in scored_list:
        proposal = proposals.get(id=tutor_score.proposal_id)

        # Check if a conversation already exists for this teacher+job
        conversation = Conversation.objects.filter(
            job=job,
            teacher=proposal.teacher,
        ).first()

        result.append({
            "proposal":     proposal,
            "score":        _get_cached_score(tutor_score.proposal_id),
            "conversation": conversation,
        })

    return result


def _save_scores_to_db(scored_list):
    """
    Saves or updates the ProposalScore for each proposal.
    Uses update_or_create so running it multiple times is safe.
    """
    for ts in scored_list:
        ProposalScore.objects.update_or_create(
            proposal_id=ts.proposal_id,
            defaults={
                "total_score":          ts.total_score,
                "rating_score":         ts.rating_score,
                "responsiveness_score": ts.responsiveness_score,
                "alignment_score":      ts.alignment_score,
                "is_new_tutor":         ts.is_new_tutor,
                "explanation":          ts.explanation,
            }
        )


def _get_cached_score(proposal_id):
    """Fetches the ProposalScore we just saved, for use in the template."""
    try:
        return ProposalScore.objects.get(proposal_id=proposal_id)
    except ProposalScore.DoesNotExist:
        return None
