# Testing

## Test Suite

Run all tests:

```bash
pytest -q
```

Current test modules:

- `tests/test_data_loader.py`
- `tests/test_execution_and_strategy.py`

## Coverage Focus

### Data Loader

- Option filename parsing
- Trading day discovery
- Day-level data loading and nearest-expiry behavior
- Strike availability around ATM ranges

### Execution Engine

- Atomic rejection when quotes are stale
- Slippage and fee application

### Strategy Behavior

- Position state updates only on fill confirmations
- End-of-day close generation after confirmed entries

## Recommended Extensions

- Replay engine determinism and timestamp edge cases
- Portfolio PnL reconciliation against hand-calculated fixtures
- Multi-day regression fixtures for stable summary outputs
- End-to-end smoke tests for CSV outputs and plot generation
