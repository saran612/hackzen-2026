# Contributing to SkinCV

Thank you for your interest in contributing to **SkinCV**! Whether it's a bug fix, new feature, documentation improvement, or a fresh skin-analysis heuristic, every contribution is welcome.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Submitting Pull Requests](#submitting-pull-requests)
- [Project Structure](#project-structure)
- [Coding Guidelines](#coding-guidelines)
  - [Backend (Python / FastAPI)](#backend-python--fastapi)
  - [Frontend (React / Vite)](#frontend-react--vite)
  - [Computer Vision](#computer-vision)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [License](#license)

---

## Code of Conduct

By participating in this project you agree to treat all contributors with respect and foster an inclusive, harassment-free environment. Be kind, constructive, and professional in all interactions.

---

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/hackzen-2026.git
   cd hackzen-2026
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/saran612/hackzen-2026.git
   ```
4. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

### Backend

```bash
cd backend
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --port 3000 --host 0.0.0.0
```

> **Tip:** The frontend proxies API requests to `localhost:8002` — make sure the backend is running first.

---

## How to Contribute

### Reporting Bugs

- Search existing issues to avoid duplicates.
- Open a new issue with:
  - A clear, descriptive title.
  - Steps to reproduce the bug.
  - Expected vs. actual behavior.
  - Screenshots or logs if applicable.
  - Your environment details (OS, browser, Python/Node versions).

### Suggesting Features

- Open an issue with the **"enhancement"** label.
- Describe the use case, expected behavior, and why it would benefit the project.

### Submitting Pull Requests

1. Ensure your branch is up to date with `main`:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
2. Make your changes following the [Coding Guidelines](#coding-guidelines) below.
3. Test your changes locally (both backend and frontend).
4. Push to your fork and open a Pull Request against `main`.

---

## Project Structure

```
hackzen-2026/
├── backend/               # FastAPI + SQLAlchemy backend
│   ├── app/               # Application source code
│   ├── requirements.txt   # Python dependencies
│   └── ...
├── frontend/              # React + Vite + TailwindCSS v4 frontend
│   ├── src/               # React components, pages, and utilities
│   ├── public/            # Static assets
│   ├── package.json       # Node dependencies
│   └── ...
├── docs/                  # Additional documentation
├── LICENSE                # MIT License
├── README.md              # Project overview & setup
└── CONTRIBUTION.md        # ← You are here
```

---

## Coding Guidelines

### Backend (Python / FastAPI)

- Follow **PEP 8** style conventions.
- Use **type hints** for function signatures.
- Write docstrings for all public functions and API endpoints.
- Keep endpoint logic thin — delegate to service/utility modules.
- Add or update tests in the `backend/` test files when changing logic.

### Frontend (React / Vite)

- Use **functional components** with React Hooks.
- Follow the existing component and page structure under `src/`.
- Use **TailwindCSS v4** utility classes for styling — avoid inline styles.
- Use **Lucide Icons** for any new iconography (consistent with the rest of the UI).
- Keep components focused and reusable.

### Computer Vision

- All CV processing uses **MediaPipe Face Landmarker Tasks API** and **OpenCV**.
- When modifying scoring heuristics or adding new skin concern detectors, document your methodology in `docs/` or in code comments.
- Ensure changes are **skin-tone inclusive** — test across a diverse range of skin tones.

---

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**
```
feat(cv): add dark circle detection heuristic
fix(api): handle missing face landmarks gracefully
docs(readme): update setup instructions for Windows
```

---

## Pull Request Process

1. Ensure your code passes all existing tests.
2. Update documentation if your change affects setup, API, or CV behavior.
3. Fill out the PR template with a clear description of your changes.
4. Link any related issues (e.g., `Closes #12`).
5. A maintainer will review your PR. Please be responsive to feedback.
6. Once approved, your PR will be squash-merged into `main`.

---

## License

By contributing to SkinCV, you agree that your contributions will be licensed under the [MIT License](LICENSE).
