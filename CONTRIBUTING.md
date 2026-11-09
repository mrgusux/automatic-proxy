# Contributing to Automatic Proxy

Thank you for your interest in contributing to **Automatic Proxy**! We welcome bug reports, new upstream source suggestions, performance enhancements, and documentation improvements.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mrgusux/automatic-proxy.git
   cd automatic-proxy
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install pytest pytest-asyncio
   ```

3. **Set up Next.js Website**:
   ```bash
   cd website
   npm install
   npm run dev
   ```

## Running Tests

- Run core validation tests:
  ```bash
  pytest -v tests/
  ```
- Run Next.js website tests & typecheck:
  ```bash
  cd website
  npm test
  npm run lint
  ```

## Code Guidelines

- **Python**: Follow PEP 8 and strict type hinting (`src/proxy_validator/`). All async network code must enforce connection timeouts and handle unclosed socket cleanups.
- **Next.js & Frontend**: React 19, Next.js 16 App Router, Turbopack, Tailwind CSS 4. Keep client components as leaf nodes.
- **Git Commits**: Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `perf:`, `test:`, `ci:`).

## Pull Request Process

1. Fork the repo and create your feature branch: `git checkout -b feat/my-new-feature`.
2. Ensure all tests pass and code compiles without type errors.
3. Open a Pull Request pointing to `main` with a clear explanation of changes.
