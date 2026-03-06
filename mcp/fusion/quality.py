"""Quality check: filter results below score threshold, validate min results."""
from typing import List
from shared.config import settings
from shared.schemas import FusedResult


class QualityCheckResult:
    def __init__(self, passed: bool, results: List[FusedResult], warnings: List[str]):
        self.passed = passed
        self.results = results
        self.warnings = warnings


def check_quality(
    results: List[FusedResult],
    min_score: float | None = None,
    min_results: int | None = None,
) -> QualityCheckResult:
    min_score = min_score if min_score is not None else settings.QUALITY_MIN_SCORE
    min_results = min_results if min_results is not None else settings.QUALITY_MIN_RESULTS
    warnings = []

    if not results:
        return QualityCheckResult(passed=False, results=[], warnings=["No results from fusion pipeline"])

    filtered = [r for r in results if r.final_score >= min_score]
    dropped = len(results) - len(filtered)
    if dropped > 0:
        warnings.append(f"Dropped {dropped} results below score threshold {min_score}")

    empty_count = sum(1 for r in filtered if not r.desc_text)
    if empty_count > 0:
        warnings.append(f"{empty_count} results have no description text")

    passed = len(filtered) >= min_results
    if not passed:
        warnings.append(f"Only {len(filtered)} results (minimum: {min_results})")

    return QualityCheckResult(passed=passed, results=filtered, warnings=warnings)
