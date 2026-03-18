# CI/CD Pipeline Setup Guide

## 📋 Overview

This document describes the complete CI/CD pipeline setup for the **resilient-backend** repository.

---

## 🚀 GitHub Actions Workflows

### 1. **CI Pipeline** (`.github/workflows/ci.yml`)

**Triggers**: Push to `main`/`develop`, Pull Requests

**Jobs**:

#### a. **Lint Job**
- Runs **ruff** (fast Python linter)
- Checks code formatting with **black**
- Validates import sorting with **isort**
- Performs type checking with **mypy**
- All checks set to `continue-on-error: true` (non-blocking for initial setup)

#### b. **Test Job**
- Matrix testing on **Python 3.9** and **3.12**
- Installs all dependencies from `requirements.txt`
- Runs full test suite with **pytest**
- Generates code coverage reports (term, XML, HTML)
- Uploads coverage to **Codecov** (requires `CODECOV_TOKEN` secret)
- Archives HTML coverage reports as artifacts

#### c. **Security Job**
- Runs **bandit** (Python security linter)
- Checks for vulnerable dependencies with **safety**
- Uploads security reports as artifacts
- Non-blocking by default

#### d. **Build Job**
- Verifies the API can be imported
- Compiles all Python files to check for syntax errors
- Runs only after lint and test jobs pass

#### e. **Dependency Review**
- Runs on Pull Requests only
- Scans for high-severity vulnerabilities in dependency changes

---

### 2. **Security Scanning** (`.github/workflows/security.yml`)

**Triggers**: 
- Weekly schedule (Mondays at 9 AM UTC)
- Push to `main`
- Manual dispatch

**Jobs**:

#### a. **CodeQL Analysis**
- GitHub's semantic code analysis
- Scans for security vulnerabilities
- Uploads results to GitHub Security tab

#### b. **Secret Scanning**
- Uses **TruffleHog** to detect exposed secrets
- Scans commit history for credentials

#### c. **Dependency Vulnerability Scan**
- Runs **pip-audit** and **safety**
- Generates vulnerability reports
- Archives reports for 30 days

#### d. **Docker Security Scan**
- Builds a temporary Docker image
- Scans with **Trivy** (vulnerability scanner)
- Uploads SARIF results to GitHub Security

---

### 3. **Deployment** (`.github/workflows/deploy.yml`)

**Triggers**: 
- Push to `main`
- Version tags (`v*`)
- Manual dispatch

**Jobs**:

#### a. **Deploy to Railway**
- Automatically deploys to Railway on main branch pushes
- Requires `RAILWAY_TOKEN` secret
- Environment: `production`

#### b. **Create GitHub Release**
- Triggered by version tags (e.g., `v1.2.3`)
- Auto-generates changelog from git commits
- Creates release notes

#### c. **Docker Build & Push**
- Builds Docker image on main/tag pushes
- Pushes to Docker Hub
- Tags: `latest`, branch name, SHA, tag version
- Requires `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets

---

### 4. **Release Management** (`.github/workflows/release.yml`)

**Trigger**: Manual workflow dispatch

**Features**:
- Semantic versioning (major/minor/patch)
- Automatic changelog generation
- Git tag creation
- GitHub release with install instructions
- Pre-release option

**Usage**:
1. Go to Actions → Release Management
2. Click "Run workflow"
3. Select version bump type
4. Optionally mark as pre-release

---

## 🔧 Configuration Files

### `pytest.ini`
- Test discovery patterns
- Coverage settings
- Exclusions for non-test files

### `pyproject.toml`
- **black**: Line length 100, Python 3.12 target
- **isort**: Black-compatible profile
- **ruff**: Comprehensive linting rules
- **mypy**: Type checking configuration
- **bandit**: Security scanning settings

### `.pre-commit-config.yaml`
Pre-commit hooks for local development:
- Trailing whitespace removal
- YAML/JSON validation
- Large file detection
- ruff, black, isort, mypy
- bandit security checks

**Setup**:
```bash
pip install pre-commit
pre-commit install
```

### `.github/dependabot.yml`
- Weekly dependency updates (Mondays 9 AM)
- Groups related packages together
- Auto-creates PRs for security updates

---

## 🔐 Required GitHub Secrets

Set these in: `Settings → Secrets and variables → Actions`

| Secret Name | Description | Required For |
|-------------|-------------|--------------|
| `CODECOV_TOKEN` | Codecov upload token | Code coverage reports |
| `RAILWAY_TOKEN` | Railway CLI token | Deployment to Railway |
| `DOCKER_USERNAME` | Docker Hub username | Docker image publishing |
| `DOCKER_PASSWORD` | Docker Hub password/token | Docker image publishing |

---

## 🎯 Setting Up the Pipeline

### 1. Enable GitHub Actions
```bash
cd resilient-backend
git add .github/ pytest.ini pyproject.toml .pre-commit-config.yaml
git commit -m "ci: add comprehensive CI/CD pipeline"
git push origin main
```

### 2. Configure Secrets
1. Go to repository **Settings → Secrets → Actions**
2. Add the required secrets listed above
3. (Optional) Add `CODECOV_TOKEN` from [codecov.io](https://codecov.io)

### 3. Enable Dependabot
1. Go to **Settings → Security → Dependabot**
2. Enable "Dependabot alerts"
3. Enable "Dependabot security updates"

### 4. Review First Run
1. Go to **Actions** tab
2. Check CI workflow execution
3. Review any failures and adjust

---

## 📊 Monitoring & Badges

Add these badges to your `README.md`:

```markdown
[![CI Pipeline](https://github.com/dizzy1900/resilient-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/dizzy1900/resilient-backend/actions/workflows/ci.yml)
[![Security Scan](https://github.com/dizzy1900/resilient-backend/actions/workflows/security.yml/badge.svg)](https://github.com/dizzy1900/resilient-backend/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/dizzy1900/resilient-backend/branch/main/graph/badge.svg)](https://codecov.io/gh/dizzy1900/resilient-backend)
```

---

## 🐛 Troubleshooting

### Tests Failing in CI
```bash
# Run locally to debug
pytest tests/ -v --cov=.

# Check Python version compatibility
python --version  # Should be 3.9 or 3.12
```

### Import Errors
```bash
# Verify all dependencies installed
pip install -r requirements.txt

# Check for missing test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock httpx
```

### Linting Failures
```bash
# Auto-fix most issues
ruff check . --fix
black .
isort .

# Check what would change
ruff check .
black --check --diff .
```

### Docker Build Fails
```bash
# Test locally
docker build -t resilient-backend:test .
docker run -p 8000:8000 resilient-backend:test
```

---

## 🔄 Workflow Optimization

### Speed Improvements
1. **Caching**: pip dependencies cached via `actions/setup-python`
2. **Parallel Jobs**: Lint, test, and security run in parallel
3. **Matrix Strategy**: Python versions tested simultaneously

### Cost Reduction
1. Use `continue-on-error: true` for non-critical checks
2. Limit test matrix to essential Python versions
3. Schedule heavy jobs (security scans) weekly instead of per-commit

---

## 📈 Next Steps

1. ✅ **Increase test coverage** to >80%
2. ✅ **Enable CodeQL** for advanced security analysis
3. ✅ **Set up staging environment** for pre-production testing
4. ✅ **Add performance benchmarks** to CI
5. ✅ **Configure automatic rollback** on deployment failures

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [pre-commit Documentation](https://pre-commit.com/)
- [Railway Documentation](https://docs.railway.app/)

---

**Last Updated**: 2026-03-17  
**Maintained by**: AdaptMetric Team
