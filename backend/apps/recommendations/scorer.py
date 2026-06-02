# ============================================================
# apps/recommendations/scorer.py
#
# This is the BRAIN of the recommendation system.
# It reads tutor data and produces a score from 0.0 to 1.0.
#
# HOW IT WORKS (simple explanation):
#   Each tutor proposal gets scored on 3 things:
#     1. Rating      — how good are their reviews?
#     2. Responsiveness — how quickly do they reply?
#     3. Alignment   — do they match what the student needs?
#
#   These 3 scores are combined using weights:
#     final_score = (0.40 × rating) + (0.35 × responsiveness) + (0.25 × alignment)
#
#   Proposals are then sorted from highest score to lowest.
# ============================================================

import math
from dataclasses import dataclass, field


# -------------------------------------------------------
# TutorScore: a simple container that holds all the scores
# for ONE proposal. Think of it like a report card.
# -------------------------------------------------------
@dataclass
class TutorScore:
    proposal_id: int          # which proposal this belongs to
    teacher_id: int           # which teacher
    total_score: float        # final combined score (0.0 to 1.0)
    rating_score: float       # score from ratings/reviews (0.0 to 1.0)
    responsiveness_score: float  # score from reply speed (0.0 to 1.0)
    alignment_score: float    # score from subject/budget match (0.0 to 1.0)
    is_new_tutor: bool        # True if teacher has < 3 awarded jobs
    explanation: str          # human-readable sentence shown to student


# -------------------------------------------------------
# TutorRecommender: the class that does all the work.
# You create one per job, then call rank_proposals().
# -------------------------------------------------------
class TutorRecommender:

    # --- Default weights (must add up to 1.0) ---
    # These control how much each signal matters.
    # You can change them in Django Admin without touching this file.
    DEFAULT_WEIGHT_RATING         = 0.40
    DEFAULT_WEIGHT_RESPONSIVENESS = 0.35
    DEFAULT_WEIGHT_ALIGNMENT      = 0.25

    # --- Cold-start settings ---
    # When a new teacher has no reviews, we don't give them 0 stars.
    # Instead we assume they are "average" until proven otherwise.
    # This is called a Bayesian prior.
    PLATFORM_AVG_RATING  = 4.0   # assumed rating for brand-new teachers
    BAYESIAN_PRIOR_COUNT = 3     # acts like 3 "ghost" reviews at the average

    # Teachers with fewer than this many awarded jobs get a small boost
    # so they appear near the top and get a chance to earn real reviews.
    NEW_TUTOR_THRESHOLD = 3
    NEW_TUTOR_BOOST     = 0.06   # adds 6% to their final score

    def __init__(self, job):
        """
        job: the Job model instance the student posted.
        We store it so all the scoring methods can access it.
        """
        self.job = job
        self.weights = self._load_weights()

    # -------------------------------------------------------
    # STEP 1: Load weights from DB (or use defaults)
    # -------------------------------------------------------
    def _load_weights(self):
        """
        Tries to load custom weights from the ScoringConfig table.
        If none exist yet, uses the DEFAULT values above.
        This lets you tune the algorithm from Django Admin.
        """
        try:
            from .models import ScoringConfig
            config = ScoringConfig.objects.filter(active=True).latest("updated_at")
            return {
                "rating":         config.weight_rating,
                "responsiveness": config.weight_responsiveness,
                "alignment":      config.weight_alignment,
            }
        except Exception:
            # No config in DB yet — use code defaults
            return {
                "rating":         self.DEFAULT_WEIGHT_RATING,
                "responsiveness": self.DEFAULT_WEIGHT_RESPONSIVENESS,
                "alignment":      self.DEFAULT_WEIGHT_ALIGNMENT,
            }

    # -------------------------------------------------------
    # MAIN PUBLIC METHOD: Call this from your view
    # -------------------------------------------------------
    def rank_proposals(self, proposals):
        """
        Takes a list/queryset of Proposal objects for one job.
        Returns a list of TutorScore objects, sorted best-first.

        Usage in view:
            recommender = TutorRecommender(job)
            ranked = recommender.rank_proposals(job.proposals.all())
        """
        scored_list = [self._score_one_proposal(p) for p in proposals]
        # Sort: highest score first
        scored_list.sort(key=lambda s: s.total_score, reverse=True)
        return scored_list

    # -------------------------------------------------------
    # STEP 2: Score a single proposal
    # -------------------------------------------------------
    def _score_one_proposal(self, proposal) -> TutorScore:
        """
        Calculates all 3 sub-scores for one proposal, then combines them.
        """
        teacher = proposal.teacher

        # Calculate each sub-score (each returns 0.0 to 1.0)
        r_score  = self._rating_score(proposal)
        rs_score = self._responsiveness_score(teacher)
        al_score = self._alignment_score(proposal)

        # Check if this is a new teacher who needs a visibility boost
        new_tutor = self._is_new_tutor(teacher)
        boost = self.NEW_TUTOR_BOOST if new_tutor else 0.0

        # Combine everything using weights
        w = self.weights
        total = (
            w["rating"]         * r_score  +
            w["responsiveness"] * rs_score +
            w["alignment"]      * al_score +
            boost
        )

        # Make sure we never go above 1.0 (100%)
        total = min(total, 1.0)

        return TutorScore(
            proposal_id          = proposal.id,
            teacher_id           = teacher.id,
            total_score          = round(total, 4),
            rating_score         = round(r_score, 4),
            responsiveness_score = round(rs_score, 4),
            alignment_score      = round(al_score, 4),
            is_new_tutor         = new_tutor,
            explanation          = self._build_explanation(r_score, rs_score, al_score, new_tutor),
        )

    # -------------------------------------------------------
    # SUB-SCORE 1: Rating
    # -------------------------------------------------------
    def _rating_score(self, proposal) -> float:
        """
        Uses the rating and reviews already stored on the Proposal model.

        Your Proposal model has:
            rating  = DecimalField (e.g. 4.9)
            reviews = IntegerField (e.g. 12)

        COLD-START PROBLEM:
            If a new teacher has 0 reviews, their rating field defaults to 4.9
            (set in your job_detail view). But we can't fully trust that
            because it's not earned yet.

            We use Bayesian smoothing:
            - Imagine the teacher has 3 "ghost" reviews at 4.0 (platform avg)
            - As real reviews accumulate, the ghost ones matter less
            - Formula: (real_reviews * real_rating + ghost_count * avg) / (real_reviews + ghost_count)

        Example:
            New teacher (0 reviews):  (0*4.9 + 3*4.0) / (0+3) = 4.0  → score = 0.80
            Experienced (10 reviews): (10*4.8 + 3*4.0) / (10+3) = 4.62 → score = 0.92
        """
        raw_rating  = float(proposal.rating or self.PLATFORM_AVG_RATING)
        review_count = int(proposal.reviews or 0)

        k = self.BAYESIAN_PRIOR_COUNT
        prior = self.PLATFORM_AVG_RATING

        # Bayesian average: blends real rating with platform average
        bayesian_avg = (review_count * raw_rating + k * prior) / (review_count + k)

        # Convert 0-5 star scale to 0.0-1.0 score
        return bayesian_avg / 5.0

    # -------------------------------------------------------
    # SUB-SCORE 2: Responsiveness
    # -------------------------------------------------------
    def _responsiveness_score(self, teacher) -> float:
        """
        Measures how actively the teacher has engaged on the platform.
        We look at two things:

        1. Proposal response rate: Out of all jobs they bid on,
           how many got a response (awarded or rejected)?
           - If they submit proposals but never follow up = low score
           - Formula: awarded_or_rejected / total_proposals

        2. Message activity: Did they send messages after being awarded?
           - Uses the Message model from bookings app
           - More messages sent = higher engagement

        For brand-new teachers (no history), we return 0.5 (neutral).
        This is fair — we don't punish them for having no history.
        """
        from apps.bookings.models import Proposal, Message

        # --- Part 1: Proposal response rate ---
        all_proposals = Proposal.objects.filter(teacher=teacher)
        total = all_proposals.count()

        if total == 0:
            # Brand new teacher — no proposals yet, give neutral score
            return 0.5

        # Count proposals that moved past "Pending" (teacher was engaged)
        responded = all_proposals.filter(status__in=["Awarded", "Rejected"]).count()
        response_rate = responded / total  # e.g. 0.75 = responded to 75%

        # --- Part 2: Message activity ---
        total_messages_sent = Message.objects.filter(sender=teacher).count()

        # Scale: 0 messages = 0.0, 10+ messages = 1.0
        # math.log1p(x) = natural log of (1+x), grows fast at first then slows
        message_score = min(math.log1p(total_messages_sent) / math.log1p(10), 1.0)

        # Combine: response rate matters more (60%) than message count (40%)
        return 0.60 * response_rate + 0.40 * message_score

    # -------------------------------------------------------
    # SUB-SCORE 3: Alignment
    # -------------------------------------------------------
    def _alignment_score(self, proposal) -> float:
        """
        Measures how well this specific proposal matches the job's needs.
        We check 2 things:

        1. Budget fit  (60% of alignment score)
           Does the teacher's hourly rate fit in the student's budget range?

        2. Cover letter quality  (40% of alignment score)
           Does the proposal_text mention the course/subject keywords?

        Both sub-scores are 0.0 to 1.0 and combined into one alignment score.
        """
        budget_score  = self._budget_fit(proposal)
        keyword_score = self._keyword_match(proposal)

        return 0.60 * budget_score + 0.40 * keyword_score

    def _budget_fit(self, proposal) -> float:
        """
        Compares the teacher's rate against the student's budget.

        Your Job model stores budget as a string like: "$5 - $15 / hr"
        We parse out the numbers and check if the teacher's rate fits.

        Scoring rules:
          - Rate is inside the budget range → high score (0.7 to 1.0)
          - Rate is below the minimum → 0.65 (might be low quality)
          - Rate is above the maximum → penalty based on how far over
          - Budget couldn't be parsed → 0.5 (neutral, no penalty)
        """
        import re

        budget_str = self.job.budget or ""
        # Extract all numbers from the budget string
        # e.g. "$5 - $15 / hr"  →  ['5', '15']
        numbers = re.findall(r'\d+(?:\.\d+)?', budget_str)

        if len(numbers) < 2:
            # Budget wasn't in a parseable format — give neutral score
            return 0.5

        budget_min = float(numbers[0])
        budget_max = float(numbers[1])

        # Try to parse the teacher's hourly rate
        # It's stored as a string like "10" or "PKR 500"
        rate_numbers = re.findall(r'\d+(?:\.\d+)?', str(proposal.hourly_rate or "0"))
        if not rate_numbers:
            return 0.5

        rate = float(rate_numbers[0])

        if rate == 0:
            return 0.5

        if budget_min <= rate <= budget_max:
            # Teacher's rate is within range.
            # Give extra credit for being closer to the midpoint.
            midpoint  = (budget_min + budget_max) / 2
            half_range = (budget_max - budget_min) / 2 or 1
            # Closer to midpoint = higher score (0.7 to 1.0)
            return 1.0 - (abs(rate - midpoint) / half_range) * 0.30

        elif rate < budget_min:
            # Too cheap — slight concern, but not a dealbreaker
            return 0.65

        else:
            # Over budget — penalise proportionally
            # e.g. 20% over budget → score of 0.67
            overshoot_ratio = (rate - budget_max) / budget_max
            return max(0.0, 1.0 - overshoot_ratio)

    def _keyword_match(self, proposal) -> float:
        """
        Checks if the proposal cover letter mentions the job's course/subject.
        This is a simple but effective way to measure relevance.

        Example:
          Job course: "Quran Tajweed"
          Proposal text: "I have 5 years teaching Tajweed and Hifz..."
          → Words "tajweed" found → score = 0.75

        We split the course name into individual words and count matches.
        """
        if not proposal.proposal_text:
            return 0.3  # No cover letter = low score

        proposal_lower = proposal.proposal_text.lower()
        job_course     = (self.job.course or "").lower()
        job_title      = (self.job.title or "").lower()

        # Split course name into individual words to match any of them
        # e.g. "Quran Tajweed" → ["quran", "tajweed"]
        keywords = set(
            word for word in (job_course + " " + job_title).split()
            if len(word) > 2  # ignore tiny words like "of", "in"
        )

        if not keywords:
            return 0.5  # No keywords to match against

        # Count how many keywords appear in the proposal text
        matched = sum(1 for kw in keywords if kw in proposal_lower)
        match_ratio = matched / len(keywords)

        # Scale: 0 matches = 0.30, all match = 1.0
        return 0.30 + 0.70 * match_ratio

    # -------------------------------------------------------
    # HELPER: Is this teacher new to the platform?
    # -------------------------------------------------------
    def _is_new_tutor(self, teacher) -> bool:
        """
        Returns True if the teacher has fewer than NEW_TUTOR_THRESHOLD
        awarded jobs. These teachers get a small score boost to make
        them visible so they can earn their first real reviews.
        """
        from apps.bookings.models import Proposal
        awarded_count = Proposal.objects.filter(
            teacher=teacher,
            status="Awarded"
        ).count()
        return awarded_count < self.NEW_TUTOR_THRESHOLD

    # -------------------------------------------------------
    # HELPER: Build a human-readable explanation
    # -------------------------------------------------------
    def _build_explanation(self, r_score, rs_score, al_score, is_new) -> str:
        """
        Creates a one-sentence explanation shown below each proposal card.
        Students see WHY a tutor ranked where they did.
        """
        parts = []

        if r_score >= 0.85:
            parts.append("highly rated")
        elif r_score >= 0.70:
            parts.append("well rated")

        if rs_score >= 0.80:
            parts.append("very responsive")
        elif rs_score >= 0.60:
            parts.append("reasonably responsive")

        if al_score >= 0.75:
            parts.append("strong subject match")
        elif al_score >= 0.50:
            parts.append("good subject match")

        if is_new:
            parts.append("new to platform (boosted for visibility)")

        if parts:
            return "This tutor is " + ", ".join(parts) + "."
        return "Scored based on rating, responsiveness, and alignment."
