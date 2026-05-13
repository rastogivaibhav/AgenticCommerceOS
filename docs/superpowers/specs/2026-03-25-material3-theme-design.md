# ACOS Control Plane — Material 3 Theme

**Date:** 2026-03-25
**Status:** Approved
**Scope:** `apps/ops_ui_v2` frontend only — no API changes

---

## Decision Summary

| Decision | Choice |
|---|---|
| Design system | Google Material Design 3 (Material You) |
| Color scheme | Purple Light (M3 baseline) |
| Navigation | Navigation Rail (80px, icons + labels) |
| Typography | Roboto (400/500/700) + Roboto Mono for IDs |
| Theme toggle | Keep existing light/dark toggle; add M3 dark tokens |

---

## Tailwind Integration Strategy

The project uses Tailwind CSS. The M3 tokens are defined as **CSS custom properties on `:root`** and mapped into `tailwind.config.js` so that Tailwind utility classes resolve to M3 values:

```js
// tailwind.config.js
theme: {
  extend: {
    colors: {
      primary: 'var(--md-primary)',
      'on-primary': 'var(--md-on-primary)',
      'primary-container': 'var(--md-primary-container)',
      'on-primary-container': 'var(--md-on-primary-container)',
      secondary: 'var(--md-secondary)',
      'secondary-container': 'var(--md-secondary-container)',
      'on-secondary-container': 'var(--md-on-secondary-container)',
      surface: 'var(--md-surface)',
      'surface-variant': 'var(--md-surface-variant)',
      'surface-container': 'var(--md-surface-container)',
      'surface-container-high': 'var(--md-surface-container-high)',
      'on-surface': 'var(--md-on-surface)',
      'on-surface-variant': 'var(--md-on-surface-variant)',
      outline: 'var(--md-outline)',
      'outline-variant': 'var(--md-outline-variant)',
      error: 'var(--md-error)',
      'error-container': 'var(--md-error-container)',
      'warning-container': 'var(--md-warning-container)',
      'on-warning-container': 'var(--md-on-warning-container)',
    }
  }
}
```

All existing `bg-gray-*`, `dark:bg-gray-*`, `text-gray-*` Tailwind classes in components are replaced with the M3 token equivalents above. No raw hex values in component JSX.

---

## Dark Mode Configuration

The existing `ThemeProvider` toggles a `dark` class on `<html>` (confirmed by `tailwind.config.js` `darkMode: 'class'`). The M3 dark tokens are therefore scoped to `:root.dark` which matches correctly.

No change to `ThemeProvider.jsx` or `lib/theme.jsx` is needed — those files toggle the `dark` class on `<html>` as before. Only the CSS custom property values inside `:root.dark` are replaced.

---

## Color Tokens

### Light scheme (`:root`)
```css
--md-primary: #6750A4;
--md-on-primary: #FFFFFF;
--md-primary-container: #EADDFF;
--md-on-primary-container: #21005D;
--md-secondary: #625B71;
--md-secondary-container: #E8DEF8;
--md-on-secondary-container: #1D192B;
--md-tertiary: #7E5260;
--md-tertiary-container: #FFD8E4;
--md-on-tertiary-container: #31111D;
--md-surface: #FFFBFE;
--md-surface-variant: #E7E0EC;
--md-surface-container: #F3EDF7;
--md-surface-container-high: #ECE6F0;
--md-on-surface: #1C1B1F;
--md-on-surface-variant: #49454F;
--md-outline: #79747E;
--md-outline-variant: #CAC4D0;
--md-error: #B3261E;
--md-error-container: #F9DEDC;
--md-on-error-container: #410E0B;
/* Semantic aliases for status indicators */
--md-warning-container: #FDE8C9;
--md-on-warning-container: #B45309;
--md-success-container: #C8F0DA;
--md-on-success-container: #198A56;
```

### Dark scheme (`:root.dark`)
```css
--md-primary: #D0BCFF;
--md-on-primary: #381E72;
--md-primary-container: #4F378B;
--md-on-primary-container: #EADDFF;
--md-secondary: #CCC2DC;
--md-secondary-container: #4A4458;
--md-on-secondary-container: #E8DEF8;
--md-tertiary: #EFB8C8;
--md-tertiary-container: #633B48;
--md-on-tertiary-container: #FFD8E4;
--md-surface: #1C1B1F;
--md-surface-variant: #49454F;
--md-surface-container: #211F26;
--md-surface-container-high: #2B2930;
--md-on-surface: #E6E1E5;
--md-on-surface-variant: #CAC4D0;
--md-outline: #938F99;
--md-outline-variant: #49454F;
--md-error: #F2B8B5;
--md-error-container: #8C1D18;
--md-on-error-container: #F9DEDC;
--md-warning-container: #4A2F0A;
--md-on-warning-container: #FCD4A0;
--md-success-container: #0A2E1C;
--md-on-success-container: #9EEFC0;
```

---

## Typography

Add to `index.css` font import:
```css
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;500&display=swap');
```

Replace the existing `font-family` in `body`:
```css
body { font-family: 'Roboto', sans-serif; }
```

| Role | Size | Weight | Usage |
|---|---|---|---|
| Display / page title | 28px | 400 | `<h1>` page headers |
| Title large | 22px | 400 | Top App Bar title |
| Title medium | 16px | 500 | Card titles, section headings |
| Body medium | 14px | 400 | Body copy, descriptions |
| Label large | 14px | 500 | Buttons, prominent chips |
| Label small / eyebrow | 11px | 500 | Uppercase eyebrow labels |
| Mono | 12px | 400 | IDs, code (`Roboto Mono`) |

---

## Layout & Navigation

### Top App Bar (`Header.jsx`)
- Height: 64px
- Background: `surface-container`
- Border: `1px solid outline-variant` on bottom
- Left: 80px purple (`primary`) logo block with white "ACOS" wordmark
- Center: page title 22px weight 400
- Right: search bar (surface-variant bg, 28px border-radius, 40px tall) + user avatar circle

### Navigation Rail (`Sidebar.jsx` + `Layout.css`)
- Width: **80px** (replaces current 256px drawer)
- Background: `surface-container-high`
- Border: `1px solid outline-variant` on right
- Items: 64px wide, 16px border-radius container
  - Icon: 20×20px, centered in a 40×28px indicator pill
  - Label: 11px, 500 weight, below icon
  - **Active** state: indicator pill background `secondary-container`; label and icon color `primary`
  - **Hover** state: indicator pill background `rgba(primary, 0.08)`
- Mobile: keeps existing overlay drawer (no change to mobile behaviour)

`Layout.css` change: set `.sidebar-desktop { width: 80px; }` (was 256px). The interior nav item structure is owned by `Sidebar.jsx`.

### Main content area
- Background: `surface`
- `overflow-y: auto`, `padding: 24px`

---

## Components

### Cards
Applies to Agents, Skills, Workflows, and any `glass-card` usage.
- Background: `surface-container`
- Border-radius: `16px`
- Border: `1px solid transparent` default → `1px solid outline-variant` on hover
- Box-shadow on hover: `0 2px 8px rgba(0,0,0,0.12)` (light), `0 2px 8px rgba(0,0,0,0.4)` (dark)
- Remove all `backdrop-filter: blur(...)` glass effects

### Buttons (`Button.jsx` + inline usages)
| Variant | Background | Text | Border-radius | Height |
|---|---|---|---|---|
| Filled (primary CTA) | `primary` | `on-primary` | 20px | 40px |
| Tonal (secondary) | `secondary-container` | `on-secondary-container` | 20px | 40px |
| Outlined | transparent | `primary` | 20px, `1px solid outline` | 40px |
| Text | transparent | `primary` | 20px | 40px |

### Status chips
Use semantic tokens — no raw hex in JSX.
| State | Background token | Text token |
|---|---|---|
| Healthy | `success-container` | `on-success-container` |
| Degraded / Disabled | `warning-container` | `on-warning-container` |
| Error | `error-container` | `on-error-container` |

### Filter chips
- Border: `1px solid outline-variant`, border-radius: `8px`, height: `32px`
- Active: background `secondary-container`, border-color `primary`, text `on-secondary-container`

### Summary / metric cards (top of list pages + `MetricsCard.jsx`)
Four tonal cards in a flex row, `border-radius: 16px`, `padding: 16px 20px`:
- Card 1: `primary-container` / `on-primary-container`
- Card 2: `secondary-container` / `on-secondary-container`
- Card 3: context-dependent (warning for counts, tertiary for scores)
- Card 4: `surface-container-high` / `on-surface`

### Form inputs (`ExperimentForm.jsx` text fields)
- Background: `surface-variant`
- Border-radius: `4px 4px 0 0` (M3 filled text field)
- Bottom border: `2px solid primary` on focus, `1px solid outline` default
- Label: 12px, `primary` color when focused

### Tables (Workflows, Skills)
- Container: `surface-container` bg, `16px` border-radius
- Header row: `surface-container-high` bg, label-small text
- Data rows: `surface` bg on hover, no horizontal borders (use `12px` row padding for spacing)
- Remove `.glass-table-wrap` background and border-image styles

---

## Files to Change

### CSS / config
| File | Change |
|---|---|
| `src/index.css` | Add Roboto font import; replace all CSS vars with M3 tokens (light + dark) |
| `tailwind.config.js` | Extend colors with M3 token mappings |
| `src/App.css` | Update global classes to use M3 tokens; remove glass/blur effects |
| `src/pages/Lists.css` | Update table, modal, skeleton, button classes to M3 tokens |
| `src/pages/Simulation.css` | Update any button/chip color classes |
| `src/components/Layout.css` | Change `.sidebar-desktop { width: 256px }` → `80px` |

### Components
| File | Change |
|---|---|
| `src/components/Header.jsx` | Rebuild as Top App Bar (logo block + title + search + avatar) |
| `src/components/Sidebar.jsx` | Rebuild nav items as Navigation Rail (icon pill + label, active indicator) |
| `src/components/Layout.jsx` | Update wrapper Tailwind classes for M3 surface tokens |
| `src/components/Button.jsx` | Implement 4 M3 button variants (filled, tonal, outlined, text) |
| `src/components/MetricsCard.jsx` | Replace current card bg with tonal container pattern |
| `src/pages/Agents.jsx` | Summary row + card grid + filter chips with M3 tokens |
| `src/pages/Skills.jsx` | Same card/chip pattern as Agents |
| `src/pages/WorkflowRegistry.jsx` | Update table styles, modal, buttons |
| `src/pages/Analytics.jsx` | Update metric cards and chart container backgrounds |
| `src/pages/Experiments.jsx` | Update layout; delegate form/results to subcomponents |
| `src/components/ExperimentForm.jsx` | M3 text fields, tonal button |
| `src/components/ExperimentResults.jsx` | M3 card and table styles |
| `src/pages/Simulation.jsx` | Button/chip styles only; no layout changes |

### Not changed
| File | Reason |
|---|---|
| `src/components/ThemeProvider.jsx` | Already toggles `dark` class on `<html>` correctly |
| `src/lib/theme.jsx` | No change needed |
| `src/components/WorkflowCanvas.jsx` | ReactFlow canvas node styling is out of scope |
| All API/backend files | Out of scope |

---

## Out of Scope

- ReactFlow canvas node and edge styling
- Backend / API changes
- New features or pages
- Ripple / ink animation effects
- Mobile Navigation Bottom Bar (current mobile overlay drawer unchanged)
