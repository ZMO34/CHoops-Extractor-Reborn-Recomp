# CHoops Recomp Studio

See the [v0.2.0 workflow](docs/USER_GUIDE.md#folder-mod-workflow-in-020) for setup, features and limits.

Xbox 360 College Hoops 2K8 asset editor for the native recompilation.
Open an installed game's `assets` directory to browse and preview. Edit private
project copies and install the exported mod folder through the recomp launcher.

This is a code fork of the owner's CHoops Extractor Reborn v1.23, reworked around
Xbox formats and loose assets. Only format behavior validated against Xbox input
is enabled. Source game assets, executables and private research are never shipped.

See `docs/CURRENT_STATUS.md`, `docs/PARITY.md` and `docs/USER_GUIDE.md` for actual
feature support and validation limits. Source baseline:
https://github.com/ZMO34/CHoops-Extractor-Reborn at
`8ed6b90c8907e36dae2a33316294051a0a67db9c`.

# Non-destructive CHMOD authoring

The Mods / Mod Projects tab creates private source-bound projects and exports
the runtime's canonical mod folders. See [the authoring guide](docs/USER_GUIDE.md)
for supported payloads, CLI commands, runtime requirements and verification limits.

The public C++ extension SDK is hosted in [sdk/](sdk/README.md), including ABI2,
C++ wrappers, neutral examples and build/package instructions. Native callbacks
require a matching API1.3 recomp and explicit launcher opt-in. Current adapters
are researched/compiled, not in-game verified. ABI1 authoring remains compatible.
