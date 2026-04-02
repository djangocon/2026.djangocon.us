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

### Custom Shadows

Use the predefined shadow utilities for buttons:
- `shadow-button` - default state
- `shadow-button-hover` - hover state
- `shadow-button-active` - active state
