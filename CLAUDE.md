# Claude Code Rules

## Tailwind CSS Organization

When writing `@apply` directives, organize classes by category with each category on its own line:

1. **Position** - `relative`, `absolute`, `fixed`, `sticky`, `z-*`
2. **Flex/Layout** - `flex`, `grid`, `items-*`, `justify-*`, `align-*`, `flex-row`, `flex-col`
3. **Spacing** - `p-*`, `m-*`, `gap-*`, padding and margin utilities
4. **Typography** - `font-*`, `text-*`, `leading-*`, `tracking-*`, `uppercase`, `lowercase`
5. **Borders & Decoration** - `border-*`, `rounded-*`, `shadow-*`, `ring-*`
6. **Transitions & Animation** - `transition-*`, `duration-*`, `ease-*`, `animate-*`

### Example

```css
.button {
  @apply relative;
  @apply flex items-center justify-center;
  @apply py-3 px-4 gap-2.5;
  @apply font-bold text-dark-blue uppercase;
  @apply border-[3px] rounded-full shadow-button;
  @apply transition-all duration-[125ms] ease-out;
}
```

### Modifiers

Modifier classes (responsive like `lg:`, `sm:`, `md:`, and state like `hover:`, `focus:`) should always go at the **end** of their `@apply` line — never interleaved with their unprefixed counterparts.

```css
/* good */
@apply py-4 gap-2 lg:p-3;
@apply text-black no-underline hover:text-ocean-blue;

/* avoid */
@apply py-4 lg:p-3 gap-2;
@apply text-black hover:text-ocean-blue no-underline;
```

When an `@apply` directive contains 3 or more modifier classes, pull them onto their own line at the end of the rule:

```css
.site-nav > ul {
  @apply flex flex-col w-full gap-4;
  @apply font-tanker text-2xl text-dark-blue uppercase;
  @apply lg:flex-row lg:items-center lg:justify-end lg:w-auto;
}
```

If there are only one or two modifier classes, they can stay inline with the base classes for that category — but still at the end of the line.

### Custom Shadows

Use the predefined shadow utilities for buttons:
- `shadow-button` - default state
- `shadow-button-hover` - hover state
- `shadow-button-active` - active state
