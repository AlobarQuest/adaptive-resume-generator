#!/usr/bin/env python3
"""
Reset utility for Adaptive Resume Generator.
Provides options to reset database and/or settings for testing.
"""
import os
import sys
from pathlib import Path
import shutil


def get_data_dir():
    """Get the application data directory."""
    return Path.home() / '.adaptive_resume'


def get_db_path():
    """Get the database file path."""
    return get_data_dir() / 'resume_data.db'


def get_settings_path():
    """Get the settings file path."""
    return get_data_dir() / 'settings.json'


def reset_database():
    """Delete the database file."""
    db_path = get_db_path()
    if db_path.exists():
        db_path.unlink()
        print(f"[OK] Database deleted: {db_path}")
        return True
    else:
        print(f"[INFO] Database does not exist: {db_path}")
        return False


def reset_settings():
    """Delete the settings file."""
    settings_path = get_settings_path()
    if settings_path.exists():
        settings_path.unlink()
        print(f"[OK] Settings deleted: {settings_path}")
        return True
    else:
        print(f"[INFO] Settings do not exist: {settings_path}")
        return False


def reset_all():
    """Delete the entire data directory."""
    data_dir = get_data_dir()
    if data_dir.exists():
        shutil.rmtree(data_dir)
        print(f"[OK] All data deleted: {data_dir}")
        return True
    else:
        print(f"[INFO] Data directory does not exist: {data_dir}")
        return False


def create_sample_profile():
    """Create a sample profile for testing."""
    # Import here to avoid issues if database doesn't exist
    from adaptive_resume.models.base import get_session, init_db
    from adaptive_resume.services.profile_service import ProfileService
    from adaptive_resume.services.job_service import JobService
    from adaptive_resume.services.skill_service import SkillService
    from adaptive_resume.services.education_service import EducationService
    from datetime import date

    # Initialize database
    init_db()

    session = get_session()
    try:
        # Create profile
        profile_service = ProfileService(session)
        profile = profile_service.create_profile(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="(555) 123-4567",
            city="San Francisco",
            state="CA",
            linkedin_url="https://linkedin.com/in/johndoe",
            portfolio_url="https://github.com/johndoe",
            professional_summary="Experienced software engineer with 5+ years building scalable web applications."
        )

        # Add some skills
        skill_service = SkillService(session)
        skills = ["Python", "JavaScript", "React", "SQL", "Git", "AWS", "Docker"]
        for skill_name in skills:
            skill_service.create_skill(skill_name)

        # Add education
        education_service = EducationService(session)
        education_service.create_education(
            institution="State University",
            degree="Bachelor of Science",
            field_of_study="Computer Science",
            start_date=date(2015, 9, 1),
            end_date=date(2019, 5, 15),
            gpa=3.7
        )

        # Add a job with bullet points
        job_service = JobService(session)
        job = job_service.create_job(
            company_name="Tech Corp",
            job_title="Software Engineer",
            start_date=date(2019, 6, 1),
            end_date=date(2023, 12, 31),
            location="San Francisco, CA",
            description="Full-stack development for enterprise applications"
        )

        # Add bullet points to the job
        bullets = [
            "Developed RESTful APIs serving 10,000+ daily active users",
            "Reduced page load time by 40% through React optimization",
            "Mentored 3 junior developers on best practices",
        ]
        for bullet_text in bullets:
            job_service.create_bullet_point(job.id, bullet_text)

        session.commit()
        print("\n[OK] Sample profile created successfully!")
        print(f"  Profile: {profile.first_name} {profile.last_name}")
        print(f"  Skills: {len(skills)}")
        print(f"  Jobs: 1 (with {len(bullets)} bullet points)")
        print(f"  Education: 1 entry")

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Error creating sample profile: {e}")
        raise
    finally:
        session.close()


def show_status():
    """Show current data status."""
    data_dir = get_data_dir()
    db_path = get_db_path()
    settings_path = get_settings_path()

    print("\nCurrent Status:")
    print(f"  Data directory: {data_dir}")
    print(f"    Exists: {data_dir.exists()}")
    print(f"  Database: {db_path}")
    print(f"    Exists: {db_path.exists()}")
    if db_path.exists():
        size_mb = db_path.stat().st_size / 1024 / 1024
        print(f"    Size: {size_mb:.2f} MB")
    print(f"  Settings: {settings_path}")
    print(f"    Exists: {settings_path.exists()}")


def main():
    """Main menu for reset operations."""
    print("=" * 60)
    print("Adaptive Resume Generator - Data Reset Utility")
    print("=" * 60)

    show_status()

    print("\nReset Options:")
    print("  1. Reset database only (keeps API key and settings)")
    print("  2. Reset database + settings (complete reset)")
    print("  3. Reset database and create sample profile")
    print("  4. Show status only (no changes)")
    print("  5. Cancel")

    choice = input("\nSelect option (1-5): ").strip()

    if choice == "1":
        print("\n--- Resetting database only ---")
        confirm = input("Are you sure? This cannot be undone. (yes/no): ").strip().lower()
        if confirm == "yes":
            reset_database()
            print("\n[OK] Database reset complete. Settings preserved.")
        else:
            print("Cancelled.")

    elif choice == "2":
        print("\n--- Resetting ALL data (database + settings) ---")
        confirm = input("Are you sure? This will delete your API key. (yes/no): ").strip().lower()
        if confirm == "yes":
            reset_all()
            print("\n[OK] Complete reset done. All data deleted.")
        else:
            print("Cancelled.")

    elif choice == "3":
        print("\n--- Resetting database and creating sample profile ---")
        confirm = input("Are you sure? This will delete existing data. (yes/no): ").strip().lower()
        if confirm == "yes":
            reset_database()
            try:
                create_sample_profile()
                print("\n[OK] Database reset with sample profile created.")
            except Exception as e:
                print(f"\n[ERROR] Failed to create sample profile: {e}")
                return 1
        else:
            print("Cancelled.")

    elif choice == "4":
        print("\n--- Status only (no changes made) ---")

    elif choice == "5":
        print("\nCancelled.")

    else:
        print("\nInvalid choice.")
        return 1

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
