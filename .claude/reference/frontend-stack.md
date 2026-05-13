# Frontend Stack

<!-- REPLACE if your project does NOT have a frontend, OR if your stack differs.
The defaults below represent libraries Claude knows well out of the box. -->

## Component library

**Default:** [shadcn/ui](https://github.com/shadcn-ui/ui) — copy-paste React components on Radix UI + Tailwind. Claude generates these natively.

## Styling

**Default:** [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) — utility-first. Claude generates Tailwind classes natively.

## Icons

**Default:** [Lucide](https://github.com/lucide-icons/lucide) (`lucide-react`). Default icon set in Claude artifacts.

## Charts / data viz

**Default:** [Recharts](https://github.com/recharts/recharts). Default React charts library Claude uses.

## Animated / marketing components (optional)

- [Acternity UI](https://ui.acternity.com)
- [Magic UI](https://magicui.design)

## Bootstrap a new component

When building a new UI component:
1. Use shadcn/ui patterns where possible (check if one already exists for the use case).
2. Tailwind for styling.
3. Lucide for icons.
4. Recharts for any charts.
5. If pixel-perfect mockups are needed, generate with [v0.dev](https://v0.dev) and iterate.

## NOT defaults (consumer overrides)

<!-- REPLACE: list anything you've chosen DIFFERENTLY from the above.
Examples: Mantine instead of shadcn, Chakra instead of Tailwind, Heroicons instead of Lucide. -->
