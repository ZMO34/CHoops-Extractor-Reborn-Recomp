# Xbox roster relationships

Open Roster → School relationships. Searchable lists assign the school's arena,
conference, three rivals, head coach and two assistants. Conference assignment
updates the team link and both conference member lists together. Historical
conference data and team classification are preserved.

The member list supports lineup ordering, unassignment and transfers from the
searchable player selector. Transfers update the old/new lists and counts in one
undoable operation. Unassigned players can be assigned to a school. Full lists,
shared players, duplicate members, broken references and noncontiguous lists
reject before the document changes. Apply changes in memory, then Save roster.

## Xbox evidence

The supplied Xbox roster has 443 schools, 39 conferences and 5,607 assigned
players. All school member lists are contiguous and unique, including stock
17/18-player schools. Every conference list agrees with the team's backlink.
A scan found no additional player-to-school relative pointer or matching scalar
team ID in the 316-byte player rows; transfers preserve those rows entirely.

| Team field | Offset | Target | Anchor bias |
| --- | --- | --- | --- |
| Arena | 0x44 | arenas | 25 |
| Conference | 0x48 | conferences | 1 |
| Rivals 1–3 | 0x4c, 0x50, 0x54 | teams | 49 |
| Head coach / assistants | 0x60, 0x64, 0x68 | coaches | 21 |

References are signed big-endian deltas: `field + delta - bias` is a target row
start. Zero and -1 are null. Team player references occupy 18 words at +0x6c,
with a big-endian 16-bit count at +0x188 and player anchor bias 17. Conference
member lists have 100 words at +0x6e0, count +0x870 and team bias 49. Writers
derive every target from the live table headers, never fixed file addresses.

Arena/coach/rival assignment changes only its reference word. Conference moves
preserve historical fields and update only the two lists/counts and team link.
Transfers preserve player bytes and modify only affected school lists/counts.
The arena descriptor's separate owner/name routing is retained, allowing shared
arenas without rewriting their identity. Rival links remain directional.

`tools/relationship_smoke.py` checks the complete relationship corpus and tests
all eight assignments, transfer, unassignment, lineup ordering and exact undo on
an independent in-memory document. Supplied files are not written. These checks
are not an in-game Legacy or season-progression certification. Scholarship,
eligibility and historical statistics are separate fields and are not inferred
or reset when a relationship changes.
