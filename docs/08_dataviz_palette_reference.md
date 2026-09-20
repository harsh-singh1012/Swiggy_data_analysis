# Visualization Palette Reference

Used consistently across every chart in `eda_charts/` and recommended for the Power BI build so a given entity (a segment, a city) reads as the same color everywhere it appears. Categorical hues are used in this fixed order — never reassigned per chart — because a stable order is what keeps color meaningful across pages; a color that shifts between pages just adds noise.

## Categorical order (use in this sequence, don't cycle or reorder)

| Slot | Name | Hex | Typical use in this project |
|---|---|---|---|
| 1 | Blue | `#2a78d6` | Primary series — revenue lines, primary bars |
| 2 | Orange | `#eb6834` | Secondary series — orders, comparison bars |
| 3 | Aqua | `#1baf7a` | Tertiary series — AOV, ratings |
| 4 | Yellow | `#eda100` | Fourth series when needed |
| 5 | Magenta | `#e87ba4` | Fifth series when needed |
| 6 | Green | `#008300` | Sixth series / "good" delta callouts |
| 7 | Violet | `#4a3aa7` | Seventh series |
| 8 | Red | `#e34948` | Eighth series / "decline" callouts |

Sequential (single-hue magnitude, e.g. the retention heatmap) uses blue, light → dark: `#cde2fb → #86b6ef → #3987e5 → #256abf → #184f95`.

## Chrome and ink

| Role | Hex |
|---|---|
| Chart surface | `#fcfcfb` |
| Primary ink (titles, labels) | `#0b0b0b` |
| Secondary/muted ink (axis, gridlines) | `#898781` / `#e1e0d9` |
| Decline / negative delta | `#e34948` |
| Growth / positive delta | `#0ca30c` |

## Rules followed throughout this project

- No pie charts — composition is shown with horizontal bars or a Lorenz-style cumulative line.
- One y-axis per chart; two differently-scaled measures become two charts, never a dual-axis combo.
- Rankings use horizontal bars, sorted descending.
- Trends use line charts; distributions use histograms; correlation uses scatter plots — matched to the job the chart needs to do, not to what looks most "advanced."

Full method and validation tooling: this project followed the `dataviz` design skill during chart construction (color-by-job assignment, mark specs, and the anti-pattern checklist); this file is the trimmed reference for anyone extending the charts later, including inside Power BI.
