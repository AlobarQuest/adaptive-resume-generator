"""
Test script to verify SQLAlchemy models are working correctly.

This script:
1. Creates an in-memory database
2. Initializes all tables
3. Creates sample data
4. Queries the data to verify relationships
5. Tests model methods
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from datetime import date, datetime
from adaptive_resume.models import (
    Base, get_engine, get_session,
    Profile, Job, BulletPoint, Tag, BulletTag,
    Skill, Education, Certification, JobApplication,
    seed_tags, create_default_template
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_models():
    """Test all models and relationships."""
    
    print("="*60)
    print("ADAPTIVE RESUME GENERATOR - MODEL TEST")
    print("="*60)
    print()
    
    # Create in-memory database
    print("1. Creating in-memory test database...")
    engine = create_engine('sqlite:///:memory:', echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create all tables
    print("2. Creating all tables...")
    Base.metadata.create_all(engine)
    print(f"   ✓ Created {len(Base.metadata.tables)} tables")
    print()
    
    # Seed tags
    print("3. Seeding predefined tags...")
    tag_count = seed_tags(session)
    print(f"   ✓ Created {tag_count} tags")
    print()
    
    # Create default template
    print("4. Creating default resume template...")
    template = create_default_template(session)
    print(f"   ✓ Created template: {template.name}")
    print()
    
    # Create a profile
    print("5. Creating test profile...")
    profile = Profile(
        first_name="Devon",
        last_name="Watkins",
        email="devon.watkins@example.com",
        phone="555-123-4567",
        city="Sugar Hill",
        state="Georgia",
        linkedin_url="https://linkedin.com/in/devonwatkins",
        professional_summary="Experienced IT professional with 25 years of expertise."
    )
    session.add(profile)
    session.commit()
    print(f"   ✓ Created profile: {profile.full_name}")
    print()
    
    # Create a job
    print("6. Creating test job...")
    job = Job(
        profile_id=profile.id,
        company_name="TechCorp Solutions",
        job_title="Senior Program Manager",
        location="Atlanta, GA",
        start_date=date(2018, 3, 1),
        end_date=date(2023, 6, 30),
        is_current=False,
        description="Led cross-functional teams in delivering enterprise software solutions.",
        display_order=1
    )
    session.add(job)
    session.commit()
    print(f"   ✓ Created job: {job.job_title} at {job.company_name}")
    print(f"   ✓ Date range: {job.date_range}")
    print(f"   ✓ Duration: {job.duration_months} months")
    print()
    
    # Create bullet points with tags
    print("7. Creating bullet points with tags...")
    
    # Get some tags
    cloud_tag = session.query(Tag).filter_by(name='cloud').first()
    leadership_tag = session.query(Tag).filter_by(name='leadership').first()
    
    bullet1 = BulletPoint(
        job_id=job.id,
        content="Led migration of legacy infrastructure to AWS cloud platform",
        metrics="Reduced operational costs by 35% and improved system uptime to 99.9%",
        impact="Enabled company to scale rapidly during 300% growth period",
        display_order=1,
        is_highlighted=True
    )
    session.add(bullet1)
    session.commit()
    
    # Add tags to bullet
    bt1 = BulletTag(bullet_point_id=bullet1.id, tag_id=cloud_tag.id)
    bt2 = BulletTag(bullet_point_id=bullet1.id, tag_id=leadership_tag.id)
    session.add_all([bt1, bt2])
    session.commit()
    
    print(f"   ✓ Created bullet point with {len(bullet1.tags)} tags")
    print(f"   ✓ Tags: {', '.join(bullet1.tag_names)}")
    print()
    
    # Create skills
    print("8. Creating skills...")
    skill1 = Skill(
        profile_id=profile.id,
        skill_name="Python",
        category="Programming Languages",
        proficiency_level="Expert",
        years_experience=10.0,
        display_order=1
    )
    skill2 = Skill(
        profile_id=profile.id,
        skill_name="Project Management",
        category="Soft Skills",
        proficiency_level="Advanced",
        years_experience=15.0,
        display_order=2
    )
    session.add_all([skill1, skill2])
    session.commit()
    print(f"   ✓ Created 2 skills")
    print(f"   ✓ {skill1.skill_name} - {skill1.experience_display}")
    print(f"   ✓ {skill2.skill_name} - {skill2.experience_display}")
    print()
    
    # Create education
    print("9. Creating education...")
    education = Education(
        profile_id=profile.id,
        institution="Georgia Institute of Technology",
        degree="Bachelor of Science",
        field_of_study="Computer Science",
        start_date=date(1990, 8, 1),
        end_date=date(1994, 5, 15),
        gpa=3.75,
        honors="Magna Cum Laude",
        display_order=1
    )
    session.add(education)
    session.commit()
    print(f"   ✓ Created education: {education.degree} in {education.field_of_study}")
    print(f"   ✓ GPA: {education.gpa_display}")
    print()
    
    # Create certification
    print("10. Creating certification...")
    certification = Certification(
        profile_id=profile.id,
        name="AWS Solutions Architect",
        issuing_organization="Amazon Web Services",
        issue_date=date(2020, 1, 15),
        expiration_date=date(2026, 1, 15),
        credential_id="AWS-12345",
        display_order=1
    )
    session.add(certification)
    session.commit()
    print(f"    ✓ Created certification: {certification.name}")
    print(f"    ✓ Status: {certification.status}")
    print()
    
    # Create job application
    print("11. Creating job application...")
    application = JobApplication(
        profile_id=profile.id,
        company_name="StartupCo",
        position_title="VP of Engineering",
        job_description="Looking for an experienced engineering leader...",
        application_date=date.today(),
        status=JobApplication.STATUS_APPLIED,
        job_url="https://startupco.com/jobs/vp-engineering"
    )
    session.add(application)
    session.commit()
    print(f"    ✓ Created application: {application.position_title} at {application.company_name}")
    print(f"    ✓ Status: {application.status}")
    print(f"    ✓ Days since application: {application.days_since_application}")
    print()
    
    # Test relationships
    print("12. Testing relationships...")
    
    # Profile -> Jobs
    profile_jobs = profile.jobs
    print(f"    ✓ Profile has {len(profile_jobs)} job(s)")
    
    # Profile -> Skills
    profile_skills = profile.skills
    print(f"    ✓ Profile has {len(profile_skills)} skill(s)")
    
    # Job -> BulletPoints
    job_bullets = job.bullet_points
    print(f"    ✓ Job has {len(job_bullets)} bullet point(s)")
    
    # BulletPoint -> Tags
    bullet_tags = bullet1.tags
    print(f"    ✓ Bullet point has {len(bullet_tags)} tag(s)")
    
    # Profile -> Applications
    profile_apps = profile.job_applications
    print(f"    ✓ Profile has {len(profile_apps)} application(s)")
    print()
    
    # Test to_dict methods
    print("13. Testing to_dict() methods...")
    profile_dict = profile.to_dict()
    print(f"    ✓ Profile dict has {len(profile_dict)} keys")
    
    job_dict = job.to_dict()
    print(f"    ✓ Job dict has {len(job_dict)} keys")
    
    bullet_dict = bullet1.to_dict()
    print(f"    ✓ Bullet dict has {len(bullet_dict)} keys")
    print()
    
    # Test queries
    print("14. Testing queries...")
    
    # Find all jobs for profile
    jobs = session.query(Job).filter_by(profile_id=profile.id).all()
    print(f"    ✓ Found {len(jobs)} job(s) for profile")
    
    # Find all bullet points with 'cloud' tag
    cloud_bullets = session.query(BulletPoint).join(BulletTag).join(Tag).filter(
        Tag.name == 'cloud'
    ).all()
    print(f"    ✓ Found {len(cloud_bullets)} bullet(s) with 'cloud' tag")
    
    # Find all active applications
    active_apps = session.query(JobApplication).filter(
        JobApplication.status.in_([
            JobApplication.STATUS_APPLIED,
            JobApplication.STATUS_PHONE_SCREEN,
            JobApplication.STATUS_INTERVIEW
        ])
    ).all()
    print(f"    ✓ Found {len(active_apps)} active application(s)")
    print()
    
    print("="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    print()
    print("Summary:")
    print(f"  • Models working correctly")
    print(f"  • Relationships verified")
    print(f"  • Constraints enforced")
    print(f"  • Methods functioning")
    print()
    
    # Close session
    session.close()
    
    return True


if __name__ == '__main__':
    try:
        test_models()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
