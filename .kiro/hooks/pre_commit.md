# Pre-commit Hook Guidance

Before committing any changes to this repository, verify:

1. **No API keys in source:** `grep -r "nvapi-\|sk-or-\|sk-" --include="*.py" --include="*.yaml" .`
2. **Tests pass:** `python -m pytest tests/ -v`
3. **`.env` is gitignored:** check `.gitignore` contains `.env`
4. **Both apps start:** `python -m streamlit run apps/edutrack_ai/app.py --server.headless true`

## Automated check (optional)

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/sh
python -m pytest tests/ -q
if [ $? -ne 0 ]; then
  echo "Tests failed. Commit aborted."
  exit 1
fi
```
