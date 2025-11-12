| Field | Value |
| --- | --- |
| Title | Data Model |
| Audience | Data engineers, backend developers |
| Status | Stable |
| Last Updated | 2024-06-15 |

## Summary
This document captures the relational schema backing the Adaptive Resume Generator. It explains the entities that compose a profile, how matching metadata is stored, and the tables that track job applications so developers can extend the persistence layer without violating constraints.

## Key Takeaways
- Profiles own jobs, education, certifications, and skills; bullet points link to tags through a join table for flexible categorization.
- Job applications store submission history and link to generated resumes and cover letters so outcomes remain auditable.
- Alembic manages migrations across SQLite today and PostgreSQL tomorrow—avoid manual DDL so schema history stays consistent.

## Details
### Technology Stack
- **Database Engine:** SQLite 3 for the desktop MVP with a migration path to PostgreSQL 12+.
- **ORM:** SQLAlchemy 2.x models housed in `src/adaptive_resume/models/`.
- **Migrations:** Alembic revision scripts in the `alembic/versions/` directory manage schema evolution.

### Core Profile Entities
| Table | Purpose | Key Columns |
| --- | --- | --- |
| `profiles` | Canonical record for an individual | `first_name`, `last_name`, `email`, `phone`, `city`, `state`, `linkedin_url`, `professional_summary`, timestamps |
| `jobs` | Employment history tied to a profile | `profile_id` (FK), `company_name`, `job_title`, `location`, `start_date`, `end_date`, `is_current`, `display_order` |
| `bullet_points` | Quantified accomplishments per job | `job_id` (FK), `content`, `metrics`, `impact`, `display_order`, `is_highlighted` |
| `skills` | Structured list of capabilities | `profile_id` (FK), `skill_name`, `category`, `proficiency_level`, `years_experience`, `display_order` |
| `education` | Academic history entries | `profile_id` (FK), `institution`, `degree`, `field_of_study`, `start_date`, `end_date`, `gpa`, `honors`, `display_order` |
| `certifications` | Professional credentials | `profile_id` (FK), `name`, `issuing_organization`, `issue_date`, `expiration_date`, `credential_id`, `credential_url`, `display_order` |

### Matching Taxonomy
| Table | Purpose | Key Columns |
| --- | --- | --- |
| `tags` | Canonical vocabulary used for matching | `name`, `category`, timestamps |
| `bullet_tags` | Many-to-many bridge between bullet points and tags | `bullet_point_id` (FK), `tag_id` (FK), timestamps |
| `job_targets` *(planned)* | Future enhancement to store target roles or industries for proactive suggestions | `profile_id` (FK), `title`, `description`, `priority` |

### Application Tracking
| Table | Purpose | Key Columns |
| --- | --- | --- |
| `job_applications` | Tracks submissions per profile | `profile_id` (FK), `company_name`, `position_title`, `application_date`, `status`, `job_url`, `follow_up_date`, `notes` |
| `generated_resumes` | Stores rendered resume metadata per application | `application_id` (FK), `file_path`, `template_name`, `created_at` |
| `cover_letters` | Optional tailored letters paired with applications | `application_id` (FK), `file_path`, `tone`, `created_at` |

### Constraints and Indexing
- Foreign keys enforce ownership; cascading deletes remove dependent rows such as `jobs` when a profile is purged.
- Display ordering fields (`display_order`) keep UI rendering stable without additional joins.
- Unique indexes on `tags.name` and `skills (profile_id, skill_name)` prevent duplicate taxonomy entries.
- Timestamp columns (`created_at`, `updated_at`) support audit trails and sync jobs once APIs ship.

### Migration Strategy
- Use Alembic autogeneration with curated revision scripts—manual SQL should only appear when cross-database compatibility demands it.
- Seed data (e.g., default tags) lives in application code via helper functions like `seed_tags(session)` to remain idempotent during tests.
- When targeting PostgreSQL, audit data types (e.g., booleans, timestamps) to ensure compatibility, then configure `alembic.ini` with the new DSN.

## Next Steps
- Review the [Intelligence Pipeline](intelligence_pipeline.md) for how tags and bullet scores feed matching algorithms.
- Coordinate schema updates with the [Delivery Plan](../development/delivery_plan.md) to track required migrations.
