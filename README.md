# CHoops Recomp Studio

The first Windows preview is **v0.1**. See
[release notes](docs/RELEASE_NOTES_v0.1.md) for setup, features and limits.

Xbox 360 College Hoops 2K8 asset editor for the native recompilation.
Open an installed game's `assets` directory; edit resources directly and restart
through the recomp launcher to apply changes. No archive explorer, staging layer,
disc builder or automatic game launcher is part of this application.

This is a code fork of the owner's CHoops Extractor Reborn v1.23, reworked around
Xbox formats and loose assets. Only format behavior validated against Xbox input
is enabled. Source game assets, executables and private research are never shipped.

See `docs/CURRENT_STATUS.md`, `docs/PARITY.md` and `docs/USER_GUIDE.md` for actual
feature support and validation limits. Source baseline:
https://github.com/ZMO34/CHoops-Extractor-Reborn at
`8ed6b90c8907e36dae2a33316294051a0a67db9c`.

# Non-destructive CHMOD authoring

The Mods / Mod Projects tab creates private source-bound projects and exports
the runtime's canonical `.chmod` packages. See [the authoring guide](docs/CHMOD_AUTHORING.md)
for supported payloads, CLI commands, runtime requirements and verification limits.

The public C++ extension SDK is hosted in [sdk/](sdk/README.md), including ABI2,
C++ wrappers, neutral examples and build/package instructions. Native callbacks
require a matching API1.3 recomp and explicit launcher opt-in. Current adapters
are researched/compiled, not in-game verified. ABI1 authoring remains compatible.
