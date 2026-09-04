
## 2024-05-21 - MemoryPressureBanner Dismiss Button
**Learning:** Icon-only custom buttons (like those often used in dismissing banners) sometimes omit proper keyboard focus styles (`focus-visible:ring-...`) and tooltips (`title` attribute) even if they have an `aria-label`.
**Action:** Always ensure that custom icon buttons have explicit `focus-visible` utility classes and a `title` attribute so they are fully accessible for both keyboard navigation and mouse hover.
