# PetMate Database Migration Scripts

This directory contains several scripts to help fix database migration issues in the PetMate application.

## Automated Fix Scripts

These scripts will automatically detect and fix most common migration issues:

- **auto_fix_migrations.ps1** (Windows) - Automatically fixes migration issues
- **auto_fix_migrations.sh** (Unix/Linux) - Automatically fixes migration issues

The automated fix scripts will:
1. Check if containers are running
2. Stamp the current migration head
3. Run database migrations
4. Detect and fix multiple heads/duplicates
5. Verify database tables

**Usage:**
```
# Windows
.\auto_fix_migrations.ps1

# Unix/Linux
./auto_fix_migrations.sh
```

## Hard Reset Scripts (Last Resort)

These scripts completely reset the database and migrations. **Warning: This will delete all data!**

- **hard_reset_migrations.ps1** (Windows) - Completely resets the database
- **hard_reset_migrations.sh** (Unix/Linux) - Completely resets the database

The hard reset scripts will:
1. Backup existing migrations
2. Drop all database tables
3. Delete all migrations
4. Create a fresh migration
5. Apply the migration
6. Verify database tables
7. Create an admin user (optional)

**Usage:**
```
# Windows
.\hard_reset_migrations.ps1

# Unix/Linux
./hard_reset_migrations.sh
```

## Manual Fix Scripts

These scripts provide a more guided approach to fixing issues:

- **fix_migrations.ps1** / **fix_migrations.sh** - Fix multiple migration heads
- **fix_duplicate_migrations.ps1** / **fix_duplicate_migrations.sh** - Fix duplicate revision warnings
- **manual_migrations.ps1** / **manual_migrations.sh** - Show manual migration commands

## Container Names

All scripts have been updated to use these specific container names:
- Web container: `petmate`
- Database container: `petmate_db`

## Troubleshooting Steps

1. First, try the automated fix script
2. If that doesn't work, try the manual scripts
3. As a last resort, use the hard reset script

## Common Errors

- **Multiple head revisions are present** - Use fix_migrations.ps1
- **Revision is present more than once** - Use fix_duplicate_migrations.ps1
- **Table 'users' does not exist** - First run migrations, then consider reset 