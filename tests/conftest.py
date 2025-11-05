"""
pytest configuration and fixtures for Adaptive Resume Generator tests.

This file provides shared fixtures that can be used across all tests.
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from adaptive_resume.models.base import Base
from adaptive_resume.models import (
    Profile, Job, BulletPoint, Tag, BulletTag,
    Skill, Education, Certification, JobApplication,
    seed_tags, create_default_template
)


@pytest.fixture(scope='function')
def engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope='function')
def session(engine):
    """Create a database session for testing."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope='function')
def seeded_session(session):
    """Create a session with predefined tags seeded."""
    seed_tags(session)
    yield session


@pytest.fixture(scope='function')
def sample_profile(session):
    """Create a sample profile for testing."""
    profile = Profile(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="555-123-4567",
        city="Atlanta",
        state="Georgia",
        linkedin_url="https://linkedin.com/in/johndoe",
        professional_summary="Experienced software engineer with 10 years of expertise."
    )
    session.add(profile)
    session.commit()
    return profile


@pytest.fixture(scope='function')
def sample_job(session, sample_profile):
    """Create a sample job for testing."""
    job = Job(
        profile_id=sample_profile.id,
        company_name="TechCorp",
        job_title="Senior Software Engineer",
        location="Atlanta, GA",
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
        is_current=False,
        description="Led development of enterprise applications.",
        display_order=1
    )
    session.add(job)
    session.commit()
    return job


@pytest.fixture(scope='function')
def sample_bullet_point(seeded_session, sample_job):
    """Create a sample bullet point with tags for testing."""
    bullet = BulletPoint(
        job_id=sample_job.id,
        content="Developed microservices architecture using Python and AWS",
        metrics="Reduced response time by 50% and costs by 30%",
        impact="Enabled company to scale to 1M users",
        display_order=1,
        is_highlighted=True
    )
    seeded_session.add(bullet)
    seeded_session.commit()
    
    # Add some tags
    cloud_tag = seeded_session.query(Tag).filter_by(name='cloud').first()
    programming_tag = seeded_session.query(Tag).filter_by(name='programming').first()
    
    if cloud_tag:
        bt1 = BulletTag(bullet_point_id=bullet.id, tag_id=cloud_tag.id)
        seeded_session.add(bt1)
    if programming_tag:
        bt2 = BulletTag(bullet_point_id=bullet.id, tag_id=programming_tag.id)
        seeded_session.add(bt2)
    
    seeded_session.commit()
    return bullet


@pytest.fixture(scope='function')
def sample_skill(session, sample_profile):
    """Create a sample skill for testing."""
    skill = Skill(
        profile_id=sample_profile.id,
        skill_name="Python",
        category="Programming Languages",
        proficiency_level="Expert",
        years_experience=10.0,
        display_order=1
    )
    session.add(skill)
    session.commit()
    return skill


@pytest.fixture(scope='function')
def sample_education(session, sample_profile):
    """Create a sample education entry for testing."""
    education = Education(
        profile_id=sample_profile.id,
        institution="Georgia Tech",
        degree="Bachelor of Science",
        field_of_study="Computer Science",
        start_date=date(2010, 8, 1),
        end_date=date(2014, 5, 15),
        gpa=3.75,
        honors="Magna Cum Laude",
        display_order=1
    )
    session.add(education)
    session.commit()
    return education


@pytest.fixture(scope='function')
def sample_certification(session, sample_profile):
    """Create a sample certification for testing."""
    certification = Certification(
        profile_id=sample_profile.id,
        name="AWS Solutions Architect",
        issuing_organization="Amazon Web Services",
        issue_date=date(2020, 1, 15),
        expiration_date=date(2026, 1, 15),
        credential_id="AWS-12345",
        display_order=1
    )
    session.add(certification)
    session.commit()
    return certification


@pytest.fixture(scope='function')
def sample_job_application(session, sample_profile):
    """Create a sample job application for testing."""
    application = JobApplication(
        profile_id=sample_profile.id,
        company_name="StartupCo",
        position_title="VP of Engineering",
        job_description="Looking for an experienced engineering leader...",
        application_date=date.today(),
        status=JobApplication.STATUS_APPLIED,
        job_url="https://startupco.com/jobs/vp-engineering"
    )
    session.add(application)
    session.commit()
    return application
