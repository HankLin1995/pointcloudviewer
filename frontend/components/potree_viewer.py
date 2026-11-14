from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components


COMPONENT_ROOT = Path(__file__).resolve().parents[1] / "potree_component"
_component = components.declare_component(
    "potree_viewer",
    path=str(COMPONENT_ROOT),
)


def potree_viewer(*, dataset: dict[str, object], key: str) -> None:
    """Render the Potree viewer with an EPT dataset served by Streamlit."""

    _component(dataset=dataset, key=key, default=None)
