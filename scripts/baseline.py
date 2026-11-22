#!/usr/bin/env python3
"""vibe-checkup baseline helper. Deterministic git bookkeeping so the agent does not
spend tokens running (and mis-running) the same six git commands every time.

Usage:
  python baseline.py stamp <project_root>
      Prints the front-matter facts for a normal-mode report (commit, dirty) and makes
      sure <project_root>/.vibe-checkup/ exists with its own .gitignore ("*"), so the
      folder is invisible to git without touching the project's .gitignore.

  python baseline.py scope <project_root> [--exclude DIR ...] [--threshold 0.4]
      Fast-mode scoping. Reads .vibe-checkup/report.md, validates its commit, and prints
      the change set since it (working tree vs that commit, plus untracked files).
      verdict: incremental | empty | full   (full = no usable baseline, or change too large)

  python baseline.py score <scores_file> [--items-from OTHER_FILE]
      Computes dimension scores, total and grade from a scores file: one check item per
      line, "<dim>.<item> <verdict>", e.g. "1.1 🟠", "1.2 通过", "1.5 不适用（无 UI）",
      "1.2 见 1.1". Only a severity emoji or 通过/pass is scored; every other verdict is
      listed but left out. --items-from keeps only the items that appear in OTHER_FILE
      (fast mode: re-score the baseline on the same ★ items).

  python baseline.py assemble <report_file> <findings_file> [<findings_file> ...]
      Replaces the single "<!-- FINDINGS -->" line in the report with the findings files,
      in the order given, so findings are written once and never re-typed.

Writes: stamp creates .vibe-checkup/ and its .gitignore; assemble rewrites the report
file it is given. Nothing else is written.

Exit codes: 0 ok; 1 bad input (score / assemble); 2 git itself failed (e.g. dubious
ownership): show the error to the user, do NOT treat it as "not a git repository".
"""
import argparse
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

STATE_DIR = ".vibe-checkup"


def git(root, *args):
    """Returns (stdout or None, stderr)."""
    try:
        r = subprocess.run(
            ["git", "-c", "core.quotePath=false", "-C", root, *args],
            capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=120)
        return (r.stdout if r.returncode == 0 else None), (r.stderr or "").strip()
    except FileNotFoundError:
        return None, "git executable not found"
    except Exception as e:
        return None, str(e)


def repo_state(root):
    """('ok', None) | ('not_repo', None) | ('error', message)"""
    out, err = git(root, "rev-parse", "--show-toplevel")
    if out is not None:
        return "ok", None
    if "not a git repository" in err.lower():
        return "not_repo", None
    return "error", err[:300]


def ensure_state_dir(root):
    d = os.path.join(root, STATE_DIR)
    os.makedirs(d, exist_ok=True)
    gi = os.path.join(d, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("*\n")


def head_commit(root):
    out, _ = git(root, "rev-parse", "HEAD")
    return (out or "").strip() or None  # None: repo with no commits yet


def cmd_stamp(root):
    state, err = repo_state(root)
    if state == "error":
        print(f"git_error: {err}")
        return 2
    ensure_state_dir(root)
    if state == "not_repo":
        print("commit: none\ndirty: false")
        return 0
    dirty, _ = git(root, "status", "--porcelain", "--", ".")
    print(f"commit: {head_commit(root) or 'none'}")
    print(f"dirty: {'true' if (dirty or '').strip() else 'false'}")
    return 0


def read_front_matter(path):
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return None
    m = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep and not line.lstrip().startswith("#"):
            fm[k.strip()] = v.split("#")[0].strip()
    return fm


def excluded(path, prefixes):
    return path.startswith(STATE_DIR + "/") or any(path == p or path.startswith(p + "/") for p in prefixes)


def cmd_scope(root, exclude, threshold):
    state, err = repo_state(root)
    if state == "error":
        print(f"git_error: {err}")
        return 2

    def full(reason, base="none"):
        print("baseline: no")
        print(f"reason: {reason}")
        print(f"base_commit: {base}")
        print("verdict: full")
        return 0

    if state == "not_repo":
        return full("not a git repository")
    head = head_commit(root)
    fm = read_front_matter(os.path.join(root, STATE_DIR, "report.md"))
    if fm is None:
        return full("no .vibe-checkup/report.md with front matter")
    if fm.get("mode") != "normal":
        return full(f"report.md mode is '{fm.get('mode')}', not normal")
    base = fm.get("commit", "none")
    if base in ("", "none"):
        return full("baseline report has no commit", base="none")
    if not re.fullmatch(r"[0-9a-fA-F]{7,64}", base):
        return full("baseline commit is not a hash", base=base)
    if not (git(root, "rev-parse", "--verify", "-q", base + "^{commit}")[0] or "").strip():
        return full("baseline commit no longer exists in this repo (rebase/gc/shallow clone)", base=base)

    diff, e1 = git(root, "diff", "--name-status", "--no-renames", "-z", "--relative", base)
    untracked, e2 = git(root, "ls-files", "-z", "--others", "--exclude-standard")
    if diff is None or untracked is None:
        print(f"git_error: {(e1 or e2)[:300]}")
        return 2
    changes = {}
    parts = diff.split("\0")
    for i in range(0, len(parts) - 1, 2):
        status, path = parts[i].strip(), parts[i + 1]
        if status and path and not excluded(path, exclude):
            changes[path] = status[0]
    for path in untracked.split("\0"):
        if path and path not in changes and not excluded(path, exclude):
            changes[path] = "?"

    tracked = [p for p in (git(root, "ls-files", "-z")[0] or "").split("\0") if p and not excluded(p, exclude)]
    n, total = len(changes), max(len(tracked), 1)
    ratio = n / total
    print("baseline: yes")
    print(f"base_commit: {base}")
    print(f"head_commit: {head or 'none'}")
    print(f"changed_files: {n}")
    print(f"tracked_files: {len(tracked)}")
    print(f"ratio: {ratio:.2f}")
    if n == 0:
        print("verdict: empty")
        return 0
    if ratio > threshold:
        print(f"reason: change set is {ratio:.0%} of tracked files (> {threshold:.0%}); treat as no baseline")
        print("verdict: full")
        return 0
    print("verdict: incremental")
    print("changed (A added, M modified, D deleted, ? untracked):")
    for path in sorted(changes):
        print(f"{changes[path]} {path}")
    return 0


SEVERITY = {"🔴": 4, "🟠": 2, "🟡": 1, "⚪": 0}


def read_scores(path):
    """{(dim, item): verdict}; verdict is a severity emoji, 'pass', or None (not scored)."""
    items = {}
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            m = re.match(r"\s*[-*]?\s*([0-9]+)\.([0-9]+)\s+(.*)", line)
            if not m:
                continue
            rest = m.group(3).strip()
            found = [s for s in SEVERITY if s in rest]
            if rest.startswith("见"):  # root cause already scored under another item
                verdict = None
            elif found:
                verdict = max(found, key=SEVERITY.get)
            else:
                verdict = "pass" if re.match(r"(通过|pass)", rest, re.I) else None
            items[(int(m.group(1)), int(m.group(2)))] = verdict
    return items


def cmd_score(path, items_from):
    try:
        items = read_scores(path)
        if items_from:
            keep = set(read_scores(items_from))
            items = {k: v for k, v in items.items() if k in keep}
    except OSError as e:
        print(f"error: {e}")
        return 1
    if not items:
        print("error: no '<dim>.<item> <verdict>' lines found")
        return 1
    dim_scores, any_red = [], False
    for dim in sorted({d for d, _ in items}):
        verdicts = [v for (d, _), v in items.items() if d == dim]
        scored = [v for v in verdicts if v is not None]
        counts = " ".join(f"{s}{scored.count(s)}" for s in SEVERITY)
        any_red = any_red or "🔴" in scored
        if not scored:
            print(f"dim {dim}: not scored ({len(verdicts)} items, none scored)")
            continue
        deduction = sum(SEVERITY.get(v, 0) for v in scored)
        score = round(10 * max(0.0, 1 - deduction / (2 * len(scored))), 1)
        dim_scores.append(score)
        print(f"dim {dim}: {score}  (scored {len(scored)} of {len(verdicts)} items; deduction {deduction}; {counts})")
    if not dim_scores:
        print("total: none (nothing scored)")
        return 0
    total = int(sum(dim_scores) / len(dim_scores) * 10 + 0.5)
    grade = "健康" if total >= 85 else "亚健康" if total >= 70 else "需要治理" if total >= 50 else "失控"
    if any_red and total >= 70:
        grade = "需要治理"
    print(f"scored_dims: {len(dim_scores)}")
    print(f"total: {total}")
    print(f"grade: {grade}" + ("  (capped: at least one 🔴)" if any_red and total >= 70 else ""))
    return 0


FINDINGS_MARK = "<!-- FINDINGS -->"


def cmd_assemble(report, parts):
    try:
        with open(report, encoding="utf-8") as fh:
            text = fh.read()
        chunks = []
        for p in parts:
            with open(p, encoding="utf-8") as fh:
                chunks.append(fh.read().strip())
    except OSError as e:
        print(f"error: {e}")
        return 1
    if text.count(FINDINGS_MARK) != 1:
        print(f"error: report must contain exactly one '{FINDINGS_MARK}' line (found {text.count(FINDINGS_MARK)}); nothing written")
        return 1
    with open(report, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text.replace(FINDINGS_MARK, "\n\n".join(c for c in chunks if c)))
    print(f"assembled: {len(parts)} findings files into {report}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sc = sub.add_parser("score")
    sc.add_argument("file")
    sc.add_argument("--items-from", default="", help="score only the items listed in this other scores file")
    asm = sub.add_parser("assemble")
    asm.add_argument("report")
    asm.add_argument("findings", nargs="+")
    s = sub.add_parser("stamp")
    s.add_argument("root")
    c = sub.add_parser("scope")
    c.add_argument("root")
    c.add_argument("--exclude", action="append", default=[], help="dir prefix to ignore (repeatable)")
    c.add_argument("--threshold", type=float, default=0.4)
    a = ap.parse_args()
    if a.cmd == "score":
        sys.exit(cmd_score(a.file, a.items_from))
    if a.cmd == "assemble":
        sys.exit(cmd_assemble(a.report, a.findings))
    root = os.path.abspath(a.root)
    if a.cmd == "stamp":
        sys.exit(cmd_stamp(root))
    sys.exit(cmd_scope(root, [x.strip("/\\").replace("\\", "/") for x in a.exclude], a.threshold))


if __name__ == "__main__":
    main()
