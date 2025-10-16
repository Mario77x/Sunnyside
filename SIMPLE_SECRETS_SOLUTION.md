# Simple Secrets Management Solution using MongoDB

This document outlines a simplified approach to secrets management using the existing MongoDB database as a lightweight alternative to Doppler.

## 1. Overview

The core idea is to store secrets in a dedicated MongoDB collection instead of `.env` files. A simple utility script will manage these secrets, and the application will load them from MongoDB at startup. This approach solves the problem of secrets being lost or overwritten in `.env` files and provides a centralized store for configuration variables.

## 2. MongoDB Schema

A new collection named `secrets` will be created in the MongoDB database. Each document in this collection will represent a single secret and will have the following structure:

```json
{
  "_id": "<ObjectId>",
  "key": "<string>",
  "value": "<string>",
  "environment": "<string>",
  "created_at": "<ISODate>",
  "updated_at": "<ISODate>"
}
```

-   `key`: The name of the secret (e.g., `DATABASE_URL`).
-   `value`: The encrypted secret value.
-   `environment`: The environment the secret belongs to (e.g., `development`, `production`).
-   `created_at`: Timestamp of when the secret was created.
-   `updated_at`: Timestamp of when the secret was last updated.

## 3. Secrets Management Utility

A Python script named `secrets_manager.py` will be created in the `scripts/` directory to handle CRUD operations for secrets. This script will provide a command-line interface for managing secrets.

**Usage:**

```bash
# Add or update a secret
python scripts/secrets_manager.py set <KEY> <VALUE> --environment <ENV>

# Get a secret
python scripts/secrets_manager.py get <KEY> --environment <ENV>

# Delete a secret
python scripts/secrets_manager.py delete <KEY> --environment <ENV>
```

The script will handle the encryption and decryption of secret values automatically.

## 4. Application Integration

The application will be modified to load secrets from MongoDB instead of `.env` files. This will be done by creating a new utility function that fetches all secrets for the current environment from the `secrets` collection and loads them into the application's environment variables at startup.

The `backend/utils/environment.py` file will be modified to include a function like `load_secrets_from_db()`. This function will be called in `backend/main.py` before the application starts.

## 5. Migration from .env

A migration script will be provided to move existing secrets from `.env` files to the MongoDB `secrets` collection. This script will read the `.env` file, encrypt the values, and store them in MongoDB.

**Usage:**

```bash
python scripts/migrate_secrets.py --env-file .env --environment development
```

This script will ensure a smooth transition from the old `.env` based approach to the new MongoDB-based secrets management solution.

## 6. Encryption

A simple encryption mechanism will be used to protect sensitive values. The `cryptography` library, which is a common dependency in many Python projects, will be used for this purpose. A secret key for encryption will be stored in a separate, non-versioned configuration file or environment variable that is manually managed.