# Security Best Practices

## Environment Variables & Credentials

### ✅ DO:
- **Always use `.env` files for local development**
  - Copy `.env.example` to `.env` and fill in your credentials
  - Never commit `.env` to version control

- **Use environment variables for ALL sensitive data:**
  - Database URLs and credentials
  - API keys (Anthropic, GitHub, Netlify, Neon, etc.)
  - Access tokens (WhatsApp, OAuth tokens)
  - Webhook secrets
  - Private keys

- **Keep `.env.example` updated:**
  - Document all required environment variables
  - Use placeholder values only (e.g., `your_api_key_here`)
  - Never put real credentials in `.env.example`

- **Verify `.gitignore` includes:**
  ```gitignore
  .env*
  !.env.example
  *.backup
  *.pem
  ```

### ❌ DON'T:
- **Never hardcode credentials in code**
  - Use `os.getenv()` or environment variable loaders
  - Never put database URLs in code

- **Never commit sensitive files:**
  - `.env` files
  - Private keys (`.pem`, `.key` files)
  - Backup files containing credentials
  - Configuration files with secrets

- **Never log sensitive data:**
  - Mask passwords and tokens in logs
  - Sanitize database connection strings before logging
  - Be careful with error messages that might expose credentials

## Current Credentials in This Project

All credentials are stored in `.env` (gitignored). Required environment variables:

1. **Anthropic API** - `ANTHROPIC_API_KEY`
2. **Redis** - `REDIS_URL`
3. **PostgreSQL/Neon** - `DATABASE_URL`, `NEON_API_KEY`
4. **WhatsApp** - `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PERMANENT_TOKEN`, etc.
5. **GitHub** - `GITHUB_PERSONAL_ACCESS_TOKEN`, `GITHUB_PRIVATE_KEY_PATH`
6. **Netlify** - `NETLIFY_PERSONAL_ACCESS_TOKEN`
7. **Logfire** - `LOGFIRE_TOKEN`, `LOGFIRE_READ_TOKEN`

See `.env.example` for the complete list.

## Backend Agent Security

The Backend Agent automatically generates secure backends that:

1. ✅ Always create `.env.example` files (no real credentials)
2. ✅ Always create `.gitignore` with `.env` excluded
3. ✅ Load all credentials from `os.getenv()` or equivalent
4. ✅ Use placeholders in documentation (e.g., `postgresql://[USER]:[PASS]@[HOST]/[DB]`)
5. ✅ Never expose database URLs in prompts or generated code

## Git Commit Safety

Before committing:
```bash
# Check what you're committing
git status

# Review changes for sensitive data
git diff

# Verify .env is not staged
git ls-files | grep .env
# (should only show .env.example, not .env)
```

If you accidentally commit credentials:
1. **Immediately rotate the exposed credentials**
2. Remove from git history: `git filter-branch` or BFG Repo-Cleaner
3. Force push (only if private repo and coordinated with team)

## Production Deployment

For production (Render, Netlify, Vercel, etc.):
- Set environment variables in the hosting platform's dashboard
- Never use `.env` files in production
- Use secret management services for highly sensitive data
- Enable automatic secret rotation where possible

## GitGuardian & Secret Scanning

This repository should have:
- GitGuardian monitoring enabled
- GitHub secret scanning enabled
- Pre-commit hooks to check for secrets (optional)

If GitGuardian alerts:
1. **Rotate the exposed credential immediately**
2. Verify the secret is removed from git history
3. Update the credential everywhere it's used
4. Review how the exposure happened and prevent recurrence
