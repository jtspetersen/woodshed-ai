# Woodshed AI — Design System v1.0

> **Reference document for development.** Hand this to Claude Code alongside the project brief when building UI components.

---

## Mood & Concept

**Vintage Analog Studio** — warm, textured, inviting. Think tube amps glowing in a dim room, worn wooden furniture, VU meters bouncing. The app should feel like a comfortable workshop where you make music, not a sterile SaaS dashboard.

**Key words:** warm, rounded, approachable, analog, crafted, honest, musical

---

## Logo

**Format:** Icon + Wordmark

**Icon:** A geometric shed shape (triangular roof flowing into a rounded-rectangle body as one unified path) with two musical eighth notes centered inside the shed body. Represents both the "woodshed" (practice space) and music (notes within).

**Wordmark:** "Woodshed" in Nunito 800, "AI" in Nunito 600 at reduced opacity (0.6). The "AI" is secondary — this is a music tool first.

**SVG Layer Order (critical for uniform stroke weight):**
1. Body fill — `fill="#3D3229"`, no stroke
2. Roof fill — `fill="#4A3B2E"`, no stroke (subtle depth)
3. Eave line — decorative, inset slightly from edges, low opacity
4. Notes — two eighth notes centered in the shed body (x≈32, y≈42)
5. **Outline — drawn LAST** — single `fill="none"` path with `stroke-width="2.5"` so roof, walls, and floor all share identical weight

**Note positioning:**
- Left note: ellipse at (24.5, 45.5), stem up to y=34, flag curving right. Opacity 0.9
- Right note: ellipse at (37.5, 43), stem up to y=33, flag curving right. Opacity 0.7
- At small sizes (≤28px): simplify to note heads + stems only (no flags), thicker strokes
- At tiny sizes (16px/favicon): note heads only as simple dots

**Usage rules:**
- Always maintain spacing between icon and wordmark
- Minimum size: 20px icon height (x-small variant)
- Default size: 40px icon height
- Dark variant: amber outline + amber notes on dark fill
- Light variant: dark amber (`#A66A08`) outline + notes on light fill (`#EDE8E3`)
- Icon can be used standalone at 40px+ for favicons, app icons

**Dark variant SVG (default — paste-ready):**
```svg
<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M8 28L32 10L56 28V52C56 54.2091 54.2091 56 52 56H12C9.79086 56 8 54.2091 8 52V28Z" fill="#3D3229"/>
  <path d="M8 28L32 10L56 28Z" fill="#4A3B2E"/>
  <line x1="10" y1="28" x2="54" y2="28" stroke="#F5A623" stroke-width="1" opacity="0.3"/>
  <g opacity="0.9"><ellipse cx="24.5" cy="45.5" rx="3.2" ry="2.4" fill="#FCBF6A" transform="rotate(-15 24.5 45.5)"/><line x1="27.2" y1="44.5" x2="27.2" y2="34" stroke="#FCBF6A" stroke-width="1.8" stroke-linecap="round"/><path d="M27.2 34C27.2 34 30 35.2 32 37.5" stroke="#FCBF6A" stroke-width="1.4" stroke-linecap="round" fill="none"/></g>
  <g opacity="0.7"><ellipse cx="37.5" cy="43" rx="3.2" ry="2.4" fill="#FCBF6A" transform="rotate(-15 37.5 43)"/><line x1="40.2" y1="42" x2="40.2" y2="33" stroke="#FCBF6A" stroke-width="1.8" stroke-linecap="round"/><path d="M40.2 33C40.2 33 42.8 34 44.5 36" stroke="#FCBF6A" stroke-width="1.4" stroke-linecap="round" fill="none"/></g>
  <path d="M8 28L32 10L56 28V52C56 54.2091 54.2091 56 52 56H12C9.79086 56 8 54.2091 8 52V28Z" fill="none" stroke="#F5A623" stroke-width="2.5" stroke-linejoin="round"/>
</svg>
```

**Light variant SVG (paste-ready):**
```svg
<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M8 28L32 10L56 28V52C56 54.2091 54.2091 56 52 56H12C9.79086 56 8 54.2091 8 52V28Z" fill="#EDE8E3"/>
  <path d="M8 28L32 10L56 28Z" fill="#DDD5CE"/>
  <line x1="10" y1="28" x2="54" y2="28" stroke="#A66A08" stroke-width="1" opacity="0.2"/>
  <g opacity="0.85"><ellipse cx="24.5" cy="45.5" rx="3.2" ry="2.4" fill="#A66A08" transform="rotate(-15 24.5 45.5)"/><line x1="27.2" y1="44.5" x2="27.2" y2="34" stroke="#A66A08" stroke-width="1.8" stroke-linecap="round"/><path d="M27.2 34C27.2 34 30 35.2 32 37.5" stroke="#A66A08" stroke-width="1.4" stroke-linecap="round" fill="none"/></g>
  <g opacity="0.6"><ellipse cx="37.5" cy="43" rx="3.2" ry="2.4" fill="#A66A08" transform="rotate(-15 37.5 43)"/><line x1="40.2" y1="42" x2="40.2" y2="33" stroke="#A66A08" stroke-width="1.8" stroke-linecap="round"/><path d="M40.2 33C40.2 33 42.8 34 44.5 36" stroke="#A66A08" stroke-width="1.4" stroke-linecap="round" fill="none"/></g>
  <path d="M8 28L32 10L56 28V52C56 54.2091 54.2091 56 52 56H12C9.79086 56 8 54.2091 8 52V28Z" fill="none" stroke="#A66A08" stroke-width="2.5" stroke-linejoin="round"/>
</svg>
```

---

## Color Palette

### Primary — Amber (the "tube glow")
| Token        | Hex       | Use |
|-------------|-----------|-----|
| `amber-50`  | `#FFF8F0` | Light theme backgrounds |
| `amber-100` | `#FEECD2` | Primary text on dark bg |
| `amber-200` | `#FDD9A5` | Secondary headings |
| `amber-300` | `#FCBF6A` | Hover states, highlights |
| `amber-400` | `#F5A623` | **Primary brand color** — buttons, logo, accents |
| `amber-500` | `#D4890A` | Primary on light backgrounds |
| `amber-600` | `#A66A08` | Darkest amber, borders on light |

### Neutrals — Bark (the "wood" tones)
| Token        | Hex       | Use |
|-------------|-----------|-----|
| `bark-50`   | `#F7F4F1` | Light theme background |
| `bark-100`  | `#EDE8E3` | Light surface alt |
| `bark-200`  | `#DDD5CE` | Light borders |
| `bark-300`  | `#C4B9AF` | Disabled text (light) |
| `bark-400`  | `#A89A8D` | Muted text (dark theme) |
| `bark-500`  | `#87776A` | Dim text, labels |
| `bark-600`  | `#6B5B4B` | Borders (dark theme) |
| `bark-700`  | `#524538` | Surface alt (dark theme) |
| `bark-800`  | `#3D3229` | **Surface** (dark theme cards, panels) |
| `bark-900`  | `#2A211B` | **Background** (dark theme base) |
| `bark-950`  | `#1A1310` | Deepest dark, text on light |

### Accents
| Token        | Hex       | Use |
|-------------|-----------|-----|
| `rust-500`  | `#C75C3A` | Errors, destructive actions |
| `rust-400`  | `#E06D45` | Warnings, "unresolved" tags |
| `rust-300`  | `#F08A66` | Lighter rust for hover states |
| `sage-500`  | `#5E8C6A` | Success states |
| `sage-400`  | `#7AAB87` | "Connected", "resolved" indicators |
| `sage-300`  | `#99C4A5` | Lighter sage for backgrounds |

### Semantic Mapping (Dark Theme — Default)
```css
--color-bg:            var(--bark-900);     /* Page background */
--color-surface:       var(--bark-800);     /* Cards, panels */
--color-surface-alt:   var(--bark-700);     /* Elevated surfaces */
--color-border:        var(--bark-600);     /* Default borders */
--color-text:          var(--amber-100);    /* Primary text */
--color-text-muted:    var(--bark-400);     /* Secondary text */
--color-text-dim:      var(--bark-500);     /* Tertiary text */
--color-primary:       var(--amber-400);    /* CTA, brand accent */
--color-primary-hover: var(--amber-300);    /* Hover state */
--color-accent:        var(--rust-400);     /* Attention / warning */
--color-success:       var(--sage-400);     /* Positive states */
--color-error:         var(--rust-500);     /* Error states */
```

---

## Typography

### Font Stack
| Role     | Font           | Weights    | Use |
|----------|---------------|------------|-----|
| Display  | **Nunito**     | 600, 700, 800 | Headings, titles, button labels, logo |
| Body     | **Nunito Sans** | 400, 500, 600 | Body text, descriptions, chat messages |
| Mono     | **JetBrains Mono** | 400, 500 | Chord symbols, Roman numerals, scales, MIDI data, code |

### Google Fonts Import
```
https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Nunito+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap
```

### Type Scale
| Token     | Size     | Typical use |
|-----------|----------|-------------|
| `text-xs` | 0.75rem  | Captions, metadata, status |
| `text-sm` | 0.875rem | Labels, secondary text, chips |
| `text-base` | 1rem   | Body text default |
| `text-lg` | 1.125rem | Subheadings, card titles |
| `text-xl` | 1.25rem  | Section headers |
| `text-2xl` | 1.5rem  | Page section titles |
| `text-3xl` | 1.875rem | Feature titles |
| `text-4xl` | 2.25rem | Hero headings |
| `text-5xl` | 3rem    | App title / splash |

### Special Rule — Musical Notation Inline
Any chord symbol, Roman numeral, scale name, or technical music data that appears inline in body text should use the **mono font** styled as a "chord tag":
```css
.chord-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 500;
  background: rgba(245, 166, 35, 0.15);
  color: #FCBF6A;  /* amber-300 */
  padding: 1px 6px;
  border-radius: 6px;
}
```

---

## Voice & Tone

### Personality: "The session musician friend"
Woodshed AI sounds like a knowledgeable musician who genuinely loves helping people learn and create. They know deep theory but explain it in plain language. They get excited about good ideas and are honest (but kind) about what doesn't work.

### Four Pillars

1. **Encouraging** — Validate the user's starting point. Every idea is worth exploring. Lead with what's working before suggesting changes.

2. **Knowledgeable** — Theory-grounded and precise. Always explain *why* something works, not just *what* to do. Show your reasoning.

3. **Playful** — Music is fun. Use conversational language, light humor, and musical metaphors. Avoid academic stiffness.

4. **Honest** — If something clashes or doesn't work, say so gently. Offer alternatives. Don't just validate everything.

### Do / Don't

| Do | Don't |
|----|-------|
| "That progression has a great pull — here's why..." | "According to music theory, you should..." |
| "Try swapping G for G7 — it'll want to resolve more." | "That's wrong. The correct chord is..." |
| "Nice instinct! That's modal interchange." | "As an AI language model, I can help with..." |
| "Here are three ways to take this." | "Here is a comprehensive analysis of your harmonic..." |
| "Ooh, a tritone sub? Getting spicy." | "The tritone substitution is defined as..." |

### Error Messages
Even errors should feel warm:
- "Can't reach Ollama — is it running? Fire it up and I'll be ready to jam."
- "Hmm, I don't recognize that chord symbol. Double-check the spelling?"
- "The knowledge base is still loading — give it a sec, we're warming up the tubes."

---

## Spacing

Use an 4px base grid:
| Token | Value |
|-------|-------|
| `space-1` | 0.25rem (4px) |
| `space-2` | 0.5rem (8px) |
| `space-3` | 0.75rem (12px) |
| `space-4` | 1rem (16px) |
| `space-6` | 1.5rem (24px) |
| `space-8` | 2rem (32px) |
| `space-10` | 2.5rem (40px) |
| `space-12` | 3rem (48px) |
| `space-16` | 4rem (64px) |

---

## Border Radii

| Token | Value | Use |
|-------|-------|-----|
| `radius-sm` | 6px | Chord tags, small elements |
| `radius-md` | 10px | Inputs, status bars |
| `radius-lg` | 16px | Cards, panels, chat bubbles |
| `radius-xl` | 24px | Large containers |
| `radius-full` | 9999px | Buttons (pill shape), chips |

---

## Shadows & Effects

| Token | Value | Use |
|-------|-------|-----|
| `shadow-sm` | `0 1px 3px rgba(0,0,0,0.25)` | Subtle elevation |
| `shadow-md` | `0 4px 12px rgba(0,0,0,0.3)` | Cards on hover |
| `shadow-lg` | `0 8px 30px rgba(0,0,0,0.35)` | Modals, popovers |
| `shadow-glow` | `0 0 20px rgba(245,166,35,0.15)` | Primary button hover (amber glow) |

### Noise Texture
Apply a subtle SVG noise overlay to the `body::before` pseudo-element at very low opacity (0.03) for vintage texture. This should be `pointer-events: none` and `position: fixed`.

---

## Starter Components

### Buttons
- **Primary:** Amber fill, dark text, pill shape, amber glow on hover
- **Secondary:** Transparent, amber text, bark border, amber border on hover
- **Ghost:** Transparent, muted text, no border, subtle bg on hover
- **Danger:** Transparent, rust text, rust border
- **Sizes:** `btn-sm`, default, `btn-lg`

### Text Input
- Dark inset background (`bark-900`), `bark-600` border
- On focus: amber border + amber glow ring (`box-shadow: 0 0 0 3px rgba(245,166,35,0.15)`)

### Chat Bubbles
- **User:** `bark-700` background, right-aligned, bottom-right corner squared
- **Assistant:** `bark-900` background with `bark-700` border, left-aligned, bottom-left corner squared
- Musical terms inside chat use `.chord-tag` styling

### Chips / Tags
- Pill-shaped, mono font, small
- Variants: default (neutral), `amber` (keys/analysis), `sage` (positive), `rust` (tension/warning)

### Cards
- `bark-800` surface, `bark-700` border, `radius-lg`
- Hover: lighter border + medium shadow

### Status Bar
- Horizontal row of status items with colored dots (sage=ok, amber=warning, rust=error)
- Mono font, xs size, dark inset background

### VU Meter (Decorative)
- Animated bars in sage → amber → rust gradient
- Use as loading/thinking indicator instead of a spinner
- Pulsing scale animation

### Hint Box
- Soft amber background tint with amber left border
- Info icon + helpful text
- Use for onboarding tips and usage suggestions

---

## Transitions

| Token | Value | Use |
|-------|-------|-----|
| `ease-out` | `cubic-bezier(0.25, 0.46, 0.45, 0.94)` | All transitions |
| `duration-fast` | 150ms | Hover states, focus rings |
| `duration-normal` | 250ms | Most interactions |
| `duration-slow` | 400ms | Page transitions, reveals |

---

## Gradio Integration Notes

Gradio's theming system allows custom CSS. When building the Gradio UI (Task 1.7):

1. Use Gradio's `theme` parameter with a custom theme that maps to these tokens
2. Override Gradio's default CSS with a custom stylesheet matching this system
3. Key overrides: background colors, font families, border radii, input styles
4. The chat component should use custom CSS to match the bubble styles above
5. Add the noise texture overlay via custom CSS injection

---

*This is a living document. Add new components and patterns as the app grows.*
