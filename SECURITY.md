# Security Configuration Guide

## Environment Variables

This application uses environment variables to securely manage sensitive configuration data. **Never commit actual secrets to version control.**

### Required Environment Variables

1. **MONGODB_URI** - MongoDB connection string with credentials
2. **JWT_SECRET** - Secret key for JWT token signing
3. **JWT_ALGORITHM** - JWT algorithm (default: HS256)
4. **JWT_EXPIRES_IN** - JWT token expiration time in seconds
5. **CORS_ORIGINS** - Allowed CORS origins (comma-separated)

### Setup Instructions

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your actual values:
   - Replace `MONGODB_URI` with your actual MongoDB connection string
   - Generate a secure `JWT_SECRET` (recommended: 64+ random characters)
   - Configure `CORS_ORIGINS` for your deployment environment

### Security Best Practices

- **Never commit `.env` files** - They are included in `.gitignore`
- **Use strong, unique secrets** - Generate random strings for JWT_SECRET
- **Rotate secrets regularly** - Especially in production environments
- **Use environment-specific configurations** - Different secrets for dev/staging/prod
- **Limit CORS origins** - Only allow necessary frontend domains

### Production Deployment

For production deployments, set environment variables through your hosting platform's configuration system rather than using `.env` files:

- **Heroku**: Use `heroku config:set`
- **Vercel**: Use environment variables in dashboard
- **AWS**: Use Systems Manager Parameter Store or Secrets Manager
- **Docker**: Use secrets management or environment variables

### Checking for Exposed Secrets

Before committing code, always verify:
1. No hardcoded secrets in source code
2. `.env` file is in `.gitignore`
3. No secrets in commit history

### Emergency Response

If secrets are accidentally exposed:
1. **Immediately rotate all exposed credentials**
2. **Update environment variables** in all environments
3. **Review commit history** for any exposed secrets
4. **Consider revoking and regenerating** database access credentials

## Contact

For security concerns, please contact the development team immediately.