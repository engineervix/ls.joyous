# ------------------------------------------------------------------------------
# Utilities for working with Wagtail panels across versions
# ------------------------------------------------------------------------------
from typing import List

try:
    # Wagtail >= 3
    from wagtail.admin.panels import FieldPanel, Panel
except Exception:  # pragma: no cover - fallback for older Wagtail
    from wagtail.admin.edit_handlers import FieldPanel  # type: ignore
    from wagtail.admin.edit_handlers import Panel  # type: ignore


def get_panel_fields(panel: Panel) -> List[str]:
    """
    Return the list of form field names represented by a panel. Works on
    both Wagtail <3 (required_fields) and >=3 (get_form_options / recursion).

    - For FieldPanel-like panels, returns the single field name
    - For panel groups (e.g. MultiFieldPanel), recursively aggregates children
    """
    field_names: List[str] = []

    # Wagtail >= 3: get_form_options may include fields for FieldPanel
    get_form_options = getattr(panel, "get_form_options", None)
    if callable(get_form_options):
        try:
            options = get_form_options()
            if isinstance(options, dict):
                fields_opt = options.get("fields")
                if isinstance(fields_opt, (list, tuple)):
                    field_names.extend(str(name) for name in fields_opt)
        except Exception:
            # fall back to other strategies
            pass

    # If it's a FieldPanel (or subclass), include its field_name explicitly
    if isinstance(panel, FieldPanel) and hasattr(panel, "field_name"):
        try:
            field_names.append(str(panel.field_name))
        except Exception:
            pass

    # Wagtail < 3 support: required_fields aggregates for PanelGroups already
    required_fields = getattr(panel, "required_fields", None)
    if callable(required_fields):
        try:
            field_names.extend(str(name) for name in required_fields())
        except Exception:
            pass

    # Recurse into children for PanelGroup/MultiFieldPanel-style containers
    children = getattr(panel, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            field_names.extend(get_panel_fields(child))

    # Deduplicate while preserving order
    seen = set()
    unique_fields: List[str] = []
    for name in field_names:
        if name not in seen and name:
            seen.add(name)
            unique_fields.append(name)
    return unique_fields
