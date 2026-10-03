# Original teaching source: three independent ideas

This small, original teaching fixture has three separate lessons. It is not an extract from a course, textbook or institution. Page identifiers are stable locators for a reproducible notes-authoring exercise. The intended reader is a beginner. Create explanatory notes and a keyword/concept Quick Reference; do not infer missing material from the page headings.

## Page P1: Average speed

Average speed describes an entire interval. Divide total distance travelled by elapsed time, including any pauses. Elapsed time must be positive. With distance in metres and time in seconds, the result is in metres per second. A traveller covers 60 m from A to B, then 120 m from B to C, in 12 s altogether. Thus total distance is 180 m and average speed is 15 m/s. Multiplying 15 m/s by 12 s recovers 180 m.

The average does not specify speed at any instant or the maximum speed. For unequal speeds on two parts, their arithmetic mean equals the whole-trip average only when the two durations are equal. In the example, 60 m at 10 m/s takes 6 s, and 120 m at 20 m/s also takes 6 s. Total distance differs from displacement: a round trip can have positive distance and zero displacement.

Useful recall words: average speed, mean speed, distance, elapsed time, units. Source gap: no method for estimating measurement uncertainty is supplied. Keep that gap visible rather than inventing a numerical uncertainty claim.

## Page P2: Rectangle area

Area measures a two-dimensional region. A 3 m by 2 m rectangle can be tiled by six 1 m by 1 m squares, without gaps or overlaps. Its area is 6 m². In general, A = w × h for positive rectangle side lengths w and h. The rule also applies when side lengths are not integers. Length units must be compatible: convert 200 cm to 2 m before multiplying by 3 m. The result is 6 m², not 600 m².

If both dimensions are scaled by a positive factor k, area is multiplied by k². Doubling only one dimension doubles the area; doubling both quadruples it. Perimeter is a different quantity: the 3 m by 2 m rectangle has perimeter 2 × (3 + 2) = 10 m. Surface covering needs area; edging needs perimeter. Two adjacent side lengths alone do not determine the area of an arbitrary quadrilateral.

Useful recall words: area, unit square, scaling, dimensions, perimeter, units.

## Page P3: Stack behaviour

A stack exposes operations at one end, the top. Push adds an item there; pop removes and returns the top item. This gives last-in, first-out ordering, abbreviated LIFO. A stack specifies observable behaviour rather than a unique storage layout; arrays and linked structures are possible implementations.

Write a stack from bottom to top, with the top at the right. Starting empty, push A to obtain [A], then push B to obtain [A, B]. A pop returns B and leaves [A]. A second pop returns A and leaves an empty stack. A third pop has no stored item to return. The interface must define its empty-stack response, such as an error or an explicit empty result. This fixture does not choose an implementation or prescribe one particular response.

Check both returned values and the remaining state. A FIFO queue would return A before B, so the same two inputs distinguish the removal order. If an implementation has fixed capacity, overflow behaviour needs a separate test.

Useful recall words: stack, LIFO, push, pop, removal order, empty collection, capacity.
