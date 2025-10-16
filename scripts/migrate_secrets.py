#!/usr/bin/env python3
"""
Migration script to move secrets from .env files to MongoDB.

This script reads environment variables from .env files and stores them
securely in the MongoDB secrets collection.
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from secrets_manager import SecretsManager


class SecretsMigrator:
    def __init__(self, secrets_manager: SecretsManager):
        self.secrets_manager = secrets_manager
        
    def read_env_file(self, env_file_path: str) -> dict:
        """Read environment variables from a .env file."""
        env_vars = {}
        
        if not os.path.exists(env_file_path):
            print(f"✗ Environment file not found: {env_file_path}")
            return env_vars
        
        try:
            with open(env_file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        env_vars[key] = value
                    else:
                        print(f"⚠ Skipping invalid line {line_num}: {line}")
            
            print(f"✓ Read {len(env_vars)} variables from {env_file_path}")
            return env_vars
            
        except Exception as e:
            print(f"✗ Error reading {env_file_path}: {e}")
            return {}
    
    async def migrate_secrets(self, env_vars: dict, environment: str, 
                            skip_existing: bool = True, dry_run: bool = False) -> dict:
        """Migrate environment variables to MongoDB secrets."""
        results = {
            "migrated": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }
        
        print(f"\n{'DRY RUN: ' if dry_run else ''}Migrating {len(env_vars)} secrets to environment '{environment}'...")
        
        for key, value in env_vars.items():
            try:
                # Check if secret already exists
                if skip_existing:
                    existing_value = await self.secrets_manager.get_secret(key, environment)
                    if existing_value is not None:
                        print(f"⚠ Skipping existing secret: {key}")
                        results["skipped"] += 1
                        continue
                
                # Migrate the secret
                if not dry_run:
                    success = await self.secrets_manager.set_secret(key, value, environment)
                    if success:
                        results["migrated"] += 1
                        print(f"✓ Migrated: {key}")
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Failed to migrate {key}")
                else:
                    print(f"✓ Would migrate: {key}")
                    results["migrated"] += 1
                    
            except Exception as e:
                results["failed"] += 1
                error_msg = f"Error migrating {key}: {e}"
                results["errors"].append(error_msg)
                print(f"✗ {error_msg}")
        
        return results
    
    def print_migration_summary(self, results: dict, dry_run: bool = False):
        """Print migration summary."""
        print(f"\n{'DRY RUN ' if dry_run else ''}Migration Summary:")
        print(f"  ✓ {'Would migrate' if dry_run else 'Migrated'}: {results['migrated']}")
        print(f"  ⚠ Skipped: {results['skipped']}")
        print(f"  ✗ Failed: {results['failed']}")
        
        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  - {error}")


async def main():
    parser = argparse.ArgumentParser(description="Migrate secrets from .env files to MongoDB")
    parser.add_argument("--env-file", "-f", default=".env",
                       help="Path to .env file (default: .env)")
    parser.add_argument("--environment", "-e", default="development",
                       help="Target environment (default: development)")
    parser.add_argument("--overwrite", action="store_true",
                       help="Overwrite existing secrets (default: skip existing)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be migrated without making changes")
    parser.add_argument("--list-vars", action="store_true",
                       help="List variables in .env file without migrating")
    
    args = parser.parse_args()
    
    # Initialize secrets manager
    secrets_manager = SecretsManager()
    migrator = SecretsMigrator(secrets_manager)
    
    # Read environment variables from file
    env_vars = migrator.read_env_file(args.env_file)
    
    if not env_vars:
        print("✗ No environment variables found to migrate")
        sys.exit(1)
    
    # If just listing variables, print them and exit
    if args.list_vars:
        print(f"\nEnvironment variables in {args.env_file}:")
        for key, value in env_vars.items():
            # Mask sensitive values for display
            display_value = value
            if len(value) > 20:
                display_value = value[:10] + "..." + value[-5:]
            print(f"  {key}={display_value}")
        sys.exit(0)
    
    try:
        # Connect to MongoDB
        await secrets_manager.connect()
        
        # Perform migration
        results = await migrator.migrate_secrets(
            env_vars=env_vars,
            environment=args.environment,
            skip_existing=not args.overwrite,
            dry_run=args.dry_run
        )
        
        # Print summary
        migrator.print_migration_summary(results, args.dry_run)
        
        # Exit with appropriate code
        if results["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
        
    finally:
        await secrets_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())