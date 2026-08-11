"""Generate a Mermaid erDiagram from the real SQLAlchemy models.

Audit finding C-18: the thesis's §11.7 "diagram" was raw Mermaid source
printed as text, and omitted the `users` table entirely. This script
introspects `database/models/*.py` directly — the same models Alembic
migrates and the Backend's ORM queries — so the diagram can't drift from
the real schema the way a hand-drawn one could. Run inside the backend
container (has `models` on its path) and redirect stdout to a `.mmd` file,
then render with mermaid-cli (see figures/README.md).
"""

from models import Base


def _fk_targets(table) -> dict[str, str]:
    targets = {}
    for fk in table.foreign_keys:
        targets[fk.parent.name] = fk.column.table.name
    return targets


def main() -> None:
    lines = ["erDiagram"]

    # Relationships, one line per FK, with a readable verb guessed from the
    # column name — labels matter less than getting every real FK listed;
    # the thesis's raw version omitted `users` and several FKs entirely.
    for table in Base.metadata.sorted_tables:
        fks = _fk_targets(table)
        for col_name, target_table in fks.items():
            verb = col_name.removesuffix("_id").replace("_", " ")
            lines.append(f'    {target_table} ||--o{{ {table.name} : "{verb}"')

    lines.append("")

    # Full column listing per table, with type and key markers — the
    # thesis's version showed zero attributes for any entity.
    for table in Base.metadata.sorted_tables:
        lines.append(f"    {table.name} {{")
        for col in table.columns:
            col_type = str(col.type).split("(")[0].upper()
            markers = []
            if col.primary_key:
                markers.append("PK")
            if col.foreign_keys:
                markers.append("FK")
            marker_str = " ".join(markers)
            lines.append(f"        {col_type} {col.name} {marker_str}".rstrip())
        lines.append("    }")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
