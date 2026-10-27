"""Render structured cable and pipe records back into Turtle husks."""

import re
from typing import Any


_CABLE_SUBJECT_RE = re.compile(r'(_:\s*cable_\d+|_:cable_\d+)\s+a\s+fp:class/Cables', re.IGNORECASE)
_PIPE_SUBJECT_RE = re.compile(r'(_:\s*pipe_\d+|_:pipe_\d+)\s+a\s+fp:class/Pipes', re.IGNORECASE)


def _escape_turtle_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _format_number(value: float) -> str:
    return f"{float(value):.1e}"


def _extract_prefix_and_subjects(
    husk: str,
    *,
    subject_pattern: re.Pattern[str],
    generated_prefix: str,
) -> tuple[str, list[str]]:
    matches = list(subject_pattern.finditer(husk))
    if not matches:
        return generated_prefix, []

    prefix = husk[: matches[0].start()].rstrip()
    subjects = [match.group(1).replace(" ", "") for match in matches]
    return prefix, subjects


def _ensure_subjects(subjects: list[str], *, stem: str, count: int) -> list[str]:
    if len(subjects) >= count:
        return subjects[:count]

    filled = list(subjects)
    next_index = len(filled) + 1
    while len(filled) < count:
        filled.append(f"_:{stem}_{next_index}")
        next_index += 1
    return filled


def _render_cable_block(subject: str, record: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"{subject} a fp:class/Cables ;",
            f'    fp-prop-cp:name "{_escape_turtle_string(record["purpose_name"])}" ;',
            f"    fp-prop-cables:min_diameter {_format_number(record['min_diameter'])} ;",
            f"    fp-prop-cables:max_diameter {_format_number(record['max_diameter'])} .",
        ]
    )


def _render_pipe_block(subject: str, record: dict[str, Any]) -> str:
    lines = [
        f"{subject} a fp:class/Pipes ;",
        f'    fp-prop-pp:name "{_escape_turtle_string(record["purpose_name"])}" ;',
        f'    fp-prop-pm:name "{_escape_turtle_string(record["material_name"])}" ;',
        f'    fp-prop-pit:name "{_escape_turtle_string(record["isolation_type_name"])}" ;',
        f'    fp-prop-ptc:name "{_escape_turtle_string(record["transfer_category_name"])}" ;',
        f"    fp-prop-pipes:min_diameter {_format_number(record['min_diameter'])} ;",
        f"    fp-prop-pipes:max_diameter {_format_number(record['max_diameter'])} ;",
    ]

    pipe_type_names = record["pipe_type_names"]
    for index, pipe_type_name in enumerate(pipe_type_names):
        terminator = "." if index == len(pipe_type_names) - 1 else ";"
        lines.append(
            f'    fp-prop-pt:name "{_escape_turtle_string(pipe_type_name)}" {terminator}'
        )

    return "\n".join(lines)


def render_cable_records_to_turtle(husk: str, records: list[dict[str, Any]]) -> str:
    prefix, discovered_subjects = _extract_prefix_and_subjects(
        husk,
        subject_pattern=_CABLE_SUBJECT_RE,
        generated_prefix="@prefix fp: <http://example.org/fireprotection/> .",
    )
    subjects = _ensure_subjects(discovered_subjects, stem="cable", count=len(records))
    blocks = [_render_cable_block(subject, record) for subject, record in zip(subjects, records)]

    if prefix:
        return f"{prefix}\n\n" + "\n\n".join(blocks)
    return "\n\n".join(blocks)


def render_pipe_records_to_turtle(husk: str, records: list[dict[str, Any]]) -> str:
    prefix, discovered_subjects = _extract_prefix_and_subjects(
        husk,
        subject_pattern=_PIPE_SUBJECT_RE,
        generated_prefix="@prefix fp: <http://example.org/fireprotection/> .",
    )
    subjects = _ensure_subjects(discovered_subjects, stem="pipe", count=len(records))
    blocks = [_render_pipe_block(subject, record) for subject, record in zip(subjects, records)]

    if prefix:
        return f"{prefix}\n\n" + "\n\n".join(blocks)
    return "\n\n".join(blocks)