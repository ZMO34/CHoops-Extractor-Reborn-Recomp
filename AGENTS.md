# Recomp Studio development

- Target this repository, not the original Extractor repository.
- Work on feature branches and publish reviewable updates through PRs to main.
  The empty-repository documentation bootstrap is the sole initial-main exception.
- Open the installed Xbox `assets` folder. No archive/disc explorer, staging
  workflow, automatic game launch or game-input automation.
- Do not import old-platform assets, save adapters, executable addresses, schema
  assumptions or research results. Revalidate source-derived algorithms on Xbox.
- Preserve unknown bytes and shared identities. Use transactional writes, reparse
  results, compare untouched ranges and reject ambiguous or unsupported layouts.
- UI and CLI use the same backend. Background workers never manipulate widgets.
- Keep game data, private reports/paths, tool distributions, logs and binaries out
  of Git. Read supplied installed assets only for research; write tests to separate
  synthetic/private outputs. User edits require an explicit Save action.
- Maintain CURRENT_STATUS, PARITY, format evidence, USER_GUIDE, COMMANDS,
  TEST_REPORT and CHANGELOG with every update. Regenerate the handoff document.
- Publish precise tests and limitations. Offline parsing/rendering is not gameplay
  confirmation. Do not describe incomplete parity as complete.
