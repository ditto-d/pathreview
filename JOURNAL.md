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

**Feedback received:** [ ] Yes  [x] No,  still awaiting review

**Summary of feedback:**
No review came in on the PR itself. I did get written grader feedback on
my Week 9 submission, which I'm treating as the closest equivalent and
responding to below.

**How you responded:**
[leave blank, no PR-thread feedback to respond to]

### Reflection

**What I built:**
Issue #152 was a scoring bug in the faithfulness checker: `_is_supported()`
required at least 2 overlapping meaningful words between a claim and its
source context, so a short claim like "Knows Python", which has only one
meaningful word after stripping filler, could never be marked as
supported, no matter how well the context backed it up. I fixed this by
adding a new method, `_support_ratio()`, that scores each claim
continuously (what fraction of its meaningful words appear in context)
instead of forcing a hard pass/fail, and updated `check()` to average
those ratios instead of counting boolean hits. I left `_is_supported()`
untouched, since five existing tests call it directly and expect a real
boolean back. Along the way I found and fixed a second, unrelated bug in
the same function, a crash on an explicit `{"text": None}` value, and
documented that as a deliberate "while I'm here" fix rather than silent
scope creep.

**What the grader feedback got right, and what I'm taking from it:**
The Week 9 feedback praised the root-cause tracing (symptom → fixed
threshold → continuous replacement) and the decision to leave
`_is_supported()` alone rather than risk breaking its existing callers.
That instinct, minimize blast radius when you're new to a codebase,
wasn't something I fully appreciated as a *named* principle going in; it
came out of practical necessity, since I could see five tests depending on
that function's boolean contract. Having a grader name it back to me as
"good instinct" helped me understand that it's a transferable habit, not
just something specific to this one bug.

The critique was sharper and more useful, though: I only wrote one new
test, `test_short_claim_fully_supported_scores_high`, which validates the
issue's repro case but doesn't touch the internal logic of
`_support_ratio()` directly. The grader pointed out that method actually
has several distinct branches worth testing on their own, the
`ceil(len/2)` rounding behavior, the zero-meaningful-token guard that
returns `0.0` early, and the punctuation-stripping in `_tokenize()`. I
tested all of these *indirectly*, by hand, while debugging the formula
against the existing 23 tests (that's literally how I caught the 0.833
vs. <0.8 failure), but none of that verification made it into the actual
test suite as its own assertion. In hindsight, that's a real gap: the
manual tracing I did to fix the formula bug was exactly the kind of
insight that should have become a permanent test, not just a debugging
session I threw away once the numbers worked out.

**What surprised me:**
How much more time the formula tuning took than the initial design. I
assumed once I had the right *idea*, continuous ratio instead of
boolean, the implementation would be close to done. Instead, my first
formula (`2 * overlap / total`) passed almost everything but failed one
test by 0.033, because it let a 2-token claim get full credit for
matching just one word. Finding and fixing that required tracing actual
numbers by hand against multiple test cases, not just reasoning about the
formula abstractly. 

**What I'd do differently:**
Two concrete things, both pointing the same direction. First, per the
grader's feedback, I'd write focused unit tests for `_support_ratio()`'s
internal branches as I built them, not just one end-to-end regression
test — the zero-token guard and the rounding behavior each deserved their
own `test_support_ratio_...` case, the same way `_is_supported()` already
has five dedicated tests. Second,I'd run the full test suite against a new 
formula before trusting it, rather than assuming it was correct and only 
discovering the gap when pytest actually failed. Both of these point at
the same lesson: verify deliberately, in writing, as tests, don't let 
verification happen accidentally through one-off debugging and then 
get thrown away once the numbers work out."

**What I'm proud of:**
Catching the second bug (the `None`-crash) on my own, in code I was
already touching, and making a deliberate, documented call about whether
to fix it in-scope rather than either ignoring it or fixing it silently.
Also proud of actually diagnosing *why* the bug happened at the token
level, tracing "Knows Python" down to a single surviving meaningful
token, rather than just patching symptoms until the named tests turned
green.