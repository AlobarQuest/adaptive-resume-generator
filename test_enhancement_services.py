"""
Simple test script to verify enhancement services work independently.

This script tests:
1. BulletEnhancer with template-based enhancement
2. AIEnhancementService (if API key is configured)
3. Settings and encryption

Run this script from the project root:
    python test_enhancement_services.py
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from adaptive_resume.services.bullet_enhancer import BulletEnhancer
from adaptive_resume.services.ai_enhancement_service import AIEnhancementService
from adaptive_resume.config.settings import Settings


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_bullet_enhancer():
    """Test the rule-based bullet enhancer."""
    print_section("Testing BulletEnhancer (Rule-Based)")
    
    enhancer = BulletEnhancer()
    
    # Test 1: Analyze a bullet
    test_bullet = "Managed a team and improved processes"
    print(f"\nOriginal bullet: {test_bullet}")
    
    category, confidence = enhancer.analyze_bullet(test_bullet)
    print(f"✓ Analysis: category='{category}', confidence={confidence:.2f}")
    
    # Test 2: Extract info
    extracted = enhancer.extract_existing_info(test_bullet)
    print(f"✓ Extracted info: {extracted}")
    
    # Test 3: Generate enhanced bullet
    responses = {
        'led': 'cross-functional team of 8',
        'achieved': 'reduced processing time by 35%',
        'scope': 'quarterly product launches'
    }
    
    enhanced = enhancer.generate_enhanced_bullet('leadership', responses)
    print(f"\n✓ Enhanced bullet:\n  {enhanced}")
    
    # Test 4: List available templates
    print(f"\n✓ Available templates: {len(enhancer.TEMPLATES)}")
    for key, template in list(enhancer.TEMPLATES.items())[:3]:
        print(f"  - {template.category}")
    print(f"  ... and {len(enhancer.TEMPLATES) - 3} more")
    
    print("\n✅ BulletEnhancer tests passed!")
    return True


def test_settings():
    """Test settings and encryption."""
    print_section("Testing Settings & Encryption")
    
    settings = Settings()
    
    # Test 1: Check if API key exists
    has_key = settings.get_api_key() is not None
    print(f"✓ API key configured: {has_key}")
    
    if has_key:
        key = settings.get_api_key()
        print(f"  Key length: {len(key)} characters")
        print(f"  Key preview: {key[:7]}...{key[-4:]}")
    
    # Test 2: Check AI enabled status
    ai_enabled = settings.ai_enabled
    print(f"✓ AI enhancement enabled: {ai_enabled}")
    
    # Test 3: Test encryption (without saving)
    test_key = "sk-ant-test-key-12345"
    print(f"\n✓ Testing encryption with test key: {test_key[:10]}...")
    
    # Just verify encryption manager works
    from adaptive_resume.config.encryption_manager import EncryptionManager
    em = EncryptionManager()
    encrypted = em.encrypt(test_key)
    decrypted = em.decrypt(encrypted)
    
    if decrypted == test_key:
        print(f"✓ Encryption/decryption successful")
    else:
        print(f"✗ Encryption/decryption FAILED")
        return False
    
    print("\n✅ Settings tests passed!")
    return True


def test_ai_service():
    """Test AI enhancement service."""
    print_section("Testing AIEnhancementService")
    
    ai_service = AIEnhancementService()
    
    # Test 1: Check availability
    print(f"✓ AI service available: {ai_service.is_available}")
    
    if not ai_service.is_available:
        print("\n⚠️  AI enhancement is not enabled.")
        print("   To enable AI enhancement:")
        print("   1. Get an API key from https://console.anthropic.com")
        print("   2. Run the GUI and go to File > Settings")
        print("   3. Enter your API key and enable AI enhancement")
        print("\n✅ AIEnhancementService tests passed (skipped - not configured)")
        return True
    
    # Test 2: Enhance a bullet (if available)
    test_bullet = "Developed software features and fixed bugs"
    print(f"\nTest bullet: {test_bullet}")
    print("Requesting AI enhancement (this may take a few seconds)...")
    
    try:
        suggestions = ai_service.enhance_bullet(test_bullet)
        
        if suggestions and len(suggestions) > 0:
            print(f"\n✓ Received {len(suggestions)} suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"\n  Suggestion {i}: {suggestion['focus']}")
                print(f"  {suggestion['text']}")
            print("\n✅ AIEnhancementService tests passed!")
            return True
        else:
            print("\n✗ No suggestions received")
            return False
            
    except Exception as e:
        print(f"\n✗ AI enhancement failed: {e}")
        print("   This could be due to:")
        print("   - Invalid API key")
        print("   - Network connectivity issues")
        print("   - API rate limits")
        return False


def main():
    """Run all tests."""
    print("\n" + "█" * 60)
    print("  ENHANCEMENT SERVICES TEST SUITE")
    print("█" * 60)
    
    results = []
    
    # Test 1: BulletEnhancer
    try:
        results.append(("BulletEnhancer", test_bullet_enhancer()))
    except Exception as e:
        print(f"\n✗ BulletEnhancer test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("BulletEnhancer", False))
    
    # Test 2: Settings
    try:
        results.append(("Settings", test_settings()))
    except Exception as e:
        print(f"\n✗ Settings test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Settings", False))
    
    # Test 3: AI Service
    try:
        results.append(("AIEnhancementService", test_ai_service()))
    except Exception as e:
        print(f"\n✗ AIEnhancementService test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("AIEnhancementService", False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("  🎉 ALL TESTS PASSED!")
    else:
        print("  ⚠️  SOME TESTS FAILED")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
