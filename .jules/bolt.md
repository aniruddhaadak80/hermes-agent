## 2024-05-24 - Holographic Memory Optimization
**Learning:** Python loops executing struct.unpack and list comprehensions converting numpy vectors into python objects (e.g. `[np.exp(1j * v) for v in vectors]`) are serious performance bottlenecks inside core math functions compared to numpy's native C vectorization.
**Action:** When working on numerical/AI representations, immediately look for ways to rewrite element-wise list comprehensions using native `numpy` vectorization such as `numpy.stack`, `numpy.frombuffer`, and `bytearray` building instead of standard list appending.

## 2024-05-18 - Missing Memoization in Custom Markdown Renderer
**Learning:** In highly dynamic UI contexts like chat interfaces where message streams or parent state updates can cause frequent renders, custom complex view components (like parsed Markdown) must be wrapped in `React.memo` unless they specifically rely on deep changing props. The `Markdown` component in `web/src/components/Markdown.tsx` was a primary candidate for this to avoid large-scale re-rendering of long static chat histories on unrelated updates.
**Action:** When inspecting list-based view components handling dense text/media, always verify if leaf components are properly memoized to prevent O(N) rendering where N is the length of the list, especially if they are state-agnostic rendering components.
