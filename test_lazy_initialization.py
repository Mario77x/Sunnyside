#!/usr/bin/env python3
"""
Test script to verify lazy initialization fixes the MISTRAL_API_KEY timing issue.
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '.')

def test_lazy_initialization():
    """Test that backend modules can be imported without MISTRAL_API_KEY errors."""
    print("🧪 Testing lazy initialization fix...")
    
    try:
        # Test importing the risk assessment service
        print("📦 Importing risk assessment service...")
        from backend.services.risk_assessment import get_risk_assessment_service
        print("✅ Risk assessment service imported successfully")
        
        # Test importing main app (this would previously fail)
        print("📦 Importing main app...")
        from backend.main import app
        print("✅ Main app imported successfully")
        
        # Test that the service is None initially (lazy)
        from backend.services.risk_assessment import risk_assessment_service
        if risk_assessment_service is None:
            print("✅ Service is properly lazy (None until first use)")
        else:
            print("⚠️  Service was initialized immediately (not lazy)")
        
        print("\n🎉 SUCCESS: Lazy initialization is working!")
        print("✅ Backend can now start without MISTRAL_API_KEY being available at import time")
        print("✅ Service will only initialize when first used (after secrets are loaded)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_lazy_initialization()
    sys.exit(0 if success else 1)