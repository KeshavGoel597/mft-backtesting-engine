# TODO

- [x] Verify timestamp alignment (Chronological min-heap replayer steps second-by-second)
- [x] Verify execution policy (Market orders fill at Bid/Ask or Mid-price accurately)
- [x] Verify strike tie-breaking (Lower strike selected when equidistant from futures price)
- [x] Benchmark replay performance (Full 21 days completed in ~10 minutes, ~30s/day wall time)
- [x] Add tests (Coverage for domain models, filename parsing, and registry selector logic)