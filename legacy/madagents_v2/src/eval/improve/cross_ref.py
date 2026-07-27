"""Update cross-references across MadGraph documentation files.

Manages **Details ->** links between reference files and detailed files.
"""

import re
from pathlib import Path

from eval.config import DOCS_DIR


def get_reference_files() -> list[Path]:
    """Get all top-level reference files."""
    return sorted(f for f in DOCS_DIR.glob("*.md") if f.is_file())


def get_detailed_files() -> list[Path]:
    """Get all detailed documentation files."""
    detailed_dir = DOCS_DIR / "detailed"
    if not detailed_dir.exists():
        return []
    return sorted(f for f in detailed_dir.glob("*.md") if f.is_file())


def get_deprecated_files() -> list[Path]:
    """Get all deprecated documentation files."""
    deprecated_dir = DOCS_DIR / "deprecated"
    if not deprecated_dir.exists():
        return []
    return sorted(f for f in deprecated_dir.glob("*.md") if f.is_file())


def find_section_end(content: str, section_heading: str) -> int | None:
    """Find the end position of a section (before the next heading of same or higher level).

    Returns the position where new content can be inserted at the end of the section.
    """
    # Find the heading
    pattern = re.compile(
        r"^(#{1,6})\s+" + re.escape(section_heading),
        re.MULTILINE,
    )
    match = pattern.search(content)
    if not match:
        return None

    heading_level = len(match.group(1))
    start_pos = match.end()

    # Find the next heading of same or higher level
    next_heading = re.compile(
        r"^#{1," + str(heading_level) + r"}\s+",
        re.MULTILINE,
    )
    next_match = next_heading.search(content, start_pos)

    if next_match:
        # Insert before the next heading, after any trailing whitespace
        insert_pos = next_match.start()
    else:
        # End of file
        insert_pos = len(content)

    return insert_pos


def add_cross_reference(
    source_file: Path,
    target_file: Path,
    anchor_text: str,
    section_heading: str | None = None,
) -> bool:
    """Add a **Details ->** link from source to target.

    Args:
        source_file: The file to add the link to.
        target_file: The file being linked to.
        anchor_text: Display text for the link.
        section_heading: If provided, insert the link at the end of this section.
                        Otherwise, append to end of file.

    Returns:
        True if the link was added, False if it already exists.
    """
    content = source_file.read_text()

    # Compute relative path from source to target
    try:
        rel_path = target_file.relative_to(source_file.parent)
    except ValueError:
        # If not relative, use path from DOCS_DIR
        rel_path = target_file.relative_to(DOCS_DIR)
        if source_file.parent != DOCS_DIR:
            # Source is in a subdirectory
            rel_path = Path("..") / rel_path

    link_text = f"**Details ->** [{anchor_text}]({rel_path})"

    # Check if link already exists
    if str(rel_path) in content:
        return False

    if section_heading:
        insert_pos = find_section_end(content, section_heading)
        if insert_pos is None:
            # Section not found, append to end
            insert_pos = len(content)
    else:
        insert_pos = len(content)

    # Ensure proper spacing
    before = content[:insert_pos].rstrip()
    after = content[insert_pos:]
    new_content = before + "\n\n" + link_text + "\n" + after

    source_file.write_text(new_content)
    return True


def register_new_file(
    new_file: Path,
    description: str,
    link_from_files: list[str] | None = None,
    link_section: str | None = None,
    target_dir: Path | None = None,
) -> list[str]:
    """Add links to a new file from the most relevant reference file(s).

    Args:
        new_file: Path to the newly created file.
        description: Short description for the link text.
        link_from_files: Explicit list of source file names to link from.
        link_section: Section heading to insert the link under.
        target_dir: If provided, operate on files in this directory instead
            of DOCS_DIR. Used for scratch dirs during per-question improvement.

    Returns:
        List of files that were updated.
    """
    docs_root = target_dir if target_dir else DOCS_DIR
    updated = []

    if link_from_files:
        for fname in link_from_files:
            source = docs_root / fname
            if source.exists():
                added = add_cross_reference(
                    source, new_file, description, link_section
                )
                if added:
                    updated.append(str(source))
    else:
        # Auto-detect: link from the most relevant file based on filename.
        # Deprecated files should only be auto-linked from detailed files,
        # not reference files — reference files should not link to deprecated content.
        is_deprecated = "deprecated" in str(new_file.relative_to(docs_root))
        new_stem = new_file.stem.lower()
        if is_deprecated:
            detailed_dir = docs_root / "detailed"
            ref_files = sorted(f for f in detailed_dir.glob("*.md") if f.is_file()) if detailed_dir.exists() else []
        else:
            ref_files = sorted(f for f in docs_root.glob("*.md") if f.is_file())
        for ref in ref_files:
            ref_stem = ref.stem.lower()
            # Simple keyword overlap heuristic
            ref_words = set(ref_stem.split("_"))
            new_words = set(new_stem.split("_"))
            # Remove numeric prefixes from detailed files
            new_words = {w for w in new_words if not w.isdigit()}
            if ref_words & new_words:
                added = add_cross_reference(
                    ref, new_file, description, link_section
                )
                if added:
                    updated.append(str(ref))

    return updated


def validate_all_links() -> list[dict]:
    """Check that all cross-references point to existing files.

    Returns a list of broken links with file, line, and target info.
    """
    broken = []
    all_files = get_reference_files() + get_detailed_files() + get_deprecated_files()

    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    for filepath in all_files:
        content = filepath.read_text()
        for i, line in enumerate(content.splitlines(), 1):
            for match in link_pattern.finditer(line):
                target = match.group(2)
                # Skip external URLs and pure anchors
                if target.startswith(("http://", "https://", "#")):
                    continue

                # Strip anchor from file+anchor links (e.g. ./config.md#section)
                target_file_part = target.split("#")[0]
                if not target_file_part:
                    continue  # was a pure anchor like "#section"

                # Resolve relative path
                target_path = (filepath.parent / target_file_part).resolve()
                if not target_path.exists():
                    broken.append({
                        "file": str(filepath),
                        "line": i,
                        "link_text": match.group(1),
                        "target": target,
                        "resolved": str(target_path),
                    })

    return broken
