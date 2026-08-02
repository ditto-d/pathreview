"""Check if generated feedback is supported by retrieved context."""

import math
import re

import structlog

logger = structlog.get_logger()

STOP_WORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "and",
    "or",
    "but",
    "in",
    "of",
    "to",
    "for",
    "that",
}


class FaithfulnessChecker:
    """Verify that feedback claims are supported by context."""

    def check(self, feedback: str, context_chunks: list[dict]) -> float:
        """Check faithfulness of feedback to context.

        Args:
            feedback: Generated feedback text
            context_chunks: Retrieved context chunks

        Returns:
            Faithfulness score 0.0-1.0. Each claim contributes a continuous
            support ratio (fraction of its meaningful tokens found in
            context); the score is the average ratio across all claims.
        """
        if not feedback or not context_chunks:
            logger.info(
                "faithfulness_empty_input",
                has_feedback=bool(feedback),
                has_chunks=bool(context_chunks),
            )
            return 0.0

        # Extract key claims from feedback (sentences)
        claims = self._extract_claims(feedback)
        if not claims:
            logger.info("faithfulness_no_claims_extracted")
            return 0.5  # Default to neutral if no extractable claims

        # Concatenate context text. chunk.get("text") or "" handles both a
        # missing "text" key and an explicit {"text": None} value; the old
        # chunk.get("text", "") only caught the missing-key case and crashed.
        context_text = " ".join([chunk.get("text") or "" for chunk in context_chunks])

        total_ratio = sum(self._support_ratio(claim, context_text) for claim in claims)

        score = total_ratio / len(claims) if claims else 0.0

        logger.info(
            "faithfulness_checked", claims_count=len(claims), average_ratio=score, score=score
        )

        return score

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract key claims from feedback text.

        Args:
            text: Feedback text

        Returns:
            List of claims (sentences)
        """
        # Split by sentence (simple regex)
        sentences = re.split(r"[.!?]+", text)
        claims = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return claims[:10]  # Limit to 10 claims for scoring

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Tokenize text into lowercase words with punctuation removed.

        Args:
             text: Input text

        Returns:
               Set of lowercase word tokens with surrounding punctuation removed.
        """

        raw_tokens = text.lower().split()
        return {token.strip(".,!?;:\"'") for token in raw_tokens}

    @staticmethod
    def _is_supported(claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim is supported
        """
        # Tokenize and check for keyword overlap
        claim_tokens = set(claim.lower().split())
        context_tokens = set(context.lower().split())

        # Require at least some meaningful overlap
        overlap = claim_tokens & context_tokens
        # Filter out common stop words

        meaningful_overlap = overlap - STOP_WORDS

        return len(meaningful_overlap) >= 2

    @staticmethod
    def _support_ratio(claim: str, context: str) -> float:
        """Calculate what fraction of a claim's meaningful tokens are in context.

        Unlike _is_supported, which returns a fixed True/False based on an absolute
        overlap threshold, this returns a continuous score so short claims aren't
        structurally unable to score highly. A claim needs at least half its
        meaningful tokens present in context to count as fully supported (rounded
        up, so a 2-token claim still needs both tokens, not just one).

        Args:
            claim: Claim text
            context: Context text

        Returns:
            Ratio in [0.0, 1.0]
        """
        claim_tokens = FaithfulnessChecker._tokenize(claim) - STOP_WORDS
        if not claim_tokens:
            return 0.0

        context_tokens = FaithfulnessChecker._tokenize(context) - STOP_WORDS
        overlap = claim_tokens & context_tokens

        required_for_full_credit = math.ceil(len(claim_tokens) / 2)
        ratio = len(overlap) / required_for_full_credit
        return min(1.0, ratio)
