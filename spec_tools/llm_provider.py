"""LLM provider abstraction for semantic test-adherence analysis."""

import json
import time
from abc import ABC, abstractmethod
from typing import Any

from spec_tools.semantic_test_result import SemanticAnalysisResult


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def analyze_test_requirement(
        self,
        requirement_id: str,
        requirement_text: str,
        test_name: str,
        test_code: str,
        test_docstring: str | None = None,
        context: str | None = None,
    ) -> SemanticAnalysisResult:
        """Analyze whether a test validates a requirement.

        Args:
            requirement_id: Fully qualified requirement ID (SPEC-XXX/REQ-XXX)
            requirement_text: Full text of the requirement
            test_name: Name of the test function
            test_code: Source code of the test function
            test_docstring: Optional docstring from the test
            context: Optional additional context (spec section, related requirements)

        Returns:
            SemanticAnalysisResult with alignment analysis
        """
        pass


class LiteLLMProvider(LLMProvider):
    """LLM provider using LiteLLM for unified provider access.

    Supports multiple backends: groq, anthropic, openai, ollama, vertex_ai, bedrock.
    """

    # Default models for each provider
    DEFAULT_MODELS = {
        "groq": "groq/llama-3.3-70b-versatile",
        "anthropic": "claude-3-5-haiku-20241022",
        "openai": "gpt-4o-mini",
        "ollama": "ollama/llama3.2",
        "vertex_ai": "vertex_ai/claude-3-5-haiku@20241022",
        "bedrock": "bedrock/anthropic.claude-3-5-haiku-20241022-v1:0",
    }

    def __init__(
        self,
        provider: str = "groq",
        model: str | None = None,
        max_retries: int = 3,
        timeout: int = 60,
    ):
        """Initialize LiteLLM provider.

        Args:
            provider: Provider name (groq, anthropic, openai, ollama, etc.)
            model: Model name/version (defaults to provider's default model)
            max_retries: Maximum number of retry attempts (default: 3)
            timeout: Request timeout in seconds (default: 60)
        """
        self.provider = provider
        self.model = model or self.DEFAULT_MODELS.get(provider, "groq/llama-3.3-70b-versatile")
        self.max_retries = max_retries
        self.timeout = timeout

    def analyze_test_requirement(
        self,
        requirement_id: str,
        requirement_text: str,
        test_name: str,
        test_code: str,
        test_docstring: str | None = None,
        context: str | None = None,
    ) -> SemanticAnalysisResult:
        """Analyze whether a test validates a requirement using LLM."""
        # Build the analysis prompt
        prompt = self._build_analysis_prompt(
            requirement_id=requirement_id,
            requirement_text=requirement_text,
            test_name=test_name,
            test_code=test_code,
            test_docstring=test_docstring,
            context=context,
        )

        # Call LLM with retry logic
        for attempt in range(self.max_retries):
            try:
                response = self._call_llm(prompt)
                return self._parse_response(
                    response=response,
                    requirement_id=requirement_id,
                    test_name=test_name,
                )
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Final attempt failed, return error result
                    return SemanticAnalysisResult(
                        requirement_id=requirement_id,
                        test_name=test_name,
                        aligned=False,
                        confidence=0.0,
                        explanation="Analysis failed after all retries",
                        provider_used=self.model,
                        error=str(e),
                    )
                # Exponential backoff: 2^attempt seconds
                time.sleep(2**attempt)

        # Should never reach here, but safety fallback
        return SemanticAnalysisResult(
            requirement_id=requirement_id,
            test_name=test_name,
            aligned=False,
            confidence=0.0,
            explanation="Analysis failed",
            provider_used=self.model,
            error="Maximum retries exceeded",
        )

    def _build_analysis_prompt(
        self,
        requirement_id: str,
        requirement_text: str,
        test_name: str,
        test_code: str,
        test_docstring: str | None = None,
        context: str | None = None,
    ) -> str:
        """Build the analysis prompt for the LLM."""
        prompt_parts = [
            "You are a software testing expert analyzing whether a test validates a requirement.",
            "",
            f"REQUIREMENT ID: {requirement_id}",
            f"REQUIREMENT TEXT: {requirement_text}",
            "",
        ]

        if context:
            prompt_parts.extend([f"CONTEXT: {context}", ""])

        prompt_parts.extend(
            [
                f"TEST NAME: {test_name}",
            ]
        )

        if test_docstring:
            prompt_parts.extend([f"TEST DOCSTRING: {test_docstring}", ""])

        prompt_parts.extend(
            [
                f"TEST CODE:\n{test_code}",
                "",
                "Analyze whether this test validates the requirement behavior.",
                "Consider the following aspects:",
                "1. Does the test validate the ACTION/BEHAVIOR described?",
                "2. Does the test cover the CONDITIONS/TRIGGERS specified?",
                "3. Do the test ASSERTIONS match expected outcomes?",
                "4. Is the test SCOPE appropriate for the requirement?",
                "",
                "Respond in JSON format with:",
                "{",
                '  "aligned": true/false,',
                '  "confidence": 0.0-1.0,',
                '  "explanation": "brief explanation",',
                '  "aspects": {',
                '    "action": true/false,',
                '    "conditions": true/false,',
                '    "assertions": true/false,',
                '    "scope": true/false',
                "  }",
                "}",
            ]
        )

        return "\n".join(prompt_parts)

    def _call_llm(self, prompt: str) -> dict[str, Any]:
        """Call the LLM API using LiteLLM."""
        try:
            import litellm

            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.timeout,
                temperature=0.0,  # Use deterministic responses
            )

            # Extract the response content
            content = response.choices[0].message.content
            return {"content": content}

        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {e}") from e

    def _parse_response(
        self,
        response: dict[str, Any],
        requirement_id: str,
        test_name: str,
    ) -> SemanticAnalysisResult:
        """Parse LLM response into SemanticAnalysisResult."""
        try:
            content = response.get("content", "")

            # Try to extract JSON from the response
            # The LLM might wrap JSON in markdown code blocks
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()

            # Parse JSON response
            parsed = json.loads(json_str)

            return SemanticAnalysisResult(
                requirement_id=requirement_id,
                test_name=test_name,
                aligned=parsed.get("aligned", False),
                confidence=float(parsed.get("confidence", 0.0)),
                explanation=parsed.get("explanation", "No explanation provided"),
                aspects=parsed.get("aspects"),
                provider_used=self.model,
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # If parsing fails, return error result
            return SemanticAnalysisResult(
                requirement_id=requirement_id,
                test_name=test_name,
                aligned=False,
                confidence=0.0,
                explanation="Failed to parse LLM response",
                provider_used=self.model,
                error=f"Parse error: {e}",
            )
