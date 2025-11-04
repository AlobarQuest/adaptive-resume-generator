# ADR-0002: Database Choice and ORM Strategy

**Status:** Accepted  
**Date:** 2025-11-04  
**Deciders:** AlobarQuest

## Context

The Adaptive Resume Generator needs to store:
- User profile and contact information
- Work history with detailed achievements
- Skills with proficiency levels
- Education and certifications
- Job applications and tracking data
- Generated resume versions
- Cover letter sections and templates

Requirements:
- Single-user desktop application (no concurrent access)
- Local data storage (privacy requirement)
- Fast read/write for GUI responsiveness
- Easy backup and portability
- Future migration to multi-user web application
- No external dependencies for end users

## Decision

We will use:
- **SQLite** as the initial database engine
- **SQLAlchemy** as the ORM (Object-Relational Mapping) layer
- **Alembic** for database migrations
- **Migration path to PostgreSQL** when transitioning to web

## Rationale

### SQLite for Desktop

**Why SQLite:**
- **Zero Configuration:** No server setup, just a file
- **Built into Python:** No external dependencies
- **Perfect for Desktop:** Single-user access pattern
- **Portable:** Entire database is one file (easy backup)
- **Fast:** Excellent performance for our data volume
- **Reliable:** Battle-tested, used by major applications
- **Cross-Platform:** Works identically on Windows and Mac

**Why NOT other databases for desktop:**
- **PostgreSQL:** Requires server installation and management (overkill)
- **MySQL:** Same server requirements as PostgreSQL
- **MongoDB:** Relational data fits our domain better than document model
- **Access/SQL Server:** Platform-specific, not cross-platform

### SQLAlchemy ORM

**Why SQLAlchemy:**
- **Database Abstraction:** Change database without changing code
- **Type Safety:** Python classes represent tables
- **Relationships:** Easy to define and navigate foreign keys
- **Migration Ready:** Switching to PostgreSQL requires minimal changes
- **Query Builder:** Pythonic query construction
- **Session Management:** Handles transactions cleanly
- **Well Documented:** Extensive documentation and community

**Why NOT other ORMs:**
- **Django ORM:** Tied to Django framework (we're not using Django)
- **Peewee:** Simpler but less powerful for complex queries
- **Raw SQL:** No type safety, harder to refactor, database-specific

### Alembic for Migrations

**Why Alembic:**
- **Version Control for Schema:** Track database changes over time
- **Integrates with SQLAlchemy:** Auto-generates migrations from models
- **Rollback Capability:** Can undo migrations if needed
- **Team Collaboration:** Multiple developers can coordinate schema changes
- **Production Safety:** Test migrations before applying

## Database Schema Strategy

### Design Principles
1. **Normalize data** to avoid redundancy
2. **Use foreign keys** for referential integrity
3. **Index frequently queried fields** for performance
4. **Store JSON** for flexible collections (bullet point selections)
5. **Use timestamps** for audit trail

### Key Relationships
```
Profile 1:N Jobs 1:N BulletPoints N:M Tags
Profile 1:N Skills
Profile 1:N Education
Profile 1:N Certifications
Profile 1:N CoverLetterSections

JobApplications N:1 GeneratedResumes
JobApplications N:1 GeneratedCoverLetters
```

### Data Types
- **IDs:** Integer primary keys (auto-increment)
- **Text:** VARCHAR with appropriate lengths
- **Long Text:** TEXT for descriptions and content
- **Dates:** DATE type for date fields
- **Booleans:** BOOLEAN for flags
- **JSON:** For array storage (bullet point selections)
- **Timestamps:** TIMESTAMP for created/updated tracking

## Consequences

### Positive

**Desktop Phase:**
- Zero setup for end users
- Instant startup (no server connection)
- Excellent performance for single user
- Easy backup (copy one file)
- No ongoing server costs
- Works offline automatically

**Development:**
- SQLAlchemy provides clean, Pythonic interface
- Type hints on models improve code quality
- Migrations track schema evolution
- Easy to write tests with in-memory SQLite
- Can seed test data easily

**Future Web Migration:**
- SQLAlchemy abstracts database specifics
- Same Python code works with PostgreSQL
- Alembic migrations work with both databases
- Service layer unchanged during migration

### Negative

**Limitations:**
- Not suitable for concurrent writes (acceptable for desktop)
- Maximum database size ~281 TB (far exceeds our needs)
- No built-in replication (not needed for desktop)
- Limited full-text search (can add FTS5 extension if needed)

**Migration Complexity:**
- Will need to convert SQLite databases when users upgrade to web
- JSON fields might need restructuring for PostgreSQL
- Need to handle data export/import for migration

### Risks and Mitigations

**Risk:** SQLite file corruption if app crashes during write  
**Mitigation:** Use WAL mode, implement proper transaction handling

**Risk:** Users accidentally delete database file  
**Mitigation:** Implement auto-backup feature, store in standard app data location

**Risk:** Large databases (10,000+ bullet points) might slow down  
**Mitigation:** Add indexes, implement pagination in GUI, profile queries

**Risk:** PostgreSQL migration might reveal SQLAlchemy usage issues  
**Mitigation:** Use only standard SQLAlchemy features, avoid SQLite-specific SQL

## Implementation Details

### Database Location
```python
# Desktop version
DATABASE_URL = "sqlite:///data/adaptive_resume.db"

# Use WAL mode for better concurrency and crash safety
PRAGMA journal_mode=WAL;
```

### SQLAlchemy Configuration
```python
# Base model with common fields
class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

### Migration Strategy
```python
# Alembic auto-generate migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Migration Path to PostgreSQL

### When to Migrate
- Moving to web-based multi-user application
- Need for concurrent access
- Advanced search requirements
- Scalability beyond single user

### Migration Steps
1. **Update Database URL:**
   ```python
   # From: sqlite:///data/adaptive_resume.db
   # To: postgresql://user:pass@localhost/adaptive_resume
   ```

2. **Run Alembic Migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Test All Queries:** Verify no SQLite-specific SQL used

4. **Data Migration:** Export SQLite data, import to PostgreSQL

5. **Update Connection Pooling:** Add connection pool configuration

### Expected Changes
- **Minimal Code Changes:** SQLAlchemy abstracts most differences
- **Performance Tuning:** Different indexing strategy for PostgreSQL
- **JSON Handling:** PostgreSQL has native JSON type with better querying
- **Full-Text Search:** PostgreSQL has superior full-text search capabilities

### Estimated Effort
- **Code Changes:** 1-2 days
- **Data Migration Tool:** 2-3 days
- **Testing:** 3-5 days
- **Total:** ~1-2 weeks

## Performance Considerations

### Expected Data Volumes
- Bullet points: 500-2,000 per user
- Jobs: 10-50 per user
- Skills: 20-100 per user
- Applications: 50-500 per user
- Database size: 10-100 MB typical

### Optimization Strategy
- Index foreign keys automatically
- Add composite indexes for common queries
- Use eager loading for relationships when fetching multiple records
- Implement pagination for large lists
- Cache frequently accessed data in memory

### Query Patterns
```python
# Good: Use joins to avoid N+1 queries
jobs = session.query(Job).options(
    joinedload(Job.bullet_points)
).filter(Job.profile_id == profile_id).all()

# Bad: Causes N+1 problem
jobs = session.query(Job).filter(Job.profile_id == profile_id).all()
for job in jobs:
    bullets = job.bullet_points  # Separate query for each job
```

## Testing Strategy

### Unit Tests
- Use in-memory SQLite for fast tests
- Create fixtures with test data
- Test all CRUD operations
- Verify relationship loading
- Test constraint enforcement

### Integration Tests
- Use temporary file-based SQLite
- Test migrations (upgrade/downgrade)
- Test transaction handling
- Verify data integrity

## Review Criteria

Review this decision if:
- Desktop application becomes too slow (unlikely)
- Need for multi-user access emerges earlier than planned
- SQLite limitations are encountered (e.g., full-text search needs)
- PostgreSQL becomes required before web migration

## References

- SQLite Documentation: https://www.sqlite.org/docs.html
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Alembic Documentation: https://alembic.sqlalchemy.org/
- SQLite vs PostgreSQL: https://www.sqlite.org/whentouse.html

## Notes

This decision strongly supports the project's architecture goals:
- **Desktop-first:** SQLite is perfect for single-user applications
- **Future-proof:** SQLAlchemy enables painless PostgreSQL migration
- **Simple deployment:** No database server needed for end users
- **Developer friendly:** Alembic tracks schema evolution cleanly

The migration path to PostgreSQL is well-established and low-risk due to SQLAlchemy's abstraction layer.
