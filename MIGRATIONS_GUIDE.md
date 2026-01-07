# Database Migrations Guide - TicketProZW

This project uses **Alembic** for database schema migrations, providing version control for the database schema.

---

## Quick Reference

```bash
# Create a new migration (autogenerate from model changes)
alembic revision --autogenerate -m "description of changes"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Check current database version
alembic current
```

---

## Setup (Already Complete)

Alembic has been configured and initialized with:

- **Configuration file**: `alembic.ini`
- **Migration scripts**: `alembic/versions/`
- **Environment setup**: `alembic/env.py`
- **Initial migration**: `b8e5e43b379d_initial_schema.py`

The database has been stamped at the initial schema version.

---

## Creating New Migrations

### Step 1: Modify Your Models

Make changes to your SQLAlchemy models in the `models/` directory.

**Example**: Adding a new column to Users
```python
# models/users.py
class Users(Base):
    # ... existing columns ...
    bio = Column(String(500))  # New column
```

### Step 2: Generate Migration

```bash
alembic revision --autogenerate -m "add bio column to users"
```

This creates a new migration file in `alembic/versions/` with:
- Automatically detected schema changes
- Both `upgrade()` and `downgrade()` functions

### Step 3: Review the Migration

**Important**: Always review auto-generated migrations before applying them.

```bash
# Check the latest migration file
ls -lt alembic/versions/ | head -2
```

Open the file and verify:
- ✅ Changes are correct
- ✅ Data migrations are handled (if needed)
- ✅ Indexes are appropriate
- ✅ Foreign keys are preserved

### Step 4: Apply the Migration

```bash
alembic upgrade head
```

This applies all pending migrations to the database.

---

## Common Operations

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations up to a specific revision
alembic upgrade b8e5e43b379d

# Apply next migration only
alembic upgrade +1
```

### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade b8e5e43b379d

# Rollback all migrations
alembic downgrade base
```

### View Migration Status

```bash
# Current database version
alembic current

# Full migration history
alembic history

# Show SQL that would be executed (dry run)
alembic upgrade head --sql
```

---

## Migration Best Practices

### 1. Always Review Auto-Generated Migrations

Alembic's autogenerate is helpful but not perfect. Always review:

```bash
# After creating migration, review it
cat alembic/versions/<migration_file>.py
```

**Common issues to check:**
- Renamed columns (detected as drop + add)
- Type changes requiring data migration
- Constraint changes
- Index changes

### 2. Test Migrations Both Ways

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Upgrade again
alembic upgrade head
```

### 3. Never Edit Applied Migrations

Once a migration has been applied to production:
- ❌ Don't edit the migration file
- ✅ Create a new migration to fix issues

### 4. Handle Data Migrations

For complex changes requiring data transformation:

```python
def upgrade() -> None:
    # Schema change
    op.add_column('users', sa.Column('full_name', sa.String(200)))

    # Data migration
    connection = op.get_bind()
    connection.execute(
        "UPDATE users SET full_name = firstname || ' ' || surname"
    )

    # Cleanup if needed
    # op.drop_column('users', 'firstname')
    # op.drop_column('users', 'surname')
```

### 5. Backup Before Major Migrations

```bash
# Backup database before migration
pg_dump -U postgres ticketprozw > backup_before_migration.sql

# Apply migration
alembic upgrade head

# If needed, restore
# psql -U postgres -d ticketprozw < backup_before_migration.sql
```

---

## Troubleshooting

### Migration Conflicts

If multiple developers create migrations simultaneously:

```bash
# Merge migrations manually
alembic merge <rev1> <rev2> -m "merge migrations"
```

### Database Out of Sync

If the database schema doesn't match Alembic's version:

```bash
# Option 1: Stamp database at correct version (dangerous)
alembic stamp head

# Option 2: Start fresh (development only)
alembic downgrade base
alembic upgrade head
```

### Auto-generate Detects Too Many Changes

If autogenerate detects unexpected changes:

1. Check that all models are imported in `alembic/env.py`
2. Verify database connection is correct
3. Review model definitions for recent changes

---

## Integration with Deployment

### Development

```bash
# Create and apply migrations locally
alembic revision --autogenerate -m "changes"
alembic upgrade head

# Commit migration file to git
git add alembic/versions/<new_migration>.py
git commit -m "Add migration: changes"
```

### Staging/Production

```bash
# After deploying new code, run migrations
alembic upgrade head

# Or use a deployment script:
./deploy.sh  # Should include: alembic upgrade head
```

### Docker/Container Deployment

In your startup script or Dockerfile CMD:

```bash
#!/bin/bash
# Run migrations before starting app
alembic upgrade head

# Start application
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Schema Change Examples

### Adding a Column

```python
# models/users.py
class Users(Base):
    avatar_url = Column(String(500))  # New column
```

```bash
alembic revision --autogenerate -m "add avatar_url to users"
alembic upgrade head
```

### Removing a Column

```python
# models/events.py
# Remove: image = Column(String(500))
```

```bash
alembic revision --autogenerate -m "remove image column from events"
alembic upgrade head
```

### Adding an Index

```python
# models/events.py
class Events(Base):
    status = Column(String(20), index=True)  # Add index
```

```bash
alembic revision --autogenerate -m "add index on events.status"
alembic upgrade head
```

### Creating a New Table

```python
# models/notifications.py
class Notifications(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    message = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Don't forget to import in `alembic/env.py`:

```python
from models.notifications import Notifications
```

```bash
alembic revision --autogenerate -m "create notifications table"
alembic upgrade head
```

---

## Current Migration State

- **Current Version**: `b8e5e43b379d` (initial schema)
- **Applied**: 2026-01-08
- **Status**: Database is up to date

To verify:

```bash
alembic current
# Should show: b8e5e43b379d (head)
```

---

## Next Steps

Now that Alembic is set up:

1. ✅ Database migrations are version-controlled
2. ✅ Schema changes are tracked
3. ✅ Rollbacks are possible
4. 📝 Create new migrations for upcoming Phase 2 changes (relationships, audit fields, etc.)

---

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic Autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
