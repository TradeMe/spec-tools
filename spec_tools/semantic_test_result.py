"""Result types for semantic test-adherence validation."""

from dataclasses import dataclass


@dataclass
class SemanticAnalysisResult:
    """Result of semantic analysis for a single test-requirement pair.

    Attributes:
        requirement_id: Fully qualified requirement ID (SPEC-XXX/REQ-XXX)
        test_name: Test function name
        aligned: Whether the test validates the requirement behavior
        confidence: Confidence score (0.0 to 1.0)
        explanation: Textual explanation of the analysis
        aspects: Dict of alignment aspects (action, conditions, assertions, scope)
        provider_used: Name of the LLM provider used for analysis
        error: Error message if analysis failed
    """

    requirement_id: str
    test_name: str
    aligned: bool
    confidence: float
    explanation: str
    aspects: dict[str, bool] | None = None
    provider_used: str = ""
    error: str | None = None


@dataclass
class SemanticTestAdherenceResult:
    """Result of semantic test-adherence validation for all test-requirement pairs.

    Attributes:
        total_pairs: Total number of test-requirement pairs analyzed
        aligned_pairs: Number of aligned pairs (above threshold)
        misaligned_pairs: Number of misaligned pairs (below threshold)
        error_pairs: Number of pairs with analysis errors
        analyses: List of individual SemanticAnalysisResult objects
        threshold: Confidence threshold used for alignment
        is_valid: Whether all pairs are aligned
    """

    total_pairs: int
    aligned_pairs: int
    misaligned_pairs: int
    error_pairs: int
    analyses: list[SemanticAnalysisResult]
    threshold: float
    is_valid: bool

    @property
    def alignment_percentage(self) -> float:
        """Calculate overall alignment percentage."""
        if self.total_pairs == 0:
            return 100.0
        return (self.aligned_pairs / self.total_pairs) * 100

    def __str__(self) -> str:
        """Format the result as a human-readable string."""
        lines = []
        lines.append("=" * 60)
        lines.append("SEMANTIC TEST-ADHERENCE REPORT")
        lines.append("=" * 60)
        lines.append(f"Total pairs analyzed: {self.total_pairs}")
        lines.append(f"Aligned: {self.aligned_pairs}")
        lines.append(f"Misaligned: {self.misaligned_pairs}")
        lines.append(f"Errors: {self.error_pairs}")
        lines.append(f"Alignment: {self.alignment_percentage:.1f}%")
        lines.append(f"Threshold: {self.threshold}")
        lines.append("")

        # Show misaligned pairs
        misaligned = [a for a in self.analyses if not a.aligned and a.error is None]
        if misaligned:
            lines.append("❌ Misaligned Test-Requirement Pairs:")
            for analysis in misaligned:
                lines.append(f"  - {analysis.requirement_id} ← {analysis.test_name}")
                lines.append(f"    Confidence: {analysis.confidence:.2f}")
                lines.append(f"    {analysis.explanation}")
            lines.append("")

        # Show error pairs
        error_analyses = [a for a in self.analyses if a.error is not None]
        if error_analyses:
            lines.append("⚠️  Analysis Errors:")
            for analysis in error_analyses:
                lines.append(f"  - {analysis.requirement_id} ← {analysis.test_name}")
                lines.append(f"    Error: {analysis.error}")
            lines.append("")

        if self.is_valid:
            lines.append("✅ Semantic test-adherence validation PASSED")
        else:
            lines.append("❌ Semantic test-adherence validation FAILED")

        lines.append("=" * 60)
        return "\n".join(lines)
