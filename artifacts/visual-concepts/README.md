## Visual Concepts

These concept images were generated as a product-vision pass for the diploma project:
"Моделирование работы приточной вентиляционной установки для ООО \"НПО \"Каскад-ГРУП\"".

### Files

- `concept-01-3d-control-room.png` — a strong 3D-first control-room concept with a dominant AHU cutaway scene, KPI stack, and operator navigation.
- `concept-02-validation-workstation.png` — a more analytical workstation centered on scenarios, validation, trends, comparison, and defense-readiness.
- `concept-03-defense-ready-digital-twin.png` — a hybrid concept that balances 3D realism, live operation, export/report tooling, and defense packaging.

### Responsive variants

- `concept-01-3d-control-room-mobile.png` — mobile-first version of the 3D control-room idea with the AHU scene, top KPIs, and bottom operator navigation.
- `concept-01-3d-control-room-tablet.png` — tablet landscape version that restores side analytics and a denser control-room layout.
- `concept-02-validation-workstation-mobile.png` — compact validation dashboard focused on mnemonic view, trends, checks, readiness, and exports.
- `concept-02-validation-workstation-tablet.png` — tablet analytical workstation with validation controls, comparison tables, trends, and event log.
- `concept-03-defense-ready-digital-twin-mobile.png` — mobile digital-twin concept with a strong 3D focal view plus defense-readiness and reporting actions.
- `concept-03-defense-ready-digital-twin-tablet.png` — tablet digital-twin workstation balancing 3D scene, scenarios, KPIs, logs, and export/report surfaces.

### Why these directions fit the project

- The repository already combines simulation, scenarios, trends, validation, comparison, export, archive, and demo-readiness flows.
- The current UI and docs emphasize a local engineering dashboard rather than a public-facing web product.
- The visualization strategy explicitly supports both 2D mnemonic and 3D scene modes, with 2D fallback preserved for reliability.

### Suggested design trajectory

If one direction is chosen for implementation, `concept-03-defense-ready-digital-twin.png` is the most balanced target:

- it reflects the existing 2D/3D duality;
- it keeps the interface technical and defense-oriented;
- it shows software maturity without drifting into a marketing aesthetic.

For responsive implementation, the matching trajectory is:

- mobile: prioritize one dominant scene or mnemonic, 4-6 top KPIs, scenario access, readiness, and export shortcuts;
- tablet: restore split panels, denser trends/tables, and side evidence or KPI rails;
- desktop: keep the current large-scene workstation approach as the richest presentation layer.
