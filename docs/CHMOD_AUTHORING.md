# CHMOD authoring

Use **Mods / Mod Projects → Create Mod**. Select the installed Xbox `assets`
folder, a complete runtime root containing `tools/chmod.ps1`, `ch2k8_tools.exe`
and `docs/formats`, and a new project directory outside the installation.
The source installation is read-only in this workflow. Direct editing remains
available through File → Open assets folder.

Add existing standard source banks to the project. Each bank is independently
copied, never hardlinked, into `edit/assets`. Select **Edit project copies** to
use the existing texture, scene, roster, relationship and uniform tools. Save
resource edits explicitly. Compare the selected TXTR with its original through
the Mods tab. **Review differences** shows target identities and both hashes.

Project metadata includes ID, name, author, exact semantic version, compatibility,
dependencies, incompatibilities and optional GitHub releases update URL. Edit
these in the manifest metadata field and save. Description is project-only:
the canonical runtime schema does not permit `description` in `mod.json`.
Reopen the project directory to continue; increment `version` before exporting
an update. Enabled state and priority belong exclusively to the launcher.

**Attach native roster + header** takes a compatible native `Roster.ROS` and its
own 328-byte aggregate header. It never reads or writes live Dummy HDD saves.
The validated, length-wrapped body is copied into `edit/native-roster-body.dat`.
Reopen project copies to edit it through the existing Roster tab. Export rebuilds
the researched big-endian byte-length wrapper and validates the complete native
save. It does not turn an arbitrary loose ROST into a save, fabricate a header,
migrate an existing Legacy, or prove a custom conference schedule. Direct CLI
commands also recognize `--assets PROJECT/edit/assets` and edit this private body.

Additional uniforms require source-compatible world/selection bank pairs and a
native roster routing to both. Add the source templates before using the existing
uniform creation tools, or attach authored bank directories with their original
template hashes. New banks produced in project copies are discovered at export.
Runtime native validation checks the complete inventory, source layout hash,
immutable bytes, private texture identities, pairs and assigned roster owners.
An incomplete pair or missing link blocks the whole export.

**Attach compiled DLL** accepts an already compiled extension; Studio never
compiles or loads it. The only catalogued package hook is `player.weight.read`,
ABI 1. Windows x64 PE structure and declarations are checked by the runtime
backend on export. This is unsandboxed code when the player enables it in the
launcher. Studio neither grants nor saves native-code launch permission.
The same canonical PE check also runs before accepting an attachment.
Scorebug, menu, scheduling, simulation, recruiting and other Legacy hooks remain
unsupported. A DLL accepted as PE metadata is not proof that it exports a valid
descriptor or functions in game; runtime loading performs additional ABI checks.

**Export .chmod** requires a new destination outside the source and project.
For dependencies, supply installed version directories for the entire selected
dependency closure; nothing is enabled or installed in the player's mods folder.
Studio generates only supported changed payloads and explicitly attached content.
It validates the canonical schema, invokes the actual launcher's install/resolve
functions in a disposable directory, creates a stored ZIP, checks entry paths,
bounds and hashes, reopens it, invokes the loader again and rechecks source hashes
before publishing by rename. Failed exports do not publish a package.
The current runtime's PowerShell cache copier retains Windows path-length
limits; choose a shallow cache root for launcher preparation.

Install and enable the package with the existing recomp launcher. Native DDS
preparation, shared-pixel-owner conflict detection, runtime receipt verification,
DLL descriptor loading and gameplay checks still apply there. Export acceptance
does not prove a successful game launch. Studio does not launch the game.

## Contract and evidence

The embedded JSON schema and hook registry are byte-identical snapshots of the
local runtime working tree on 2026-11-08. Its checkout base is commit
`1caa20dc74c09380cba6498bc38cfb04e14e922e`; the API 1.2 additions are currently
uncommitted local work, not contents of that base commit or a published release.
Its checkout remote is `kima1810/CH2K8-decomp`; the canonical schema identifies
the `kima1810/CH2K8-recomp` contract. Runtime backend and native validation are
required; Studio rejects schema/catalog drift rather than guessing a new API.
Sources inspected: versioned CHMOD 1.0/1.1/1.2 specifications, JSON schema,
hook registry, `tools/chmod.ps1`, `tools/native_assets/mod_contracts.h`,
`uniform_contracts.h`, native command dispatch, extension ABI/dispatch and the
runtime acceptance notes. Studio's workspace/protocol, DDS, scene/geometry,
roster/relationships/uniforms, audio, CLI, tests and format evidence were also
reviewed. No PS3 offsets, new hook addresses or new native save formats were added.

| Capability | Evidence/status | Boundary |
| --- | --- | --- |
| Project copies, reopen, source hashes, version export | Validated with synthetic resources | Standard loose banks only; private copies use disk space |
| DDS replacement | Validated with actual loader and native prepare/map checks | Existing exported BC templates; shared owners checked at launcher prepare |
| SCNE replacement | Validated source-bound cloth positions | No arbitrary scene/model overwrite, topology or skeleton edits |
| Native save body editing | Validated native wrapper/parser, immutable original save/header | Missing linked uniforms reject; no Legacy migration |
| Additional uniforms | Researched; delegates implemented native contract | Full world/selection + assigned native roster required; no retail acceptance claim |
| Assets + DLL package | Validated loader declarations with a synthetic PE | DLL deliberately never loaded; no hook execution claim |
| In-game behavior and scorebug hooks | Not in-game verified / scorebug unsupported | User acceptance remains outstanding |

Unsupported changes (audio, indexed fonts, embedded scene textures, raw component
texture writes, loose base ROST editing, arbitrary models) block export rather
than being silently omitted. These editors remain available for direct editing.
No arbitrary save adaptation or Legacy JSON format exists. Optional direct install
from Studio is not implemented; the launcher owns installation.

## CLI

```text
python run_studio.py --cli mod create C:/Mods/MyAuthorProject --assets D:/Game/assets --runtime D:/Runtime --id author.art --name "My artwork" --author "Author"
python run_studio.py --cli mod add-bank C:/Mods/MyAuthorProject existing.iff
python run_studio.py --cli --assets C:/Mods/MyAuthorProject/edit/assets import-artwork existing.iff/0 C:/Art/replacement.png
python run_studio.py --cli mod review C:/Mods/MyAuthorProject
python run_studio.py --cli mod attach-roster C:/Mods/MyAuthorProject C:/Saves/Roster.ROS C:/Saves/Roster.ROS.header
python run_studio.py --cli mod attach-uniform C:/Mods/MyAuthorProject C:/Art/ux501.iff 0x12345678
python run_studio.py --cli mod attach-extension C:/Mods/MyAuthorProject C:/Code/extension.dll
python run_studio.py --cli mod metadata C:/Mods/MyAuthorProject C:/Art/manifest-metadata.json
python run_studio.py --cli mod export C:/Mods/MyAuthorProject C:/Exports/art-1.0.0.chmod --dependency C:/Runtime/mods/other.mod/1.0.0
python run_studio.py --cli mod inspect C:/Exports/art-1.0.0.chmod
```

Replace all example names, resource keys, hashes and paths with verified source
identities. `inspect` performs bounded ZIP/schema/integrity checks only; export
also performs runtime semantic/source validation. The project file and private
working copy contain local paths/game resources and are not distribution formats.
Only the `.chmod` is intended for distribution, with the author's rights to its
payload. No retail content is included in the repository examples.

Tests use the real runtime's synthetic importer fixtures. Set `CHMOD_RUNTIME`
to a complete local runtime checkout to run the integration cases. They create
an isolated runtime backend with only the expected XEX hash changed to the
synthetic fixture identity; production Studio has no revision-bypass option.
The synthetic DDS example in that runtime is checked by Studio's archive reader.

API1.3 / ABI2 SDK authoring is documented in sdk/AUTHORING.md and included in
Windows packaging. Use source CLI capability/replacement options for ABI2;
existing GUI/default extension attachment remains ABI1. Runtime source snapshot
must match the updated canonical schema and inventory. SDK builds/exports do not
execute game code. Tests and gameplay acceptance remain pending by user request.
