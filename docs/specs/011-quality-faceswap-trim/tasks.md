# Tasks 011: output quality, face swap, clip trim

Protocol: `scripts/task` (claim → worktree → verify → submit); orchestrator re-verifies, reviews, merges, deploys.
Waves (no two tasks in a wave share a file):
- W1: T-011-1 (LTX endpoint, GPU) ∥ T-011-2 (prompt composer, API adapter) ∥ T-011-3 (face swap endpoint, GPU) ∥ T-011-4 (face swap jobs, API)
- W2: T-011-5 (face swap tab, web) ∥ T-011-6 (clip trim, API/worker)
- W3: T-011-7 (trim UI, tool links, real showcase)
- W4: T-011-8 live verification (browser pass on the public URL, AC-8) — orchestrator + verifier session

- [x] T-011-1 · Faithful, warm LTX clip endpoint on Modal
- [x] T-011-2 · Always send the video model a real prompt
- [x] T-011-3 · Face swap endpoint on Modal
- [x] T-011-4 · Face swap jobs (contract, data, create/read, worker)
- [x] T-011-5 · Face swap tab in the studio
- [x] T-011-6 · Clip trim in sequences (API + stitcher)
- [x] T-011-7 · Trim UI, tool links, real showcase
- [ ] T-011-9 · Real showcase on the start page (split from T-011-7)
- [ ] T-011-10 · Fix the five T-011-8 live findings
- [x] T-011-8 · Live verification of spec 011
