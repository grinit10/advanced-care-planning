# Contributing to Advanced Care Planning

Thanks for your interest in contributing! This project is a community-driven
reference architecture for voice AI in healthcare. Every contribution helps.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Commit Conventions](#commit-conventions)
- [Testing](#testing)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
By participating, you agree to uphold its standards.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/advanced-care-planning.git
   cd advanced-care-planning
   ```
3. Create a feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```
4. Set up the development environment (see below)
5. Make your changes
6. Run tests
7. Submit a pull request

## Development Environment

### Prerequisites

- Docker Desktop (for local deployment)
- Python 3.12+ (for agent development outside Docker)
- Node.js 22+ (for frontend development outside Docker)
- An Azure OpenAI resource with a deployed LLM
- A Deepgram API key

### Quick Start

```bash
# 1. Copy environment config
cp .env.example .env
# Edit .env with your API keys

# 2. Start all services
docker compose up -d

# 3. Open the app
open http://localhost:5173
```

### Running Components Locally

**Agent (without Docker):**
```bash
cd agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m agent.main
```

**Frontend (without Docker):**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
advanced-care-planning/
├── agent/                  # Python voice agent
│   ├── main.py            # Entry point
│   ├── acp_agent.py       # VoicePipelineAgent
│   ├── acp_prompts.py     # Prompt loading
│   ├── prompt_loader.py   # YAML prompt + TTS rules
│   ├── prompt.yaml        # ✏️ Edit this to customise the conversation
│   ├── session_store.py   # Redis-backed session storage
│   ├── preference_extractor.py  # LLM-based preference extraction
│   ├── http_server.py     # Session management API
│   ├── audio_recorder.py  # Conversation WAV recording
│   ├── email_sender.py    # Azure Communication Services email
│   └── tests/             # Unit tests
├── frontend/              # React + TypeScript web UI
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # LiveKit connection hook
│   │   ├── styles/        # CSS
│   │   └── lib/           # Utilities
│   └── Dockerfile
├── token-server/          # LiveKit token generation
├── helm/                  # Kubernetes Helm chart
└── docker-compose.yml     # All services
```

## Coding Standards

### Python
- **Formatting:** We use [ruff](https://docs.astral.sh/ruff/) for formatting and linting
- **Run before committing:**
  ```bash
  ruff check agent/
  ruff format agent/
  ```
- **Type hints:** All public functions must have type annotations
- **Docstrings:** Use Google-style docstrings for all public modules and functions
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes

### TypeScript / React
- **Formatting:** We use [Prettier](https://prettier.io/) with the project config
- **Linting:** We use [ESLint](https://eslint.org/) with the project config
- **Run before committing:**
  ```bash
  cd frontend
  npm run lint
  npm run format
  ```
- **Components:** Use functional components with hooks
- **Types:** All props and state must be typed. Avoid `any`.
- **Naming:** `camelCase` for functions/variables, `PascalCase` for components

### Git
- Write meaningful commit messages (see conventions below)
- Keep commits focused on a single change
- Rebase your branch before submitting a PR

## Pull Request Process

1. Ensure your branch is up to date with `master`
2. Run all tests and linting — the CI pipeline will check these
3. Update documentation if you add or change functionality
4. Update `CHANGELOG.md` with your changes
5. Open a pull request with a clear title and description
6. Reference any related issues

### PR Checklist

Before submitting:
- [ ] Code follows the project's coding standards
- [ ] Tests pass (`pytest agent/tests/` + `cd frontend && npm test`)
- [ ] Linting passes (`ruff check agent/` + `cd frontend && npm run lint`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] No new warnings or errors

## Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <short description>

[optional body]

[optional footer]
```

Types:
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `style` — formatting, no code change
- `refactor` — code restructuring
- `test` — adding or updating tests
- `chore` — build, CI, dependencies
- `perf` — performance improvement
- `security` — security fix

Examples:
```
feat: add preference extraction for substitute decision-maker
fix: handle missing audio track gracefully
docs: update architecture diagram
test: add unit tests for session_store
```

## Testing

### Python Tests
```bash
cd agent
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

We aim for:
- **Unit tests** for all utility functions and data layer code
- **Integration tests** for critical flows (session creation, preference extraction)
- **No regressions** — CI will fail if existing tests break

## Reporting Issues

- **Bug reports:** Use the GitHub issue tracker. Include:
  - Steps to reproduce
  - Expected vs actual behaviour
  - Environment details (OS, Docker version, etc.)
  - Logs from `docker compose logs agent`
- **Feature requests:** Open an issue with the "enhancement" label
- **Security vulnerabilities:** See [SECURITY.md](SECURITY.md) — do not open a public issue

## Questions?

Open a [Discussion](https://github.com/YOUR-REPO/advanced-care-planning/discussions)
on GitHub. We're happy to help!