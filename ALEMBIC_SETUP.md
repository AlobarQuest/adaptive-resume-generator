# Alembic Setup Instructions

## Step 1: Initialize Alembic

Run this command in PowerShell from the project root:

```powershell
alembic init alembic
```

This will create:
```
alembic/
├── versions/          # Migration files go here
├── env.py            # Alembic environment config (we'll modify this)
├── script.py.mako    # Template for new migrations
└── README
alembic.ini           # Alembic configuration file (we'll modify this)
```

## Step 2: After Running the Command

Once you've run `alembic init alembic`, let me know and I'll help you:
1. Configure alembic.ini to use our database
2. Modify env.py to import our models
3. Generate the initial migration
4. Test the migration

## What Alembic Does

Alembic tracks database schema changes as "migrations" - Python scripts that can:
- **Upgrade**: Apply changes to move forward (add tables, columns, etc.)
- **Downgrade**: Reverse changes to move backward (undo migrations)

This is crucial for:
- Version control of database schema
- Deploying changes to production
- Rolling back if something goes wrong
- Collaborating with other developers

## Expected Output

When you run `alembic init alembic`, you should see:
```
Creating directory C:\Users\devon\Projects\adaptive-resume-generator\alembic...done
Creating directory C:\Users\devon\Projects\adaptive-resume-generator\alembic\versions...done
Generating C:\Users\devon\Projects\adaptive-resume-generator\alembic\script.py.mako...done
Generating C:\Users\devon\Projects\adaptive-resume-generator\alembic\env.py...done
Generating C:\Users\devon\Projects\adaptive-resume-generator\alembic\README...done
Generating C:\Users\devon\Projects\adaptive-resume-generator\alembic.ini...done
Please edit configuration/connection/logging settings in 'alembic.ini' before proceeding.
```

Run the command now and let me know when it's done!
