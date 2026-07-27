"""
V4A diff parser/applier helpers.

Extracted from tools.py — self-contained, no madagents imports.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Tuple, Dict, List, Optional, Any, Literal

# ── V4A diff engine ───────────────────────────────────────────────────

class V4ADiffError(ValueError):
    """Any problem detected while parsing or applying a V4A diff."""

@dataclass
class _Chunk:
    orig_index: int = -1
    del_lines: List[str] = field(default_factory=list)
    ins_lines: List[str] = field(default_factory=list)

def _find_context_core(lines: List[str], context: List[str], start: int) -> Tuple[int, int]:
    """Find an exact/trimmed context match and return (index, fuzz_score)."""
    if not context:
        return start, 0

    # Exact match
    for i in range(start, len(lines) - len(context) + 1):
        if lines[i : i + len(context)] == context:
            return i, 0

    # rstrip match
    ctx_r = [s.rstrip() for s in context]
    for i in range(start, len(lines) - len(context) + 1):
        if [s.rstrip() for s in lines[i : i + len(context)]] == ctx_r:
            return i, 1

    # strip match (very fuzzy)
    ctx_s = [s.strip() for s in context]
    for i in range(start, len(lines) - len(context) + 1):
        if [s.strip() for s in lines[i : i + len(context)]] == ctx_s:
            return i, 100

    return -1, 0

def _find_context(lines: List[str], context: List[str], start: int, eof: bool) -> Tuple[int, int]:
    """
    If eof=True, prefer matching the context near the end of file.
    """
    if eof:
        near_end = max(0, len(lines) - len(context))
        idx, fuzz = _find_context_core(lines, context, near_end)
        if idx != -1:
            return idx, fuzz
        idx, fuzz = _find_context_core(lines, context, start)
        return idx, fuzz + 10_000
    return _find_context_core(lines, context, start)

def _peek_next_section(diff_lines: List[str], index: int) -> Tuple[List[str], List[_Chunk], int, bool]:
    """
    Reads one "section" of V4A diff until the next @@ or EOF.
    Returns:
      - old_context_lines: the contiguous context lines that must match somewhere in the original
      - chunks: delete/insert chunks anchored relative to the context
      - new_index: where we stopped in diff_lines
      - eof: whether this section is marked as end-of-file (*** End of File)
    """
    old: List[str] = []
    del_lines: List[str] = []
    ins_lines: List[str] = []
    chunks: List[_Chunk] = []

    mode: Literal["keep", "add", "delete"] = "keep"
    orig_index = index

    while index < len(diff_lines):
        s = diff_lines[index]

        # Section boundaries:
        if s.startswith("@@") or s.startswith("***"):
            break

        index += 1

        # The reference implementation treats empty as " " keep-line.
        if s == "":
            s = " "

        if not s:
            raise V4ADiffError("Invalid empty line in diff section")

        prefix = s[0]
        body = s[1:]

        last_mode = mode
        if prefix == "+":
            mode = "add"
        elif prefix == "-":
            mode = "delete"
        elif prefix == " ":
            mode = "keep"
        else:
            raise V4ADiffError(f"Invalid diff line prefix {prefix!r}: {s!r}")

        # When returning to keep-mode after edits, close a chunk
        if mode == "keep" and last_mode != mode:
            if ins_lines or del_lines:
                chunks.append(
                    _Chunk(
                        orig_index=len(old) - len(del_lines),
                        del_lines=del_lines,
                        ins_lines=ins_lines,
                    )
                )
            del_lines, ins_lines = [], []

        if mode == "delete":
            del_lines.append(body)
            old.append(body)
        elif mode == "add":
            ins_lines.append(body)
        else:  # keep
            old.append(body)

    # Final pending chunk
    if ins_lines or del_lines:
        chunks.append(
            _Chunk(
                orig_index=len(old) - len(del_lines),
                del_lines=del_lines,
                ins_lines=ins_lines,
            )
        )

    # Optional EOF sentinel sometimes appears in older harnesses
    eof = False
    if index < len(diff_lines) and diff_lines[index] == "*** End of File":
        eof = True
        index += 1

    if index == orig_index:
        raise V4ADiffError("Nothing in this diff section")

    return old, chunks, index, eof

def apply_v4a_update_diff(original: str, diff: str) -> Tuple[str, int]:
    """
    Apply a V4A "update_file" diff to original file content.
    Returns (new_content, fuzz_score).
    """
    orig_lines = original.split("\n")
    diff_lines = diff.splitlines()
    i = 0
    search_start = 0
    fuzz_total = 0

    applied_chunks: List[_Chunk] = []

    while i < len(diff_lines):
        line = diff_lines[i]

        # V4A supports "jump" markers:
        #   @@ <anchor line>
        # or a bare "@@" line.
        if line.startswith("@@ "):
            anchor = line[3:]
            i += 1

            # Move search_start forward if we can find the anchor
            found = False
            if anchor and anchor not in orig_lines[:search_start]:
                for j in range(search_start, len(orig_lines)):
                    if orig_lines[j] == anchor:
                        search_start = j + 1
                        found = True
                        break

            # Try stripped anchor as fuzzier match if exact not found
            if anchor and not found and anchor.strip() not in [s.strip() for s in orig_lines[:search_start]]:
                for j in range(search_start, len(orig_lines)):
                    if orig_lines[j].strip() == anchor.strip():
                        search_start = j + 1
                        fuzz_total += 1
                        break

            continue

        if line.strip() == "@@":
            # bare section marker; just advance
            i += 1
            continue

        # Otherwise parse the next section (keep/add/delete lines)
        ctx, chunks, new_i, eof = _peek_next_section(diff_lines, i)

        new_index, fuzz = _find_context(orig_lines, ctx, search_start, eof=eof)
        if new_index == -1:
            ctx_txt = "\n".join(ctx)
            raise V4ADiffError(f"Context not found (start={search_start}, eof={eof}). Context:\n{ctx_txt}")
        fuzz_total += fuzz

        # Anchor chunk indices to the matched context start
        for ch in chunks:
            applied_chunks.append(
                _Chunk(
                    orig_index=new_index + ch.orig_index,
                    del_lines=ch.del_lines,
                    ins_lines=ch.ins_lines,
                )
            )

        search_start = new_index + len(ctx)
        i = new_i

    # Apply chunks in order
    applied_chunks.sort(key=lambda c: c.orig_index)
    dest_lines: List[str] = []
    cursor = 0

    for ch in applied_chunks:
        if ch.orig_index > len(orig_lines):
            raise V4ADiffError(f"Chunk index {ch.orig_index} exceeds file length {len(orig_lines)}")
        if cursor > ch.orig_index:
            raise V4ADiffError(f"Overlapping chunks: cursor {cursor} > {ch.orig_index}")

        dest_lines.extend(orig_lines[cursor : ch.orig_index])
        cursor = ch.orig_index

        # Validate deletions match (best-effort)
        if ch.del_lines:
            existing = orig_lines[cursor : cursor + len(ch.del_lines)]
            if existing != ch.del_lines:
                # Allow a little fuzz: rstrip match
                if [s.rstrip() for s in existing] != [s.rstrip() for s in ch.del_lines]:
                    raise V4ADiffError(
                        "Deletion block does not match original.\n"
                        f"Expected:\n{chr(10).join(ch.del_lines)}\n\n"
                        f"Found:\n{chr(10).join(existing)}"
                    )

        dest_lines.extend(ch.ins_lines)
        cursor += len(ch.del_lines)

    dest_lines.extend(orig_lines[cursor:])
    return "\n".join(dest_lines), fuzz_total

def v4a_create_file_content(diff: str) -> str:
    """
    For create_file: docs say diff is a V4A diff representing full contents.
    In practice this is usually every line prefixed with '+'.
    We support:
      - all non-empty lines start with '+': strip '+' prefixes
      - otherwise: treat diff as raw content
    """
    lines = diff.splitlines()
    non_empty = [ln for ln in lines if ln != ""]
    if non_empty and all(ln.startswith("+") for ln in non_empty):
        return "\n".join([ln[1:] if ln.startswith("+") else ln for ln in lines])
    return diff

def validate_v4a_create_diff(diff: str) -> Optional[str]:
    """Validate that create_file diffs use '+' prefixes for each line."""
    lines = diff.splitlines()
    for idx, line in enumerate(lines, 1):
        if not line.startswith("+"):
            return (
                "Invalid create_file diff: line "
                f"{idx} does not start with '+'. "
                "For empty lines, use '+' on its own line."
            )
    return None

def validate_diff_control_chars(diff: str) -> Optional[str]:
    """Reject control characters that are not allowed in diffs."""
    for idx, ch in enumerate(diff):
        code = ord(ch)
        if code < 32 or code == 127:
            if ch in ("\n", "\t", "\r"):
                continue
            return (
                "Invalid diff: control character "
                f"U+{code:04X} at index {idx}. "
                "Only \\n, \\t, and \\r are allowed."
            )
    return None

def _safe_join(root_dir: Path, relative_path: str) -> Path:
    """Resolve a path, making relative paths relative to *root_dir*."""
    rel = Path(relative_path)

    if rel.is_absolute():
        return rel.resolve()

    # Resolve relative to root_dir
    full = (root_dir / rel).resolve()
    return full

def apply_patch_operation_to_fs(
    *,
    root_dir: Path,
    operation: Dict[str, Any],
) -> Tuple[bool, str]:
    """
    Apply a single apply_patch operation (create_file/update_file/delete_file) to disk.
    Returns (success, log_output).
    """
    op_type = operation.get("type")
    path = operation.get("path")
    diff = operation.get("diff")

    if not isinstance(path, str) or not path:
        return False, "Invalid operation.path"

    try:
        full_path = _safe_join(root_dir, path)
    except Exception as e:
        return False, f"Invalid path: {e}"

    try:
        if op_type == "delete_file":
            if full_path.exists():
                full_path.unlink()
            return True, f"Deleted {path}"

        if op_type == "create_file":
            if not isinstance(diff, str):
                return False, "create_file requires operation.diff (string)"
            error = validate_diff_control_chars(diff)
            if error:
                return False, error
            full_path.parent.mkdir(parents=True, exist_ok=True)
            content = v4a_create_file_content(diff)
            full_path.write_text(content, encoding="utf-8")
            return True, f"Created {path} ({len(content)} chars)"

        if op_type == "update_file":
            if not isinstance(diff, str):
                return False, "update_file requires operation.diff (string)"
            error = validate_diff_control_chars(diff)
            if error:
                return False, error
            if not full_path.exists():
                return False, f"File not found: {path}"
            original = full_path.read_text(encoding="utf-8")
            updated, fuzz = apply_v4a_update_diff(original, diff)
            full_path.write_text(updated, encoding="utf-8")
            return True, f"Updated {path} (fuzz={fuzz})"

        return False, f"Unknown operation.type: {op_type!r}"

    except V4ADiffError as e:
        return False, f"Patch failed for {path}: {e}"
    except Exception as e:
        return False, f"Unhandled error applying {op_type} to {path}: {e}"
