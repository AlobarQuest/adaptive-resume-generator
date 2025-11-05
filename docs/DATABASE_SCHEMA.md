# Database Schema

**Project:** Adaptive Resume Generator  
**Version:** 0.1.0-dev  
**Last Updated:** November 4, 2025  
**Author:** AlobarQuest

## Purpose

This document provides the complete database schema for the Adaptive Resume Generator, including:
- Entity-Relationship Diagrams (ERD)
- Detailed table specifications
- Column definitions and constraints
- Relationships and foreign keys
- Indexes for performance
- Migration strategy

For architectural context, see [ARCHITECTURE.md](ARCHITECTURE.md).  
For implementation roadmap, see [PROJECT_PLAN.md](PROJECT_PLAN.md).

## Database Overview

### Technology
- **Initial:** SQLite 3.x (file-based, zero configuration)
- **Future:** PostgreSQL 12+ (for web migration)
- **ORM:** SQLAlchemy 2.x (database agnostic)
- **Migrations:** Alembic (version control)

### Design Principles

1. **Normalization:** 3rd Normal Form (3NF) to reduce redundancy
2. **Referential Integrity:** Foreign keys enforce relationships
3. **Cascading Deletes:** Strategic CASCADE/RESTRICT rules
4. **Soft Deletes:** For audit trail (where needed)
5. **Timestamps:** Created/updated tracking on all entities
6. **Flexibility:** Support future web migration

## Entity-Relationship Diagram

### Complete ERD

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ADAPTIVE RESUME GENERATOR                        │
│                         DATABASE SCHEMA (ERD)                           │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────┐
│       profiles         │
│────────────────────────│
│ PK id                  │
│    first_name          │
│    last_name           │
│    email               │
│    phone               │
│    city                │
│    state               │
│    linkedin_url        │
│    portfolio_url       │
│    professional_summary│
│    created_at          │
│    updated_at          │
└────────┬───────────────┘
         │
         │ 1:N (has many jobs)
         │
         ▼
┌────────────────────────┐
│        jobs            │
│────────────────────────│
│ PK id                  │
│ FK profile_id          │◄────────────┐
│    company_name        │             │
│    job_title           │             │
│    location            │             │
│    start_date          │             │
│    end_date            │             │
│    is_current          │             │
│    description         │             │
│    display_order       │             │
│    created_at          │             │
│    updated_at          │             │
└────────┬───────────────┘             │
         │                             │
         │ 1:N (has many bullets)      │
         │                             │
         ▼                             │
┌────────────────────────┐             │
│    bullet_points       │             │
│────────────────────────│             │
│ PK id                  │             │
│ FK job_id              │             │
│    content             │             │
│    metrics             │             │
│    impact              │             │
│    display_order       │             │
│    is_highlighted      │             │
│    created_at          │             │
│    updated_at          │             │
└────────┬───────────────┘             │
         │                             │
         │ N:M (through bullet_tags)   │
         │                             │
         ▼                             │
┌────────────────────────┐             │
│     bullet_tags        │             │
│────────────────────────│             │
│ PK id                  │             │
│ FK bullet_point_id     │             │
│ FK tag_id              │             │
│    created_at          │             │
└────────┬───────────────┘             │
         │                             │
         ▼                             │
┌────────────────────────┐             │
│        tags            │             │
│────────────────────────│             │
│ PK id                  │             │
│    name                │             │
│    category            │             │
│    created_at          │             │
└────────────────────────┘             │
                                       │
                                       │
┌────────────────────────┐             │
│       skills           │             │
│────────────────────────│             │
│ PK id                  │             │
│ FK profile_id          │─────────────┤
│    skill_name          │             │
│    category            │             │
│    proficiency_level   │             │
│    years_experience    │             │
│    display_order       │             │
│    created_at          │             │
│    updated_at          │             │
└────────────────────────┘             │
                                       │
┌────────────────────────┐             │
│      education         │             │
│────────────────────────│             │
│ PK id                  │             │
│ FK profile_id          │─────────────┤
│    institution         │             │
│    degree              │             │
│    field_of_study      │             │
│    start_date          │             │
│    end_date            │             │
│    gpa                 │             │
│    honors              │             │
│    relevant_coursework │             │
│    display_order       │             │
│    created_at          │             │
│    updated_at          │             │
└────────────────────────┘             │
                                       │
┌────────────────────────┐             │
│    certifications      │             │
│────────────────────────│             │
│ PK id                  │             │
│ FK profile_id          │─────────────┘
│    name                │
│    issuing_organization│
│    issue_date          │
│    expiration_date     │
│    credential_id       │
│    credential_url      │
│    display_order       │
│    created_at          │
│    updated_at          │
└────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                     APPLICATION TRACKING ENTITIES                        │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────┐
│   job_applications     │
│────────────────────────│
│ PK id                  │
│ FK profile_id          │
│    company_name        │
│    position_title      │
│    job_description     │
│    application_date    │
│    status              │
│    job_url             │
│    contact_person      │
│    contact_email       │
│    notes               │
│    follow_up_date      │
│    created_at          │
│    updated_at          │
└────────┬───────────────┘
         │
         │ 1:N (has many resumes)
         │
         ▼
┌────────────────────────┐
│   generated_resumes    │
│────────────────────────│
│ PK id                  │
│ FK job_application_id  │
│ FK resume_template_id  │
│    file_path           │
│    selected_bullets    │ (JSON)
│    selected_skills     │ (JSON)
│    custom_summary      │
│    generated_at        │
│    created_at          │
└────────┬───────────────┘
         │
         │ N:1 (uses template)
         │
         ▼
┌────────────────────────┐
│   resume_templates     │
│────────────────────────│
│ PK id                  │
│    name                │
│    description         │
│    layout_config       │ (JSON)
│    is_default          │
│    created_at          │
│    updated_at          │
└────────────────────────┘


┌────────────────────────┐
│   job_applications     │ (from above)
└────────┬───────────────┘
         │
         │ 1:N (has many cover letters)
         │
         ▼
┌────────────────────────┐
│generated_cover_letters │
│────────────────────────│
│ PK id                  │
│ FK job_application_id  │
│    file_path           │
│    opening_section_id  │
│    body_sections       │ (JSON array of IDs)
│    closing_section_id  │
│    custom_content      │
│    generated_at        │
│    created_at          │
└────────┬───────────────┘
         │
         │ N:M (uses sections)
         │
         ▼
┌────────────────────────┐
│cover_letter_sections   │
│────────────────────────│
│ PK id                  │
│ FK profile_id          │
│    section_type        │ (opening/body/closing)
│    title               │
│    content             │
│    tags                │ (JSON)
│    is_favorite         │
│    created_at          │
│    updated_at          │
└────────────────────────┘
```

### Relationship Summary

| Parent Entity | Child Entity | Relationship | Cascade Behavior |
|--------------|--------------|--------------|------------------|
| profiles | jobs | 1:N | CASCADE delete |
| profiles | skills | 1:N | CASCADE delete |
| profiles | education | 1:N | CASCADE delete |
| profiles | certifications | 1:N | CASCADE delete |
| profiles | job_applications | 1:N | CASCADE delete |
| profiles | cover_letter_sections | 1:N | CASCADE delete |
| jobs | bullet_points | 1:N | CASCADE delete |
| bullet_points | bullet_tags | 1:N | CASCADE delete |
| tags | bullet_tags | 1:N | RESTRICT delete |
| job_applications | generated_resumes | 1:N | CASCADE delete |
| job_applications | generated_cover_letters | 1:N | CASCADE delete |
| resume_templates | generated_resumes | 1:N | RESTRICT delete |

## Table Specifications

### Core Profile Tables

#### `profiles`

User's core professional information. In v1.0, single profile per database.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| first_name | VARCHAR(100) | NOT NULL | User's first name |
| last_name | VARCHAR(100) | NOT NULL | User's last name |
| email | VARCHAR(255) | NOT NULL, UNIQUE | Primary email address |
| phone | VARCHAR(20) | NULL | Phone number (formatted) |
| city | VARCHAR(100) | NULL | Current city |
| state | VARCHAR(50) | NULL | Current state/province |
| linkedin_url | VARCHAR(255) | NULL | LinkedIn profile URL |
| portfolio_url | VARCHAR(255) | NULL | Portfolio/website URL |
| professional_summary | TEXT | NULL | Career summary/objective |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_profiles_email` on `email` (for login in future web version)

**Validation Rules:**
- Email must be valid format
- Phone can be NULL or valid format
- URLs must be valid format if provided

---

#### `jobs`

Work history entries with company and role details.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| profile_id | INTEGER | NOT NULL, FOREIGN KEY → profiles.id | Owner profile |
| company_name | VARCHAR(200) | NOT NULL | Company/organization name |
| job_title | VARCHAR(200) | NOT NULL | Job title/position |
| location | VARCHAR(200) | NULL | Job location (City, State) |
| start_date | DATE | NOT NULL | Employment start date |
| end_date | DATE | NULL | Employment end date (NULL if current) |
| is_current | BOOLEAN | NOT NULL, DEFAULT FALSE | Currently employed flag |
| description | TEXT | NULL | Overall role description |
| display_order | INTEGER | NOT NULL, DEFAULT 0 | Order for display (for manual sorting) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_jobs_profile_id` on `profile_id`
- `idx_jobs_start_date` on `start_date` (for chronological sorting)

**Foreign Keys:**
- `profile_id` → `profiles.id` ON DELETE CASCADE

**Validation Rules:**
- `start_date` must be before `end_date` (if `end_date` is not NULL)
- If `is_current` is TRUE, `end_date` must be NULL
- `display_order` used for custom ordering

---

#### `bullet_points`

Individual achievements and responsibilities for each job.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| job_id | INTEGER | NOT NULL, FOREIGN KEY → jobs.id | Parent job |
| content | TEXT | NOT NULL | Achievement/responsibility text |
| metrics | VARCHAR(500) | NULL | Quantifiable metrics (e.g., "Increased by 25%") |
| impact | TEXT | NULL | Business impact description |
| display_order | INTEGER | NOT NULL, DEFAULT 0 | Order within job |
| is_highlighted | BOOLEAN | NOT NULL, DEFAULT FALSE | Marked as standout achievement |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_bullet_points_job_id` on `job_id`
- `idx_bullet_points_content` FULLTEXT on `content` (for searching)

**Foreign Keys:**
- `job_id` → `jobs.id` ON DELETE CASCADE

**Validation Rules:**
- `content` minimum length: 10 characters
- `content` maximum length: 1000 characters (for resume formatting)

---

#### `tags`

Categories for organizing and matching bullet points.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Tag name (e.g., "leadership") |
| category | VARCHAR(50) | NULL | Tag category (e.g., "soft-skill", "technical") |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Indexes:**
- `idx_tags_name` on `name` (unique index)
- `idx_tags_category` on `category`

**Predefined Tags (seeded on setup):**
- **Technical:** programming, database, cloud, security, devops
- **Leadership:** team-management, mentoring, project-management
- **Financial:** budgeting, cost-reduction, revenue-growth
- **Customer:** customer-service, client-relations, sales
- **Process:** automation, optimization, efficiency
- **Communication:** presentations, documentation, training
- **Problem-Solving:** troubleshooting, debugging, analysis

---

#### `bullet_tags`

Many-to-many relationship between bullet points and tags.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| bullet_point_id | INTEGER | NOT NULL, FOREIGN KEY → bullet_points.id | Bullet point |
| tag_id | INTEGER | NOT NULL, FOREIGN KEY → tags.id | Tag |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Indexes:**
- `idx_bullet_tags_bullet_point_id` on `bullet_point_id`
- `idx_bullet_tags_tag_id` on `tag_id`
- `idx_bullet_tags_unique` UNIQUE on `(bullet_point_id, tag_id)`

**Foreign Keys:**
- `bullet_point_id` → `bullet_points.id` ON DELETE CASCADE
- `tag_id` → `tags.id` ON DELETE RESTRICT (prevent deleting tags in use)

---

#### `skills`

User's skills with proficiency and experience tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| profile_id | INTEGER | NOT NULL, FOREIGN KEY → profiles.id | Owner profile |
| skill_name | VARCHAR(200) | NOT NULL | Skill name (e.g., "Python", "Leadership") |
| category | VARCHAR(100) | NULL | Skill category (e.g., "Programming", "Management") |
| proficiency_level | VARCHAR(50) | NULL | Proficiency (Beginner/Intermediate/Advanced/Expert) |
| years_experience | DECIMAL(4,1) | NULL | Years of experience with skill |
| display_order | INTEGER | NOT NULL, DEFAULT 0 | Display order |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_skills_profile_id` on `profile_id`
- `idx_skills_category` on `category`

**Foreign Keys:**
- `profile_id` → `profiles.id` ON DELETE CASCADE

**Validation Rules:**
- `proficiency_level` must be one of: Beginner, Intermediate, Advanced, Expert (or NULL)
- `years_experience` must be >= 0

**Skill Categories:**
- Programming Languages
- Frameworks & Libraries
- Databases
- Cloud Platforms
- Tools & Software
- Methodologies
- Soft Skills
- Domain Knowledge

---

#### `education`

Academic history and credentials.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| profile_id | INTEGER | NOT NULL, FOREIGN KEY → profiles.id | Owner profile |
| institution | VARCHAR(255) | NOT NULL | School/university name |
| degree | VARCHAR(200) | NOT NULL | Degree type (e.g., "Bachelor of Science") |
| field_of_study | VARCHAR(200) | NULL | Major/field (e.g., "Computer Science") |
| start_date | DATE | NULL | Start date |
| end_date | DATE | NULL | Graduation date |
| gpa | DECIMAL(3,2) | NULL | GPA (e.g., 3.75) |
| honors | VARCHAR(500) | NULL | Honors/awards (e.g., "Magna Cum Laude") |
| relevant_coursework | TEXT | NULL | List of relevant courses |
| display_order | INTEGER | NOT NULL, DEFAULT 0 | Display order |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_education_profile_id` on `profile_id`
- `idx_education_end_date` on `end_date`

**Foreign Keys:**
- `profile_id` → `profiles.id` ON DELETE CASCADE

**Validation Rules:**
- `start_date` must be before `end_date` (if both provided)
- `gpa` must be between 0.00 and 4.00 (or NULL)

---

#### `certifications`

Professional certifications and licenses.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| profile_id | INTEGER | NOT NULL, FOREIGN KEY → profiles.id | Owner profile |
| name | VARCHAR(255) | NOT NULL | Certification name |
| issuing_organization | VARCHAR(255) | NOT NULL | Issuing body |
| issue_date | DATE | NULL | Date issued |
| expiration_date | DATE | NULL | Expiration date (NULL if no expiration) |
| credential_id | VARCHAR(200) | NULL | Credential/license number |
| credential_url | VARCHAR(255) | NULL | Verification URL |
| display_order | INTEGER | NOT NULL, DEFAULT 0 | Display order |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_certifications_profile_id` on `profile_id`
- `idx_certifications_expiration_date` on `expiration_date` (for expiration alerts)

**Foreign Keys:**
- `profile_id` → `profiles.id` ON DELETE CASCADE

**Validation Rules:**
- `issue_date` must be before `expiration_date` (if both provided)
- `credential_url` must be valid URL format (if provided)

---

### Application Tracking Tables

#### `job_applications`

Track job applications and their status.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| profile_id | INTEGER | NOT NULL, FOREIGN KEY → profiles.id | Owner profile |
| company_name | VARCHAR(200) | NOT NULL | Company applied to |
| position_title | VARCHAR(200) | NOT NULL | Position title |
| job_description | TEXT | NULL | Full job description (for matching) |
| application_date | DATE | NOT NULL | Date applied |
| status | VARCHAR(50) | NOT NULL, DEFAULT 'applied' | Application status |
| job_url | VARCHAR(255) | NULL | Job posting URL |
| contact_person | VARCHAR(200) | NULL | Recruiter/hiring manager name |
| contact_email | VARCHAR(255) | NULL | Contact email |
| notes | TEXT | NULL | Application notes |
| follow_up_date | DATE | NULL | Next follow-up date |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_job_applications_profile_id` on `profile_id`
- `idx_job_applications_status` on `status`
- `idx_job_applications_application_date` on `application_date`

**Foreign Keys:**
- `profile_id` → `profiles.id` ON DELETE CASCADE

**Status Values:**
- `applied` - Application submitted
- `phone_screen` - Phone screening scheduled/completed
- `interview` - Interview scheduled/completed
- `offer` - Offer received
- `accepted` - Offer accepted
- `rejected` - Application rejected
- `withdrawn` - Application withdrawn

**Validation Rules:**
- `status` must be one of the defined status values
- `application_date` cannot be in the future

---

#### `generated_resumes`

History of generated resumes with configuration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| job_application_id | INTEGER | NULL, FOREIGN KEY → job_applications.id | Related application |
| resume_template_id | INTEGER | NOT NULL, FOREIGN KEY → resume_templates.id | Template used |
| file_path | VARCHAR(500) | NOT NULL | Path to PDF file |
| selected_bullets | TEXT | NOT NULL | JSON array of bullet_point IDs |
| selected_skills | TEXT | NULL | JSON array of skill IDs |
| custom_summary | TEXT | NULL | Custom summary for this resume |
| generated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Generation timestamp |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Indexes:**
- `idx_generated_resumes_job_application_id` on `job_application_id`
- `idx_generated_resumes_generated_at` on `generated_at`

**Foreign Keys:**
- `job_application_id` → `job_applications.id` ON DELETE CASCADE
- `resume_template_id` → `resume_templates.id` ON DELETE RESTRICT

**JSON Field Formats:**

```json
// selected_bullets
[1, 5, 12, 18, 23]

// selected_skills
[2, 7, 15, 22]
```

---

#### `resume_templates`

Resume layout configurations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Template name |
| description | TEXT | NULL | Template description |
| layout_config | TEXT | NOT NULL | JSON configuration |
| is_default | BOOLEAN | NOT NULL, DEFAULT FALSE | Default template flag |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_resume_templates_name` on `name` (unique)
- `idx_resume_templates_is_default` on `is_default`

**Validation Rules:**
- Only one template can have `is_default = TRUE`

**Layout Config JSON Format:**

```json
{
  "page_size": "letter",
  "margins": {
    "top": 0.5,
    "bottom": 0.5,
    "left": 0.75,
    "right": 0.75
  },
  "fonts": {
    "header": {"family": "Helvetica-Bold", "size": 16},
    "name": {"family": "Helvetica-Bold", "size": 24},
    "section_header": {"family": "Helvetica-Bold", "size": 12},
    "body": {"family": "Helvetica", "size": 10}
  },
  "colors": {
    "primary": "#000000",
    "secondary": "#333333",
    "accent": "#0066cc"
  },
  "sections_order": [
    "contact",
    "summary",
    "skills",
    "experience",
    "education",
    "certifications"
  ],
  "bullet_style": "bullet",
  "line_spacing": 1.15
}
```

---

#### `cover_letter_sections`

Reusable cover letter sections.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| profile_id | INTEGER | NOT NULL, FOREIGN KEY → profiles.id | Owner profile |
| section_type | VARCHAR(50) | NOT NULL | Section type |
| title | VARCHAR(200) | NULL | Section title/label |
| content | TEXT | NOT NULL | Section content |
| tags | TEXT | NULL | JSON array of tags for matching |
| is_favorite | BOOLEAN | NOT NULL, DEFAULT FALSE | Favorite/frequently used |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_cover_letter_sections_profile_id` on `profile_id`
- `idx_cover_letter_sections_section_type` on `section_type`

**Foreign Keys:**
- `profile_id` → `profiles.id` ON DELETE CASCADE

**Section Types:**
- `opening` - Introduction paragraph
- `body` - Main content paragraphs
- `closing` - Closing paragraph

**Tags JSON Format:**

```json
["technical", "leadership", "startup", "enterprise"]
```

---

#### `generated_cover_letters`

History of generated cover letters.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| job_application_id | INTEGER | NULL, FOREIGN KEY → job_applications.id | Related application |
| file_path | VARCHAR(500) | NOT NULL | Path to PDF file |
| opening_section_id | INTEGER | NULL, FOREIGN KEY → cover_letter_sections.id | Opening section used |
| body_sections | TEXT | NOT NULL | JSON array of section IDs |
| closing_section_id | INTEGER | NULL, FOREIGN KEY → cover_letter_sections.id | Closing section used |
| custom_content | TEXT | NULL | Custom additions/modifications |
| generated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Generation timestamp |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Indexes:**
- `idx_generated_cover_letters_job_application_id` on `job_application_id`
- `idx_generated_cover_letters_generated_at` on `generated_at`

**Foreign Keys:**
- `job_application_id` → `job_applications.id` ON DELETE CASCADE
- `opening_section_id` → `cover_letter_sections.id` ON DELETE RESTRICT
- `closing_section_id` → `cover_letter_sections.id` ON DELETE RESTRICT

**Body Sections JSON Format:**

```json
[5, 12, 18]
```

---

## Indexes Summary

### Primary Indexes (created automatically)
- All `id` columns (PRIMARY KEY)

### Foreign Key Indexes
- `idx_jobs_profile_id`
- `idx_bullet_points_job_id`
- `idx_bullet_tags_bullet_point_id`
- `idx_bullet_tags_tag_id`
- `idx_skills_profile_id`
- `idx_education_profile_id`
- `idx_certifications_profile_id`
- `idx_job_applications_profile_id`
- `idx_generated_resumes_job_application_id`
- `idx_cover_letter_sections_profile_id`
- `idx_generated_cover_letters_job_application_id`

### Performance Indexes
- `idx_profiles_email` - For future login
- `idx_jobs_start_date` - Chronological sorting
- `idx_tags_name` - Tag lookup (UNIQUE)
- `idx_tags_category` - Category filtering
- `idx_bullet_tags_unique` - Prevent duplicate tags
- `idx_skills_category` - Category filtering
- `idx_education_end_date` - Chronological sorting
- `idx_certifications_expiration_date` - Expiration tracking
- `idx_job_applications_status` - Status filtering
- `idx_job_applications_application_date` - Date sorting

### Full-Text Indexes (SQLite FTS5)
- `idx_bullet_points_content` - Search bullet points
- Future: Job descriptions, notes, etc.

## Data Types & Constraints

### SQLite Type Mapping

| Logical Type | SQLite Storage | SQLAlchemy Type | Notes |
|-------------|----------------|-----------------|-------|
| INTEGER | INTEGER | Integer | Auto-increment PKs |
| VARCHAR(n) | TEXT | String(n) | Length validated by app |
| TEXT | TEXT | Text | Unlimited length |
| DATE | TEXT | Date | ISO 8601 format (YYYY-MM-DD) |
| TIMESTAMP | TEXT | DateTime | ISO 8601 format with timezone |
| BOOLEAN | INTEGER | Boolean | 0 = False, 1 = True |
| DECIMAL(p,s) | REAL | Numeric(p,s) | Floating point |

### PostgreSQL Type Mapping (Future)

When migrating to PostgreSQL, SQLAlchemy will map to native types:

| SQLite Type | PostgreSQL Type | Notes |
|------------|-----------------|-------|
| INTEGER | SERIAL/INTEGER | AUTO_INCREMENT → SERIAL |
| TEXT (VARCHAR) | VARCHAR(n) | Length enforced |
| TEXT | TEXT | Native TEXT type |
| TEXT (DATE) | DATE | Native DATE type |
| TEXT (TIMESTAMP) | TIMESTAMP WITH TIME ZONE | Timezone-aware |
| INTEGER (BOOLEAN) | BOOLEAN | Native BOOLEAN type |
| REAL (DECIMAL) | NUMERIC(p,s) | Exact decimal precision |

## Constraints & Rules

### Cascade Rules

**ON DELETE CASCADE:**
- Profile deleted → All jobs, skills, education, certifications, applications, cover letter sections deleted
- Job deleted → All bullet points deleted
- Bullet point deleted → All bullet_tags deleted
- Job application deleted → All generated resumes and cover letters deleted

**ON DELETE RESTRICT:**
- Tag cannot be deleted if used in bullet_tags
- Resume template cannot be deleted if used in generated_resumes
- Cover letter section cannot be deleted if used in generated_cover_letters

### Check Constraints

```sql
-- Jobs: end_date must be after start_date
CHECK (end_date IS NULL OR end_date >= start_date)

-- Jobs: if current, end_date must be NULL
CHECK (NOT is_current OR end_date IS NULL)

-- Education: GPA between 0.00 and 4.00
CHECK (gpa IS NULL OR (gpa >= 0.0 AND gpa <= 4.0))

-- Education: end_date after start_date
CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)

-- Certifications: expiration after issue
CHECK (expiration_date IS NULL OR issue_date IS NULL OR expiration_date >= issue_date)

-- Skills: years_experience non-negative
CHECK (years_experience IS NULL OR years_experience >= 0)

-- Job Applications: application date not in future
CHECK (application_date <= CURRENT_DATE)

-- Resume Templates: only one default
-- (Enforced by trigger or application logic)
```

### Unique Constraints

- `profiles.email` - UNIQUE
- `tags.name` - UNIQUE
- `(bullet_tags.bullet_point_id, bullet_tags.tag_id)` - UNIQUE
- `resume_templates.name` - UNIQUE

## Sample Data

### Example Profile

```sql
INSERT INTO profiles (first_name, last_name, email, phone, city, state, linkedin_url, professional_summary)
VALUES (
  'Devon',
  'Watkins',
  'devon.watkins@example.com',
  '555-123-4567',
  'Sugar Hill',
  'Georgia',
  'https://linkedin.com/in/devonwatkins',
  'Experienced IT professional with 25 years in system architecture, program management, and team leadership. Proven track record in delivering enterprise solutions and driving technical innovation.'
);
```

### Example Job

```sql
INSERT INTO jobs (profile_id, company_name, job_title, location, start_date, end_date, is_current, description, display_order)
VALUES (
  1,
  'TechCorp Solutions',
  'Senior Program Manager',
  'Atlanta, GA',
  '2018-03-01',
  '2023-06-30',
  FALSE,
  'Led cross-functional teams in delivering enterprise software solutions.',
  1
);
```

### Example Bullet Points with Tags

```sql
-- Insert bullet point
INSERT INTO bullet_points (job_id, content, metrics, impact, display_order)
VALUES (
  1,
  'Led migration of legacy infrastructure to AWS cloud platform',
  'Reduced operational costs by 35% and improved system uptime to 99.9%',
  'Enabled company to scale rapidly during 300% growth period',
  1
);

-- Tag it
INSERT INTO bullet_tags (bullet_point_id, tag_id)
VALUES (1, (SELECT id FROM tags WHERE name = 'cloud'));

INSERT INTO bullet_tags (bullet_point_id, tag_id)
VALUES (1, (SELECT id FROM tags WHERE name = 'leadership'));
```

## Migration Strategy

### Initial Setup

1. **Create Database File**
   ```python
   # Database created at: ~/.adaptive_resume/resume_data.db
   ```

2. **Run Migrations**
   ```bash
   alembic upgrade head
   ```

3. **Seed Tags**
   ```python
   # Seed predefined tags
   seed_default_tags()
   ```

4. **Create Default Template**
   ```python
   # Create "Professional" template as default
   create_default_template()
   ```

### Alembic Migration Files

```
alembic/versions/
├── 001_initial_schema.py         # Create all tables
├── 002_add_indexes.py            # Add performance indexes
├── 003_seed_tags.py              # Seed default tags
├── 004_create_default_template.py # Create default resume template
```

### Version Control

```bash
# Create new migration
alembic revision -m "Add new column to jobs table"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### SQLite → PostgreSQL Migration

When ready to migrate to PostgreSQL for web version:

1. **Backup SQLite Database**
   ```bash
   cp ~/.adaptive_resume/resume_data.db ~/.adaptive_resume/backup_YYYYMMDD.db
   ```

2. **Update Connection String**
   ```python
   # From:
   DATABASE_URL = "sqlite:///~/.adaptive_resume/resume_data.db"
   
   # To:
   DATABASE_URL = "postgresql://user:password@localhost:5432/adaptive_resume"
   ```

3. **Run Alembic Migrations**
   ```bash
   alembic upgrade head
   ```

4. **Migrate Data**
   ```python
   # Use SQLAlchemy to read from SQLite and write to PostgreSQL
   migrate_data(sqlite_session, postgres_session)
   ```

5. **Verify Data Integrity**
   ```python
   verify_migration(sqlite_session, postgres_session)
   ```

## Database Maintenance

### Backup Strategy

**Automated Backups:**
- Daily backup before application start
- Keep last 7 daily backups
- Keep last 4 weekly backups
- Manual backup before major operations

**Backup Location:**
```
~/.adaptive_resume/backups/
├── resume_data_2025-11-04.db
├── resume_data_2025-11-03.db
└── ...
```

### Vacuum & Optimization

**SQLite Maintenance:**
```sql
-- Reclaim unused space
VACUUM;

-- Rebuild indexes
REINDEX;

-- Update query statistics
ANALYZE;
```

**Scheduled Maintenance:**
- Run VACUUM weekly (on application start)
- Run ANALYZE after bulk operations
- Monitor database file size

### Data Integrity Checks

```sql
-- Check foreign key constraints
PRAGMA foreign_key_check;

-- Check database integrity
PRAGMA integrity_check;

-- Check specific table
PRAGMA integrity_check(table_name);
```

## Query Examples

### Common Queries

**Get all jobs with bullet points for a profile:**
```sql
SELECT 
  j.company_name,
  j.job_title,
  bp.content,
  GROUP_CONCAT(t.name) as tags
FROM jobs j
LEFT JOIN bullet_points bp ON j.id = bp.job_id
LEFT JOIN bullet_tags bt ON bp.id = bt.bullet_point_id
LEFT JOIN tags t ON bt.tag_id = t.id
WHERE j.profile_id = 1
GROUP BY j.id, bp.id
ORDER BY j.start_date DESC, bp.display_order;
```

**Find bullet points by tag:**
```sql
SELECT 
  bp.content,
  j.company_name,
  j.job_title
FROM bullet_points bp
JOIN jobs j ON bp.job_id = j.id
JOIN bullet_tags bt ON bp.id = bt.bullet_point_id
JOIN tags t ON bt.tag_id = t.id
WHERE t.name = 'leadership'
ORDER BY j.start_date DESC;
```

**Get application history with resume count:**
```sql
SELECT 
  ja.company_name,
  ja.position_title,
  ja.application_date,
  ja.status,
  COUNT(gr.id) as resume_count
FROM job_applications ja
LEFT JOIN generated_resumes gr ON ja.id = gr.job_application_id
WHERE ja.profile_id = 1
GROUP BY ja.id
ORDER BY ja.application_date DESC;
```

**Find skills by category:**
```sql
SELECT 
  category,
  GROUP_CONCAT(skill_name, ', ') as skills
FROM skills
WHERE profile_id = 1
GROUP BY category
ORDER BY category;
```

**Get certifications expiring soon:**
```sql
SELECT 
  name,
  issuing_organization,
  expiration_date,
  julianday(expiration_date) - julianday('now') as days_until_expiration
FROM certifications
WHERE profile_id = 1
  AND expiration_date IS NOT NULL
  AND expiration_date > date('now')
  AND expiration_date < date('now', '+90 days')
ORDER BY expiration_date;
```

## Performance Considerations

### Index Usage

- All foreign keys are indexed automatically
- Date columns used in sorting are indexed
- Status fields used in filtering are indexed
- Full-text search on bullet point content (FTS5)

### Query Optimization Tips

1. **Use Eager Loading**
   ```python
   # Load jobs with bullet points in one query
   jobs = session.query(Job).options(
       joinedload(Job.bullet_points)
   ).all()
   ```

2. **Limit Result Sets**
   ```python
   # Paginate large result sets
   jobs = session.query(Job).limit(20).offset(0).all()
   ```

3. **Use Appropriate Indexes**
   - Index columns used in WHERE clauses
   - Index columns used in ORDER BY
   - Avoid over-indexing (slows writes)

### Estimated Row Counts (typical user)

| Table | Estimated Rows | Notes |
|-------|----------------|-------|
| profiles | 1 | Single user in v1.0 |
| jobs | 5-20 | Career history |
| bullet_points | 50-200 | ~10 per job |
| tags | 30-50 | Predefined + custom |
| bullet_tags | 100-400 | ~2 tags per bullet |
| skills | 20-50 | Technical + soft skills |
| education | 1-5 | Degrees/courses |
| certifications | 0-10 | Professional certs |
| job_applications | 10-100 | Active job search |
| generated_resumes | 10-100 | One per application |
| generated_cover_letters | 10-100 | One per application |
| resume_templates | 3-10 | System + user templates |
| cover_letter_sections | 10-30 | Reusable sections |

**Total estimated rows:** 250-650 for typical user

**Database size estimate:** 1-5 MB for typical user

## Security & Privacy

### Current (Desktop v1.0)

1. **Local Storage Only**
   - No cloud synchronization
   - User controls file location
   - Standard file permissions

2. **No Sensitive Data Encryption**
   - Not needed for local desktop
   - OS-level file encryption available
   - Future: Optional database encryption

3. **No Authentication**
   - Single user application
   - No password required
   - Future: Optional app-level password

### Future (Web Version)

1. **Data Encryption**
   - Database encryption at rest
   - TLS for data in transit
   - Encrypted backups

2. **Authentication Required**
   - User login system
   - Password hashing (bcrypt)
   - Session management

3. **Authorization**
   - Users only access their data
   - Row-level security in PostgreSQL
   - API authentication tokens

4. **Compliance**
   - GDPR considerations
   - Data export capability
   - Right to be forgotten
   - Audit logging

## Appendix

### SQL Schema Generation

Complete schema can be generated with:

```bash
# Generate SQL from Alembic
alembic upgrade head --sql > schema.sql

# Or from SQLAlchemy
python -c "from models import Base; from sqlalchemy import create_engine; \
engine = create_engine('sqlite:///'); Base.metadata.create_all(engine)"
```

### ERD Generation Tools

Recommended tools for generating ERD from schema:

- **SchemaSpy** - Java-based, generates HTML docs
- **pgModeler** - Visual database designer
- **DBeaver** - Database client with ER diagram support
- **SQLAlchemy-Utils** - Python library with ERD generation

### Related Documentation

- **ARCHITECTURE.md** - System architecture and design patterns
- **PROJECT_PLAN.md** - Implementation roadmap
- **ADR-0002** - Database choice rationale
- **SETUP.md** - Development environment setup

---

**Database Schema Version:** 1.0.0  
**SQLAlchemy Version:** 2.x  
**SQLite Version:** 3.x  
**Target PostgreSQL Version:** 12+

**Last Updated:** November 4, 2025  
**Next Review:** Upon completion of Phase 2 (Core Data Management)
