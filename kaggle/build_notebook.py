"""Generate remotion_gpu_benchmark.ipynb dari benchmark.py (format # %%)."""

import json
from pathlib import Path

HERE = Path(__file__).parent
SOURCE = HERE / "benchmark.py"
TARGET = HERE / "remotion_gpu_benchmark.ipynb"


def split_cells(text: str):
    cells = []
    kind = "code"
    lines = []
    for line in text.splitlines():
        if line.startswith("# %%"):
            if lines:
                cells.append((kind, "\n".join(lines).strip("\n")))
            lines = []
            kind = "markdown" if "[markdown]" in line else "code"
        else:
            lines.append(line)
    if lines:
        cells.append((kind, "\n".join(lines).strip("\n")))
    return cells


def to_source(text: str):
    out = text.splitlines(keepends=True)
    return out


def markdown_lines(text: str):
    lines = []
    for line in text.splitlines():
        if line.startswith("# "):
            lines.append(line[2:])
        elif line == "#":
            lines.append("")
        else:
            lines.append(line)
    return [line + "\n" for line in lines]


nb_cells = []
for kind, body in split_cells(SOURCE.read_text()):
    if not body.strip():
        continue
    source = markdown_lines(body) if kind == "markdown" else to_source(body + ("\n" if not body.endswith("\n") else ""))
    cell = {
        "cell_type": kind,
        "metadata": {},
        "source": source,
    }
    if kind == "code":
        cell.update({"execution_count": None, "outputs": []})
    nb_cells.append(cell)

notebook = {
    "cells": nb_cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

TARGET.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n")
print(f"wrote {TARGET} ({len(nb_cells)} cells)")
