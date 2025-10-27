# Technical Note: LLM Provider Selection for Semantic Test Adherence

**Date**: 2025-10-23
**Author**: Claude (AI Assistant)
**Status**: Draft
**Related**: Milestone 001 - Semantic Test Adherence (SPEC-003)

## Executive Summary

This technical note evaluates LLM provider options and integration libraries for implementing the semantic test adherence checker (SPEC-003). The analysis focuses on:

1. **Free-tier options for GitHub Actions** (primary: Groq)
2. **Production-grade providers** (Anthropic via native API, Vertex AI, Bedrock)
3. **Integration library selection** (LiteLLM vs. direct SDKs)

**Recommendation**: Use **LiteLLM** as the primary integration library with support for:
- Groq (free tier) for CI/CD in GitHub Actions
- Anthropic Claude (native API, Vertex AI, Bedrock) for production use
- OpenAI as optional fallback provider

This approach provides maximum flexibility, built-in retry/fallback logic, and a unified API surface while supporting both cost-effective CI/CD and enterprise deployment scenarios.

## Requirements Context

From SPEC-003, the semantic test adherence checker must:

- **REQ-021**: Support multiple AI/LLM backends
- **REQ-022**: Support Anthropic Claude (via API), OpenAI GPT, and local models (Ollama)
- **REQ-023**: Accept API key/authentication configuration
- **REQ-024**: Retry up to 3 times with exponential backoff on API failures
- **REQ-040**: Read API keys from environment variables
- **REQ-041**: Support concurrent LLM requests (default: 5)
- **REQ-042**: Cache results to avoid re-analyzing unchanged code

The tool will analyze requirement-test pairs to verify semantic alignment, requiring:
- Robust error handling for API failures
- Cost-effective operation in CI/CD (GitHub Actions)
- Support for enterprise deployment scenarios
- Ability to handle 100+ test-requirement pairs efficiently

## Provider Analysis

### 1. Groq - Free Tier for GitHub Actions

**Overview**: Groq provides extremely fast inference using their custom Language Processing Units (LPUs).

**Free Tier Limits (2025)**:
- **30 requests/minute (RPM)**
- **1,000 requests/day (RPD)**
- **6,000 tokens/minute (TPM)**

**Available Models**:
- Llama 3.3 70B (versatile, good reasoning)
- Mixtral 8x7B (fast, multilingual)
- Gemma 2 9B (efficient, smaller context)

**Pros**:
- Completely free for reasonable CI/CD usage
- Extremely fast inference (often <1 second)
- OpenAI-compatible API
- No credit card required
- Active development and good documentation

**Cons**:
- Rate limits may be restrictive for large test suites
- Free tier limits shared across organization
- No Anthropic Claude models
- Less sophisticated reasoning than Claude/GPT-4

**GitHub Actions Viability**:
✅ **Excellent** - 1,000 requests/day is sufficient for most CI/CD workflows. For a test suite with 100 requirement-test pairs, you could run checks 10 times per day within free limits.

**Estimation**: At 6,000 TPM with average 500 tokens per analysis (requirement text + test code + response), you can analyze ~12 pairs per minute, or ~100 pairs in under 10 minutes with sequential processing. With concurrent requests (5), this drops to ~2 minutes.

### 2. Anthropic Claude - Production Grade

Anthropic offers Claude models through three access methods:

#### 2.1 Native Anthropic API

**Models (2025)**:
- Claude Opus 4: Most powerful, best coding model (SWE-bench leader)
- Claude Sonnet 4.5: Balanced performance, excellent for agents
- Claude Haiku 4.5: Fast, cost-effective

**Pricing**:
- Opus 4: $15/$75 per million tokens (input/output)
- Sonnet 4: $3/$15 per million tokens
- Haiku 4.5: $1/$5 per million tokens (90% savings with prompt caching)

**Pros**:
- Latest models and features immediately available
- Prompt caching for cost optimization
- Excellent reasoning and code understanding
- Direct support from Anthropic
- Simple authentication (API key)

**Cons**:
- Costs money (no free tier for API)
- Requires Anthropic account and billing setup

#### 2.2 Google Cloud Vertex AI

**Overview**: Access Claude models through Google Cloud's Vertex AI platform.

**Pros**:
- FedRAMP High compliance (government/enterprise)
- Integration with Google Cloud ecosystem
- No separate Anthropic account needed
- Managed infrastructure (no provisioning needed)
- Google Cloud billing and cost management

**Cons**:
- Requires Google Cloud account
- May have slightly higher latency than native API
- Potential delays in new model availability
- More complex authentication (service accounts, IAM)

**Best For**: Organizations already on Google Cloud, government/regulated industries

#### 2.3 AWS Bedrock

**Overview**: Access Claude models through Amazon Bedrock.

**Pros**:
- Integration with AWS ecosystem
- No separate Anthropic account needed
- AWS billing and governance
- Multi-region availability
- Compliance certifications (HIPAA, SOC 2, etc.)

**Cons**:
- Requires AWS account and Bedrock access
- May have slightly higher latency than native API
- Potential delays in new model availability
- More complex authentication (IAM roles, credentials)

**Best For**: Organizations already on AWS, enterprise deployments requiring AWS compliance

### 3. OpenAI - Optional Fallback

**Models**: GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo

**Pricing** (approximate):
- GPT-4o: $5/$15 per million tokens
- GPT-3.5 Turbo: $0.50/$1.50 per million tokens

**Pros**:
- Widely adopted, well-documented
- Good reasoning capabilities
- Competitive pricing
- OpenAI-native SDK

**Cons**:
- No free tier
- May not be preferred for some organizations (data privacy concerns)

**Recommendation**: Support as optional provider for flexibility, but not primary focus.

## Integration Library Analysis

### Option 1: LiteLLM (Recommended)

**Overview**: Universal LLM gateway providing unified API for 100+ LLM providers.

**Key Features**:
- OpenAI-compatible interface for all providers
- Built-in retry logic with exponential backoff
- Automatic fallback across providers
- Load balancing and routing
- Exception mapping (all exceptions inherit from OpenAI types)
- Active development (latest release: October 2025)

**Supported Providers**:
- Anthropic (native API, Vertex AI, Bedrock)
- OpenAI
- Groq
- Ollama (local models)
- 100+ other providers

**Example Usage**:

```python
from litellm import completion

# Works with any provider
response = completion(
    model="claude-3-7-sonnet-20250219",  # or "groq/llama-3.3-70b"
    messages=[{"role": "user", "content": "Analyze this test..."}],
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    num_retries=3,
    timeout=30.0
)
```

**Pros**:
- Single unified interface for all providers
- Built-in retry/fallback (satisfies REQ-024)
- Provider-agnostic error handling
- Cost tracking and routing capabilities
- Well-maintained, active community
- Can use OpenAI SDK patterns

**Cons**:
- Abstraction layer adds slight complexity
- May not support bleeding-edge provider features immediately
- Some Anthropic-specific beta features may not forward correctly (e.g., special headers)

**Python Requirements**: Python >=3.8, MIT licensed

**Recommendation**: ✅ **Primary choice** - Best balance of flexibility, features, and ease of use.

### Option 2: Direct Provider SDKs

**Overview**: Use official SDKs from each provider.

**Anthropic SDK Example**:

```python
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Analyze this test..."}]
)
```

**Groq SDK Example** (OpenAI-compatible):

```python
import openai

client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Analyze this test..."}]
)
```

**Pros**:
- Most direct access to provider features
- No abstraction layer
- Latest features immediately available
- Official support

**Cons**:
- Different API for each provider (more code complexity)
- Must implement retry/fallback logic manually (REQ-024)
- Must handle provider-specific exceptions
- More maintenance burden

**Recommendation**: ⚠️ Consider only if LiteLLM limitations are blockers, or for accessing cutting-edge features.

### Option 3: OpenAI SDK Compatibility Mode

**Overview**: Both Anthropic and Groq offer OpenAI SDK compatibility.

**Anthropic OpenAI Compatibility** (Beta, 2025):

```python
import OpenAI from 'openai'

const openai = new OpenAI({
    apiKey: "ANTHROPIC_API_KEY",
    baseURL: "https://api.anthropic.com/v1/"
})

const response = await openai.chat.completions.create({
    messages: [{ role: "user", content: "..." }],
    model: "claude-3-7-sonnet-20250219"
})
```

**Pros**:
- Familiar OpenAI interface
- Easy migration between providers
- Single SDK to learn

**Cons**:
- Beta status for Anthropic (may be unstable)
- May not expose all provider-specific features
- Still requires custom retry/fallback logic
- Vendor lock-in to OpenAI SDK patterns

**Recommendation**: ⚠️ Promising but less mature than LiteLLM for multi-provider support.

## Recommended Architecture

### Implementation Strategy

**Primary Library**: LiteLLM
**Default Provider**: Groq (for CI/CD and development)
**Production Providers**: Anthropic (native, Vertex, or Bedrock based on deployment)

### Configuration Design

```python
# Configuration in pyproject.toml
[tool.spec-check.check-semantic-test-adherence]
llm_provider = "groq"  # or "anthropic", "vertex", "bedrock", "openai"
llm_model = "llama-3.3-70b-versatile"  # provider-specific model name
threshold = 0.7
max_concurrent = 5
cache_results = true
```

### Environment Variables

```bash
# API Keys (read from environment per REQ-040)
GROQ_API_KEY="gsk_..."
ANTHROPIC_API_KEY="sk-ant-..."
OPENAI_API_KEY="sk-..."

# For Vertex AI
GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
VERTEX_PROJECT="my-project"
VERTEX_LOCATION="us-central1"

# For Bedrock
AWS_ACCESS_KEY_ID="AKIA..."
AWS_SECRET_ACCESS_KEY="..."
AWS_REGION="us-east-1"
```

### Provider Abstraction Layer

```python
from typing import Protocol, Any
import os
from litellm import completion

class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    def analyze_test_requirement(
        self,
        requirement_text: str,
        test_code: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze semantic alignment between test and requirement."""
        ...

class LiteLLMProvider:
    """LiteLLM-based provider supporting multiple backends."""

    def __init__(
        self,
        provider: str,
        model: str,
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        self.provider = provider
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

        # Map provider to LiteLLM model format
        self.model_string = self._get_model_string()

    def _get_model_string(self) -> str:
        """Convert provider + model to LiteLLM format."""
        if self.provider == "groq":
            return f"groq/{self.model}"
        elif self.provider == "anthropic":
            return f"anthropic/{self.model}"
        elif self.provider == "vertex":
            return f"vertex_ai/{self.model}"
        elif self.provider == "bedrock":
            return f"bedrock/{self.model}"
        else:
            return self.model

    def analyze_test_requirement(
        self,
        requirement_text: str,
        test_code: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze using LiteLLM with automatic retry."""

        prompt = self._build_prompt(requirement_text, test_code, context)

        try:
            response = completion(
                model=self.model_string,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a semantic test analyzer..."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                num_retries=self.max_retries,
                timeout=self.timeout,
                response_format={"type": "json_object"}  # Request JSON response
            )

            return self._parse_response(response)

        except Exception as e:
            return {
                "aligned": False,
                "confidence": 0.0,
                "explanation": f"Analysis failed: {e}",
                "error": str(e)
            }

    def _build_prompt(
        self,
        requirement_text: str,
        test_code: str,
        context: dict[str, Any]
    ) -> str:
        """Build analysis prompt."""
        return f"""
Analyze whether the following test validates the specified requirement.

Requirement: {requirement_text}

Test Code:
```python
{test_code}
```

Context:
- Requirement ID: {context.get('req_id')}
- Test Name: {context.get('test_name')}
- Spec File: {context.get('spec_file')}

Provide your analysis as JSON with:
- "aligned": boolean (true if test validates requirement)
- "confidence": float 0.0-1.0 (confidence in alignment)
- "explanation": string (detailed explanation of your analysis)
- "aspects": object with keys: action, conditions, assertions, scope
  (each aspect rated as "matches", "partial", or "missing")

Be specific about what the test does and how it relates to the requirement.
"""

    def _parse_response(self, response: Any) -> dict[str, Any]:
        """Parse LLM response into structured result."""
        import json

        content = response.choices[0].message.content

        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            # Fallback if model doesn't return valid JSON
            return {
                "aligned": "true" in content.lower(),
                "confidence": 0.5,
                "explanation": content,
                "error": "Failed to parse JSON response"
            }
```

### Fallback Strategy

For production robustness, implement automatic fallback:

```python
# Configuration with fallback chain
llm_provider_chain = ["groq", "anthropic", "openai"]

def analyze_with_fallback(requirement_text: str, test_code: str) -> dict:
    """Try providers in order until success."""

    for provider_name in llm_provider_chain:
        provider = create_provider(provider_name)

        try:
            result = provider.analyze_test_requirement(
                requirement_text,
                test_code,
                context={}
            )

            # If no error, return result
            if "error" not in result:
                result["provider_used"] = provider_name
                return result

        except Exception as e:
            # Log and continue to next provider
            logger.warning(f"Provider {provider_name} failed: {e}")
            continue

    # All providers failed
    raise RuntimeError("All LLM providers failed")
```

## Cost Analysis

### Scenario: 100 Test-Requirement Pairs

**Assumptions**:
- Average 500 tokens per analysis (300 input, 200 output)
- Total: 50,000 tokens per run (100 pairs × 500 tokens)

**Groq (Free Tier)**:
- Cost: $0
- Time: ~2 minutes (with 5 concurrent requests)
- Runs/day: 10 (within 1,000 request/day limit)

**Anthropic Haiku 4.5**:
- Input: 30,000 tokens × $1/1M = $0.03
- Output: 20,000 tokens × $5/1M = $0.10
- Total: ~$0.13 per run
- Monthly (daily runs): ~$4

**Anthropic Sonnet 4**:
- Input: 30,000 tokens × $3/1M = $0.09
- Output: 20,000 tokens × $15/1M = $0.30
- Total: ~$0.39 per run
- Monthly (daily runs): ~$12

**OpenAI GPT-4o**:
- Input: 30,000 tokens × $5/1M = $0.15
- Output: 20,000 tokens × $15/1M = $0.30
- Total: ~$0.45 per run
- Monthly (daily runs): ~$14

**With Prompt Caching** (Anthropic):
Requirement text can be cached across multiple test analyses, reducing costs by ~50-90% for the cached portion.

### Recommendations by Use Case

**GitHub Actions CI/CD**:
- Use Groq (free tier)
- Falls back to Anthropic if Groq limits exceeded
- Cost: Free to minimal

**Local Development**:
- Use Groq (free, fast)
- Or Ollama for fully offline work

**Production Monitoring**:
- Use Anthropic Haiku 4.5 (cost-effective, quality)
- Enable prompt caching for recurring analyses
- Cost: ~$0.13 per 100-pair run

**Enterprise Deployment**:
- Use Anthropic via Vertex AI or Bedrock
- Leverages existing cloud billing
- Meets compliance requirements

## Implementation Roadmap

### Phase 1: Core Implementation (MVP)

1. Integrate LiteLLM library (`uv add litellm`)
2. Implement provider abstraction layer
3. Support Groq as default provider
4. Add Anthropic native API support
5. Implement retry logic (REQ-024)
6. Add basic caching (REQ-042)

**Deliverable**: Working semantic analyzer with Groq and Anthropic

### Phase 2: Enhanced Providers

1. Add Vertex AI support
2. Add Bedrock support
3. Add OpenAI support
4. Implement fallback chain
5. Add provider health checks

**Deliverable**: Multi-provider support with automatic fallback

### Phase 3: Optimization

1. Implement advanced prompt caching
2. Add batch analysis optimization (REQ-029)
3. Add concurrent request pooling (REQ-041)
4. Optimize token usage (NFR-006)
5. Add progress indicators (NFR-004)

**Deliverable**: Production-ready, cost-optimized analyzer

## Security Considerations

### API Key Management

- ✅ Read from environment variables (REQ-040)
- ✅ Never log or print API keys
- ✅ Support multiple key sources (env, config files with restricted permissions)
- ✅ Clear error messages when keys are missing

### Data Privacy

- **Groq**: Check terms of service for data retention policies
- **Anthropic**: Offers data retention controls, SOC 2 Type II certified
- **Vertex AI**: Data stays within Google Cloud, FedRAMP High
- **Bedrock**: Data stays within AWS, HIPAA compliant

**Recommendation**: For sensitive codebases, prefer:
1. Vertex AI or Bedrock (data residency guarantees)
2. Self-hosted Ollama models (fully offline)
3. Anthropic native with appropriate data controls

## Testing Strategy

### Unit Tests

- Mock LiteLLM responses for deterministic testing
- Test retry logic with simulated failures
- Test provider fallback chains
- Test cache hit/miss scenarios

### Integration Tests

- Test with real Groq API (in CI, using secrets)
- Test error handling with invalid keys
- Test rate limit handling
- Test timeout scenarios

### Example Test

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.req("REQ-024")
def test_retry_logic_exponential_backoff():
    """Verify LLM provider retries up to 3 times with exponential backoff."""

    provider = LiteLLMProvider("groq", "llama-3.3-70b-versatile")

    with patch("litellm.completion") as mock_completion:
        # Simulate two failures, then success
        mock_completion.side_effect = [
            Exception("Rate limit"),
            Exception("Rate limit"),
            MagicMock(choices=[MagicMock(message=MagicMock(content='{"aligned": true}'))])
        ]

        result = provider.analyze_test_requirement(
            "REQ-001: System shall validate input",
            "def test_validates_input(): ...",
            {"req_id": "REQ-001"}
        )

        # Should succeed on third attempt
        assert mock_completion.call_count == 3
        assert result["aligned"] is True
```

## Open Questions

1. **Model Selection**: Which specific models provide best quality/cost ratio for code analysis?
   - Need to benchmark Llama 3.3 70B vs Claude Haiku vs GPT-4o on sample test-requirement pairs

2. **Context Window**: How much context should we include in prompts?
   - Full test file or just test function?
   - Related tests in same file?
   - Entire requirement section or just specific requirement?

3. **Caching Strategy**: What cache invalidation strategy works best?
   - Hash of requirement + test code?
   - Include Git commit hash?
   - Cache TTL?

4. **Ollama Integration**: Should we support local models via Ollama?
   - Useful for offline development
   - May require fine-tuning for acceptable accuracy
   - LiteLLM already supports Ollama

## Conclusion

**Recommended Approach**:

1. **Use LiteLLM** as the integration library for unified API and built-in resilience
2. **Default to Groq** for cost-free GitHub Actions CI/CD
3. **Support Anthropic** (native, Vertex, Bedrock) for production use cases
4. **Implement fallback chains** for robustness
5. **Add aggressive caching** to minimize API costs and latency

This architecture satisfies all SPEC-003 requirements while providing:
- ✅ Free tier for CI/CD (Groq)
- ✅ Production-grade options (Anthropic via multiple channels)
- ✅ Built-in retry/fallback (LiteLLM + custom fallback chains)
- ✅ Flexible deployment (native, Vertex, Bedrock)
- ✅ Cost optimization (caching, efficient models)
- ✅ Future extensibility (100+ providers via LiteLLM)

## References

- [LiteLLM Documentation](https://docs.litellm.ai/docs/)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [Groq API Documentation](https://console.groq.com/docs)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Anthropic on Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/claude)
- [Anthropic on Bedrock](https://aws.amazon.com/bedrock/claude/)
- [SPEC-003: Semantic Test-Adherence Validator](../specs/future/semantic-test-adherence.md)
