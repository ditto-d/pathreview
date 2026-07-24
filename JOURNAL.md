# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker is the part of the RAG evaluator that checks whether
AI-generated portfolio feedback is actually backed by the user's retrieved
documents, instead of hallucinated. The bug is in `_is_supported()` in
`rag/evaluator/faithfulness_checker.py`: it only counts a claim as supported if
at least 2 non-stopword tokens overlap with a context chunk, but a short claim
like "Knows Python." only has one meaningful token, so it can never pass no
matter how well the context supports it. Because of this, feedback written as
short accurate sentences gets a faithfulness score of 0.0 , the metric ends up
punishing concise writing instead of measuring whether claims are grounded. A
successful fix would score short claims correctly (probably by making the
overlap threshold scale with the claim's length instead of a fixed 2) while
still rejecting claims that genuinely aren't supported, and would make the
three currently-failing tests in `tests/unit/test_faithfulness_checker.py` pass.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Issue selection reasoning ("Is this right for me?" checklist)

**Understanding:** I can explain the bug without looking at the issue (summary
above is from memory). I found `_is_supported()` in the codebase and read the
scoring logic around it. "Done" is concrete for this issue: the three failing
tests pass and the repro snippet from the issue body stops returning 0.0.

**Tier fit:** This is my first time contributing to a large codebase, so I went
with Tier 1 like the checklist recommends. The bug is contained to a single
function in one file, which matches the Tier 1 description, but the fix still
involves a real decision about how the scoring threshold should work, so it's
not trivial.

**Codebase readiness:** I read the faithfulness checker file and the test file
for it (`tests/unit/test_faithfulness_checker.py`), including one of the
failing tests end-to-end, so I know what the fixtures and assertions look like
before I write my own test.

**Scope and time:** Tier 1 is supposed to take 3–6 focused hours and I think
this fits, the issue comes with a copy-paste repro and named failing tests, so
the scope can't really grow on me. No "blocked by" dependencies. The issue has
6 claims on it, which is allowed since claims are non-exclusive, and it means I
have classmates on the same issue to compare solution plans with in Week 8.

**Environment note:** While setting up I found that the vector-db container
crashes on startup, chromadb 0.4.22 is incompatible with NumPy 2.0
(`np.float_` was removed). I reported it to the class and applied a local
workaround. It doesn't block my issue, since the faithfulness checker is a pure
Python module that doesn't touch the vector store.


## Week 8 reproduction notes (for JOURNAL.md)

Ran `pytest tests/unit/test_faithfulness_checker.py -v` locally.
Result: 4 failed, 18 passed.

**Reproduction commit link:** https://github.com/ditto-d/pathreview/commit/13cd7eaa516b8c786c76e9c26279d2873ee834d9


Failures:
- test_partial_support_returns_middle_score — expected 0.2 < score < 0.8, got 0.0
  (log: claims_count=1, supported_count=0, score=0.0)
- test_multiple_claims_varying_support — expected 0.2 < score < 0.8, got 0.0
  (log: claims_count=2, supported_count=0, score=0.0)
- test_multiple_context_chunks — expected score > 0.5, got 0.0
  (not named in the original issue, but same root cause)
- test_none_context_chunk_text — TypeError, not an assertion failure:
  `TypeError: sequence item 0: expected str instance, NoneType found`
  at `context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])`
  This is a separate bug from #152's core issue — chunk.get("text", "") only
  supplies the default for a *missing* key, not an explicit None value.


**Blockers or open questions:**
Deciding whether to fix the unrelated None-crash bug (test_none_context_chunk_text)
in the same PR, or leave it out of scope and documented separately.