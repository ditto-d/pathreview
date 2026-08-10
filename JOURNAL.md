# JOURNAL

## Week 7 - Issue selection

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


## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/ditto-d/pathreview/commit/13cd7eaa516b8c786c76e9c26279d2873ee834d9

**Reproduction summary:**
Ran `pytest tests/unit/test_faithfulness_checker.py -v` locally. Result: 4
failed, 18 passed. Three failures (`test_partial_support_returns_middle_score`,
`test_multiple_claims_varying_support`, `test_multiple_context_chunks`) confirm
the reported bug: `_is_supported()` only returns true/false, so `check()` can
only ever score 0.0 or 1.0 per claim and can never land in the expected middle
range even when context partially supports a claim. A fourth failure,
`test_none_context_chunk_text`, is a separate crash bug (`TypeError`) in
`check()`'s context concatenation, unrelated to the reported scoring issue.

**PLAN.md link:** https://github.com/ditto-d/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Deciding whether to fix the unrelated None-crash bug (test_none_context_chunk_text)
in the same PR, or leave it out of scope and documented separately.

## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Environment set up and PLAN.md finalized from Week 8. Hadn't yet started
implementing `_support_ratio()` or the `check()` changes — the code itself
was still at the Week 8 planning stage going into this check-in.

**Next steps:**
Implement `_support_ratio()` and `_tokenize()` in
`rag/evaluator/faithfulness_checker.py`, update `check()` to use the new
continuous scoring instead of the boolean `_is_supported()` count, add a
regression test for the short-claim symptom, then run the full test suite
and `make check` before opening a PR.

**Blockers:**
None yet at this point — implementation hadn't started.

### Check-in 2 (end of week)

**PR link:** https://github.com/ditto-d/pathreview/pull/1

**Branch:** fix/152-faithfulness-short-claims

**What you built:**
Replaced the faithfulness checker's boolean support check with a
continuous scoring method (`_support_ratio`), so claims are scored based
on the fraction of their meaningful tokens found in context instead of a
fixed pass/fail overlap threshold. Also added punctuation-aware
tokenization and fixed a related crash on explicit `None` context text.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — added
`test_short_claim_fully_supported_scores_high`, a regression test for the
exact symptom in the issue. All 23 tests in the file pass.

**Self-review confirmation:** [x] make check passes (for my file — ruff
clean on `faithfulness_checker.py` and the test file; ~180 pre-existing
lint issues remain in unrelated files, documented in the PR)
[x] make test-unit passes (for my file - 23/23 in
`test_faithfulness_checker.py`; noted one pre-existing unrelated failure
in `test_batch_processor.py` in the PR)

**Draft PR feedback received from:** none


## Week 10 - Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in on the PR.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Getting the actual scoring formula right took far longer than designing
the idea behind it. I knew I wanted `_support_ratio()` to replace the
boolean `_is_supported()` check with something continuous, and that part
felt obvious once I understood the bug. But my first version, doubling
the overlap count and dividing by the claim's total tokens, passed
almost every test and then failed one, `test_multiple_claims_varying_support`,
by a small margin: 0.833 instead of the required under-0.8. Tracing that
down meant working through the actual token math by hand for a 2-token
claim ("Python expert.") and realizing the formula gave full credit for
matching just one word out of two. Fixing it took switching to
`math.ceil(len(claim_tokens) / 2)` as the number of matches required for
full credit, rounding up instead of a flat multiplier.

**What did you learn about working in a large codebase?**
The biggest shift was realizing I couldn't just make the bug go away,
I had to figure out exactly what "not breaking anything else" meant.
`_is_supported()` had five existing tests calling it directly and
asserting a real boolean back, so instead of rewriting it, I built
`_support_ratio()` as a separate method and only changed what `check()`
called. That's a different kind of thinking than solo projects, where I'd
just change whatever needed changing. I also learned that a single
function can hide more than one bug, while fixing #152's scoring issue,
I found an unrelated crash in the same function (`chunk.get("text", "")`
not handling an explicit `None` value) that actually overlapped with a
different, already-claimed issue, #153. Deciding whether to fix it
in-scope or leave it alone was a real judgment call, not something with
an obvious right answer, and I had to explain that reasoning explicitly
in my PR rather than just picking one option silently.

**How did AI tools help — and where did they fall short?**
AI was most useful for offloading tedious, mechanical work I could have
done by hand but would have been slow and error-prone: hand-tracing which
tokens survived stopword filtering for a given claim, working out what a
formula would produce for a specific test case, and drafting the PR description
text from my own notes and decisions. That let me
spend my own attention on the actual design questions, whether to touch
_is_supported(), how to scope the None-crash fix, instead of on
manual arithmetic and formatting. It fell short with the formula itself. An
AI-suggested version looked correct on paper but still failed a real test
by a specific margin (0.833 vs. under 0.8), so the test suite, not
reasoning about the formula, was what actually caught the bug. AI was a
tool for delegating grunt work, not a substitute for checking the real output.

**What would you do differently if you started over?**
Two concrete things. First, I'd write focused unit tests for
`_support_ratio()`'s internal logic as I built it, the zero-token guard,
the `ceil`-based threshold, the punctuation-stripping in `_tokenize()` —
instead of relying on one end-to-end regression test
(`test_short_claim_fully_supported_scores_high`) plus informal manual
tracing that never became permanent tests. I actually verified those edge
cases by hand while debugging, but that verification disappeared once the
numbers worked out instead of becoming something the next contributor
could rely on. Second, I'd run the full test suite against a new formula
immediately after writing it, rather than assuming it was probably right
and finding the gap only when a specific test failed.

**What are you most proud of from this module?**
Finding the second bug, the `None`-crash, on my own, in code I was
already touching, and making a deliberate, documented decision about
whether to fix it in the same PR rather than either ignoring it or
quietly bundling it in. I'm also proud of actually tracing the bug down
to the token level instead of stopping at "the named tests pass", I
could explain exactly why "Knows Python" only has one meaningful token
left after stopword removal, and why that structurally locks it out of
the old `>=2` threshold no matter how good the context is. That's the
kind of understanding that made the fix defensible, not just functional.