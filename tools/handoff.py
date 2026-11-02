"""Regenerate the continuation document from the maintained status and matrix."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parts=['# Continuation handoff\n\nRead AGENTS.md before editing. Work in this repository; do not launch the game.\n']
for name in ('CURRENT_STATUS.md','PARITY.md','TEST_REPORT.md'):
    parts.append('\n---\n\n'+(root/'docs'/name).read_text(encoding='utf-8'))
(root/'docs/HANDOFF.md').write_text('\n'.join(parts),encoding='utf-8')
