# Quick Start: CI/CD Pipeline

## ⚡ TL;DR

Your CI/CD pipeline is now ready! Here's what happens automatically:

✅ **On every Push/PR**: Lint, Test, Security Scan  
✅ **On Push to Main**: Deploy to Railway, Build Docker Image  
✅ **Weekly**: Comprehensive Security Audit  
✅ **On Version Tags**: Create GitHub Release

---

## 🚀 Quick Commands

### Run Tests Locally
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock httpx

# Run all tests with coverage
pytest tests/ -v --cov=.

# Run specific test file
pytest tests/test_api_flow.py -v
```

### Run Linters
```bash
# Install linting tools
pip install ruff black isort mypy

# Check code style
ruff check .

# Auto-fix issues
ruff check . --fix
black .
isort .
```

### Set Up Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

---

## 🔑 Required GitHub Secrets

Go to: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Where to Get It | Required? |
|--------|----------------|-----------|
| `CODECOV_TOKEN` | [codecov.io](https://codecov.io) → Add Repo | Optional |
| `RAILWAY_TOKEN` | Railway Dashboard → Settings → Tokens | For deployment |
| `DOCKER_USERNAME` | Docker Hub username | For Docker publishing |
| `DOCKER_PASSWORD` | Docker Hub access token | For Docker publishing |

---

## 📦 Create a New Release

### Option 1: Automatic (Recommended)
1. Go to **Actions** → **Release Management**
2. Click **Run workflow**
3. Choose version bump: `patch` (1.0.0 → 1.0.1), `minor` (1.0.0 → 1.1.0), or `major` (1.0.0 → 2.0.0)
4. ✅ Done! Tag, release notes, and Docker image created automatically

### Option 2: Manual
```bash
# Create and push a version tag
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# GitHub Actions will automatically create the release
```

---

## 🐳 Docker Usage

### Pull and Run
```bash
# Pull latest image
docker pull dizzy1900/resilient-backend:latest

# Run container
docker run -p 8000:8000 \
  -e JWT_SECRET_KEY=your-secret-key \
  dizzy1900/resilient-backend:latest
```

### Build Locally
```bash
# Build from source
docker build -t resilient-backend:local .

# Run local build
docker run -p 8000:8000 resilient-backend:local
```

---

## 🔍 Monitor CI/CD

### Check Workflow Status
1. Go to **Actions** tab in GitHub
2. Select workflow (CI Pipeline, Security, Deploy)
3. View logs and artifacts

### View Coverage Report
1. Go to **Actions** → **CI Pipeline** → Latest run
2. Scroll to **Artifacts**
3. Download `coverage-report-3.12`
4. Open `htmlcov/index.html` in browser

### Check Security Scans
1. Go to **Security** tab → **Code scanning**
2. Review CodeQL alerts
3. Check **Dependabot** for dependency updates

---

## 🛠️ Troubleshooting

### "CI is failing!"
```bash
# Run the same checks locally
pytest tests/ -v
ruff check .
black --check .

# Fix auto-fixable issues
ruff check . --fix
black .
isort .
```

### "Tests pass locally but fail in CI"
- Check Python version: CI uses 3.9 and 3.12
- Check environment variables in workflow
- Review CI logs for missing dependencies

### "Docker build fails"
```bash
# Test Dockerfile locally
docker build -t test .

# Check logs
docker logs <container-id>
```

### "Deployment to Railway failed"
- Verify `RAILWAY_TOKEN` is set in secrets
- Check Railway dashboard for errors
- Ensure `Procfile` exists and is correct

---

## 📊 Add Badges to README

```markdown
[![CI](https://github.com/dizzy1900/resilient-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/dizzy1900/resilient-backend/actions/workflows/ci.yml)
[![Security](https://github.com/dizzy1900/resilient-backend/actions/workflows/security.yml/badge.svg)](https://github.com/dizzy1900/resilient-backend/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/dizzy1900/resilient-backend/branch/main/graph/badge.svg)](https://codecov.io/gh/dizzy1900/resilient-backend)
```

---

## 🎯 Next Steps

1. **Push to GitHub** to trigger first CI run
2. **Add secrets** for deployment and coverage
3. **Review first workflow run** in Actions tab
4. **Fix any failing tests** or linting issues
5. **Enable branch protection** to require CI before merge

---

## 📁 Files Created

```
.github/
  workflows/
    ci.yml              # Main CI pipeline
    security.yml        # Security scanning
    deploy.yml          # Deployment automation
    release.yml         # Release management
  dependabot.yml        # Dependency updates

pytest.ini              # Pytest configuration
pyproject.toml          # Linting & tool config
.pre-commit-config.yaml # Pre-commit hooks
.gitignore              # Updated exclusions
CI_CD_SETUP.md          # Detailed documentation
QUICK_START_CI_CD.md    # This file
```

---

**Questions?** Check the detailed guide: [CI_CD_SETUP.md](./CI_CD_SETUP.md)
