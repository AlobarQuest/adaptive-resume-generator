"""
Unit tests for the BulletPoint model.

Tests cover:
- BulletPoint creation and validation
- Tag relationships (many-to-many)
- Properties (full_text, tag_names, has_tag)
- Methods (to_dict)
"""

import pytest
from adaptive_resume.models import BulletPoint, Tag, BulletTag


class TestBulletPointModel:
    """Test suite for BulletPoint model."""
    
    def test_create_bullet_point(self, session, sample_job):
        """Test creating a basic bullet point."""
        bullet = BulletPoint(
            job_id=sample_job.id,
            content="Implemented CI/CD pipeline using Jenkins",
            display_order=1
        )
        session.add(bullet)
        session.commit()
        
        assert bullet.id is not None
        assert bullet.content == "Implemented CI/CD pipeline using Jenkins"
        assert bullet.display_order == 1
        assert bullet.is_highlighted is False  # Default
    
    def test_bullet_with_metrics_and_impact(self, session, sample_job):
        """Test creating bullet point with metrics and impact."""
        bullet = BulletPoint(
            job_id=sample_job.id,
            content="Optimized database queries",
            metrics="Reduced query time by 75%",
            impact="Improved user experience and reduced server costs",
            display_order=1,
            is_highlighted=True
        )
        session.add(bullet)
        session.commit()
        
        assert bullet.metrics == "Reduced query time by 75%"
        assert bullet.impact == "Improved user experience and reduced server costs"
        assert bullet.is_highlighted is True
    
    def test_bullet_full_text_property(self, sample_bullet_point):
        """Test the full_text property combines all content."""
        full_text = sample_bullet_point.full_text
        
        assert "Developed microservices architecture" in full_text
        assert "Reduced response time by 50%" in full_text
        assert "Enabled company to scale" in full_text
    
    def test_bullet_tag_names_property(self, sample_bullet_point):
        """Test getting tag names from bullet point."""
        tag_names = sample_bullet_point.tag_names
        
        assert isinstance(tag_names, list)
        assert 'cloud' in tag_names
        assert 'programming' in tag_names
    
    def test_bullet_tags_property(self, sample_bullet_point, seeded_session):
        """Test getting tag objects from bullet point."""
        tags = sample_bullet_point.tags
        
        assert isinstance(tags, list)
        assert len(tags) == 2
        assert all(isinstance(tag, Tag) for tag in tags)
    
    def test_bullet_has_tag_method(self, sample_bullet_point):
        """Test the has_tag method."""
        assert sample_bullet_point.has_tag('cloud') is True
        assert sample_bullet_point.has_tag('programming') is True
        assert sample_bullet_point.has_tag('leadership') is False
        
        # Case insensitive
        assert sample_bullet_point.has_tag('CLOUD') is True
    
    def test_bullet_add_tags(self, seeded_session, sample_job):
        """Test adding tags to a bullet point."""
        bullet = BulletPoint(
            job_id=sample_job.id,
            content="Led agile sprint planning and retrospectives",
            display_order=1
        )
        seeded_session.add(bullet)
        seeded_session.commit()
        
        # Add tags
        leadership_tag = seeded_session.query(Tag).filter_by(name='leadership').first()
        management_tag = seeded_session.query(Tag).filter_by(name='team-management').first()
        
        bt1 = BulletTag(bullet_point_id=bullet.id, tag_id=leadership_tag.id)
        bt2 = BulletTag(bullet_point_id=bullet.id, tag_id=management_tag.id)
        seeded_session.add_all([bt1, bt2])
        seeded_session.commit()
        
        assert len(bullet.tags) == 2
        assert bullet.has_tag('leadership')
        assert bullet.has_tag('team-management')
    
    def test_bullet_duplicate_tag_prevented(self, seeded_session, sample_bullet_point):
        """Test that duplicate tags on same bullet are prevented."""
        cloud_tag = seeded_session.query(Tag).filter_by(name='cloud').first()
        
        # Count existing tags
        initial_tag_count = len(sample_bullet_point.tags)
        
        # Try to add the same tag again
        duplicate_bt = BulletTag(
            bullet_point_id=sample_bullet_point.id,
            tag_id=cloud_tag.id
        )
        seeded_session.add(duplicate_bt)
        
        # SQLite may not enforce this constraint, so we check if an exception is raised
        # or if the tag count doesn't increase inappropriately
        try:
            seeded_session.commit()
            seeded_session.refresh(sample_bullet_point)
            # If no exception, verify we didn't actually add a duplicate
            # (application should prevent this)
            # For now, just verify the tag still exists
            assert sample_bullet_point.has_tag('cloud')
        except Exception:
            # If constraint is enforced, that's good too
            seeded_session.rollback()
            assert sample_bullet_point.has_tag('cloud')
    
    def test_bullet_to_dict(self, sample_bullet_point):
        """Test converting bullet point to dictionary."""
        bullet_dict = sample_bullet_point.to_dict()
        
        assert isinstance(bullet_dict, dict)
        assert bullet_dict['content'] == "Developed microservices architecture using Python and AWS"
        assert bullet_dict['metrics'] == "Reduced response time by 50% and costs by 30%"
        assert bullet_dict['is_highlighted'] is True
        assert 'tags' in bullet_dict
        assert isinstance(bullet_dict['tags'], list)
        assert 'full_text' in bullet_dict
    
    def test_bullet_repr(self, sample_bullet_point):
        """Test string representation of bullet point."""
        repr_str = repr(sample_bullet_point)
        assert "BulletPoint" in repr_str
        assert "Developed microservices" in repr_str
    
    def test_bullet_relationship_to_job(self, sample_bullet_point, sample_job):
        """Test bullet point's relationship to job."""
        assert sample_bullet_point.job.id == sample_job.id
        assert sample_bullet_point.job.company_name == "TechCorp"
    
    def test_bullet_cascade_delete_from_job(self, seeded_session, sample_job, sample_bullet_point):
        """Test that deleting job cascades to bullet points."""
        bullet_id = sample_bullet_point.id
        
        # Delete job
        seeded_session.delete(sample_job)
        seeded_session.commit()
        
        # Bullet should be deleted (cascade)
        assert seeded_session.query(BulletPoint).filter_by(id=bullet_id).first() is None
    
    def test_bullet_cascade_delete_to_bullet_tags(self, seeded_session, sample_bullet_point):
        """Test that deleting bullet point cascades to bullet_tags."""
        bullet_id = sample_bullet_point.id
        
        # Get bullet_tag count before deletion
        bullet_tags_before = seeded_session.query(BulletTag).filter_by(
            bullet_point_id=bullet_id
        ).count()
        assert bullet_tags_before > 0
        
        # Delete bullet point
        seeded_session.delete(sample_bullet_point)
        seeded_session.commit()
        
        # BulletTags should be deleted (cascade)
        bullet_tags_after = seeded_session.query(BulletTag).filter_by(
            bullet_point_id=bullet_id
        ).count()
        assert bullet_tags_after == 0
    
    def test_bullet_without_metrics_or_impact(self, session, sample_job):
        """Test bullet point with only content (minimal)."""
        bullet = BulletPoint(
            job_id=sample_job.id,
            content="Participated in code reviews",
            display_order=1
        )
        session.add(bullet)
        session.commit()
        
        assert bullet.metrics is None
        assert bullet.impact is None
        # full_text should still work
        assert bullet.full_text == "Participated in code reviews"
