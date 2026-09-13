# Playbook: research-flow

**Input:** screenshots of one higgsfield.ai flow.
**Output:** `docs/research/flows/<flow>.md` + rows in `docs/research/product-map.md`.
**Role:** scout (cataloguing) → orchestrator (verdicts)

1. Save the screenshots as `docs/research/screenshots/NN-<flow>-<step>.png`.
   - NN keeps counting up across all flows.
   - Never rename a saved screenshot, because specs link to them.
2. Write `flows/<flow>.md` with **observations only, no solutions**:
   - Entry point and who can reach it (signed out or signed in)
   - Numbered steps, each citing its screenshot
   - Inputs and controls (types, limits, defaults), exact copy of the key labels
   - UI states seen: empty, loading/progress, error, success
   - Credits or cost shown, time taken, output format
   - Friction or bugs noticed (these are chances to be "better than the original")
3. Add or update rows in `product-map.md`: `surface · flow doc · verdict P0/P1/P2/CUT · one-line reason`.
4. Log a WORKLOG line and commit, including `.agent-logs/`.
