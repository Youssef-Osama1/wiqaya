from src.core.schemas import RetrievalResult, ThresholdDecision


def evaluate_threshold(retrieval: RetrievalResult, halt_threshold: float, downgrade_threshold: float) -> ThresholdDecision:
    top_score = retrieval.results[0].score if retrieval.results else 0.0

    if top_score < halt_threshold:
        return ThresholdDecision(
            action="HALT", top_score=top_score,
            reason=f"Top retrieval score {top_score:.3f} is below the halt threshold ({halt_threshold}) - insufficient evidence.",
        )

    if top_score < downgrade_threshold:
        return ThresholdDecision(
            action="DOWNGRADE", top_score=top_score,
            reason=f"Top retrieval score {top_score:.3f} is below the downgrade threshold ({downgrade_threshold}) - confidence capped at Low.",
        )

    return ThresholdDecision(action="PROCEED", top_score=top_score, reason=f"Top retrieval score {top_score:.3f} meets confidence thresholds.")
