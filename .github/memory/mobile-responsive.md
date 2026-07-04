# mobile-responsive

Every new page/table must be mobile-friendly at the 768px breakpoint via the
shared shell: stacked-card layout OR a scroll wrapper for wide tables, never
horizontal overflow. The shared `@media (max-width: 768px)` block in
`frontend/src/styles/tokens.css` wraps the header/rows and makes `.table`
horizontally scrollable. Verify at 768px before calling a page done.
