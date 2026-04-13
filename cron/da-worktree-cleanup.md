---
name: da-worktree-cleanup
description: Auto-clean merged claude/* branches and stale worktrees in double-agent repo
---

Run git cleanup for the double-agent repo at ~/Documents/double-agent:

1. cd ~/Documents/double-agent
2. git fetch --prune
3. For each claude/* branch: check if merged into main (git branch --merged main). If merged, delete it locally and on remote.
4. git worktree prune
5. git worktree list (verify only main remains)
6. If main has unpushed commits, push them.

Do not merge anything — only clean up already-merged branches and stale worktrees.