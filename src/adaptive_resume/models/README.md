# Models Package

This directory contains all SQLAlchemy ORM models for the Adaptive Resume Generator.

## Structure

```
models/
├── __init__.py              # Package exports
├── base.py                  # Database configuration and session management
├── profile.py               # User profile model
├── job.py                   # Work history model
├── bullet_point.py          # Achievement/responsibility model
├── tag.py                   # Tag and BulletTag models
├── skill.py                 # Skills model
├── education.py             # Education model
├── certification.py         # Certification model
├── job_application.py       # Job application tracking model
├── generated_resume.py      # Generated resume and cover letter models
└── templates.py             # Resume template and cover letter section models
```

## Models Overview

### Core Models
- **Profile**: User's core professional information (contact, summary)
- **Job**: Employment history entries
- **BulletPoint**: Individual achievements/responsibilities for each job
- **Tag**: Categories for organizing bullet points
- **BulletTag**: Many-to-many relationship between bullets and tags
- **Skill**: Technical and soft skills with proficiency levels
- **Education**: Academic credentials
- **Certification**: Professional certifications and licenses

### Application Tracking
- **JobApplication**: Track job applications with status
- **GeneratedResume**: History of generated resumes
- **GeneratedCoverLetter**: History of generated cover letters

### Templates
- **ResumeTemplate**: PDF layout configurations
- **CoverLetterSection**: Reusable cover letter paragraphs

## Usage

### Initialize Database

```python
from adaptive_resume.models import init_db, seed_tags, create_default_template, get_session

# Create all tables
init_db()

# Seed predefined tags
session = get_session()
seed_tags(session)

# Create default template
create_default_template(session)

session.close()
```

### Create a Profile

```python
from adaptive_resume.models import Profile, get_session

session = get_session()

profile = Profile(
    first_name="John",
    last_name="Doe",
    email="john.doe@example.com",
    professional_summary="Experienced software engineer..."
)

session.add(profile)
session.commit()
session.close()
```

### Create a Job with Bullet Points

```python
from datetime import date
from adaptive_resume.models import Job, BulletPoint, Tag, BulletTag, get_session

session = get_session()

# Create job
job = Job(
    profile_id=1,
    company_name="TechCorp",
    job_title="Software Engineer",
    start_date=date(2020, 1, 1),
    end_date=date(2023, 12, 31),
    is_current=False
)
session.add(job)
session.commit()

# Create bullet point
bullet = BulletPoint(
    job_id=job.id,
    content="Developed microservices architecture...",
    metrics="Reduced response time by 50%",
    display_order=1
)
session.add(bullet)
session.commit()

# Add tags
technical_tag = session.query(Tag).filter_by(name='programming').first()
bullet_tag = BulletTag(bullet_point_id=bullet.id, tag_id=technical_tag.id)
session.add(bullet_tag)
session.commit()

session.close()
```

### Query with Relationships

```python
from adaptive_resume.models import Profile, get_session

session = get_session()

# Get profile with all jobs and their bullet points
profile = session.query(Profile).filter_by(id=1).first()

for job in profile.jobs:
    print(f"{job.job_title} at {job.company_name}")
    for bullet in job.bullet_points:
        print(f"  - {bullet.content}")
        print(f"    Tags: {', '.join(bullet.tag_names)}")

session.close()
```

### Find Bullets by Tag

```python
from adaptive_resume.models import BulletPoint, Tag, BulletTag, get_session
from sqlalchemy import and_

session = get_session()

# Find all bullet points tagged with 'leadership'
bullets = session.query(BulletPoint).join(BulletTag).join(Tag).filter(
    Tag.name == 'leadership'
).all()

for bullet in bullets:
    print(bullet.content)

session.close()
```

## Testing

Run the test script to verify all models are working:

```bash
python test_models.py
```

This will:
1. Create an in-memory database
2. Create all tables
3. Seed tags
4. Create sample data
5. Test relationships
6. Verify queries

## Database Location

By default, the database is created at:
- **Windows**: `%USERPROFILE%\.adaptive_resume\resume_data.db`
- **Mac/Linux**: `~/.adaptive_resume/resume_data.db`

Override with environment variable:
```bash
export ADAPTIVE_RESUME_DB_PATH="/path/to/custom/database.db"
```

## Model Methods

All models include:
- `to_dict()`: Convert to dictionary for serialization
- `__repr__()`: String representation for debugging

Additional properties:
- `Profile.full_name`: First + last name
- `Job.date_range`: Formatted date string
- `Job.duration_months`: Calculate months employed
- `BulletPoint.full_text`: Content + metrics + impact
- `BulletPoint.tag_names`: List of tag names
- `Skill.experience_display`: Formatted experience string
- `Education.gpa_display`: Formatted GPA
- `Certification.is_expired`: Check expiration
- `JobApplication.is_active`: Check if still active

## Constraints

### Check Constraints
- Jobs: `end_date >= start_date` (if both provided)
- Jobs: If `is_current`, then `end_date` must be NULL
- Education: `gpa` between 0.00 and 4.00
- Certifications: `expiration_date >= issue_date`
- JobApplications: `application_date` not in future

### Foreign Keys
All foreign keys use appropriate CASCADE or RESTRICT behaviors:
- Profile deleted → All related data CASCADE deleted
- Tag deleted → RESTRICT if used in bullet_tags
- Template deleted → RESTRICT if used in generated_resumes

### Unique Constraints
- `profiles.email` - UNIQUE
- `tags.name` - UNIQUE
- `resume_templates.name` - UNIQUE
- `(bullet_tags.bullet_point_id, bullet_tags.tag_id)` - UNIQUE

## Schema Version

**Version**: 1.0.0  
**SQLAlchemy**: 2.x  
**SQLite**: 3.x  
**Target PostgreSQL**: 12+ (for future web migration)

See [DATABASE_SCHEMA.md](../../docs/DATABASE_SCHEMA.md) for complete schema documentation.
