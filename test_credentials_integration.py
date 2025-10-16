#!/usr/bin/env python3
"""
Comprehensive test script for all communication integrations.
Tests EmailJS, Twilio SMS/WhatsApp, and Mistral AI with stored credentials.
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add backend to path
sys.path.append('backend')

from motor.motor_asyncio import AsyncIOMotorClient
from backend.utils.environment import load_secrets_from_mongodb

class CredentialsIntegrationTester:
    def __init__(self):
        self.mongodb_client = None
        self.notification_service = None
        self.llm_service = None
        self.test_results = {}
        
    async def setup(self):
        """Setup MongoDB connection and load secrets."""
        try:
            # Connect to MongoDB
            mongodb_uri = os.getenv("MONGODB_URI")
            if not mongodb_uri:
                raise ValueError("MONGODB_URI not found in environment")
            
            self.mongodb_client = AsyncIOMotorClient(mongodb_uri)
            
            # Test connection
            await self.mongodb_client.admin.command('ping')
            print("✓ Connected to MongoDB")
            
            # Load secrets from MongoDB
            await load_secrets_from_mongodb(
                self.mongodb_client, 
                os.getenv("DATABASE_NAME", "sunnyside"),
                "development"
            )
            print("✓ Loaded secrets from MongoDB")
            
            # Initialize services after secrets are loaded
            from backend.services.notifications import NotificationService
            from backend.services.llm import LLMService
            
            self.notification_service = NotificationService()
            self.llm_service = LLMService()
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    async def test_emailjs_credentials(self):
        """Test EmailJS credentials and configuration."""
        print("\n🔧 Testing EmailJS Integration...")
        print("=" * 50)
        
        test_result = {
            "service": "EmailJS",
            "tests": {},
            "overall_status": "UNKNOWN"
        }
        
        try:
            # Check if credentials are loaded
            public_key = os.getenv("EMAILJS_PUBLIC_KEY")
            service_id = os.getenv("EMAILJS_SERVICE_ID")
            
            test_result["tests"]["credentials_loaded"] = {
                "status": "PASS" if public_key and service_id else "FAIL",
                "details": {
                    "public_key_present": bool(public_key),
                    "service_id_present": bool(service_id),
                    "public_key_preview": f"{public_key[:8]}..." if public_key else "Not found",
                    "service_id_preview": f"{service_id[:8]}..." if service_id else "Not found"
                }
            }
            
            # Check template IDs
            template_ids = {
                "activity_invitation": os.getenv("EMAILJS_ACTIVITY_INVITATION_TEMPLATE_ID"),
                "activity_response": os.getenv("EMAILJS_ACTIVITY_RESPONSE_TEMPLATE_ID"),
                "activity_cancellation": os.getenv("EMAILJS_ACTIVITY_CANCELLATION_TEMPLATE_ID"),
                "upcoming_reminder": os.getenv("EMAILJS_UPCOMING_ACTIVITY_REMINDER_TEMPLATE_ID"),
                "password_reset": os.getenv("EMAILJS_PASSWORD_RESET_TEMPLATE_ID")
            }
            
            template_status = all(template_ids.values())
            test_result["tests"]["template_ids"] = {
                "status": "PASS" if template_status else "PARTIAL",
                "details": {k: bool(v) for k, v in template_ids.items()}
            }
            
            # Test notification service initialization
            if hasattr(self.notification_service, 'emailjs_public_key'):
                test_result["tests"]["service_initialization"] = {
                    "status": "PASS",
                    "details": "NotificationService initialized with EmailJS credentials"
                }
            else:
                test_result["tests"]["service_initialization"] = {
                    "status": "FAIL",
                    "details": "NotificationService not properly initialized"
                }
            
            # Overall status
            all_tests_pass = all(
                test["status"] in ["PASS", "PARTIAL"] 
                for test in test_result["tests"].values()
            )
            test_result["overall_status"] = "PASS" if all_tests_pass else "FAIL"
            
            print(f"✓ Credentials loaded: {test_result['tests']['credentials_loaded']['status']}")
            print(f"✓ Template IDs: {test_result['tests']['template_ids']['status']}")
            print(f"✓ Service initialization: {test_result['tests']['service_initialization']['status']}")
            
        except Exception as e:
            test_result["tests"]["error"] = {
                "status": "FAIL",
                "details": str(e)
            }
            test_result["overall_status"] = "FAIL"
            print(f"❌ EmailJS test failed: {e}")
        
        self.test_results["emailjs"] = test_result
        return test_result["overall_status"] == "PASS"
    
    async def test_twilio_credentials(self):
        """Test Twilio credentials and configuration."""
        print("\n📱 Testing Twilio Integration...")
        print("=" * 50)
        
        test_result = {
            "service": "Twilio",
            "tests": {},
            "overall_status": "UNKNOWN"
        }
        
        try:
            # Check if credentials are loaded
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            phone_number = os.getenv("TWILIO_PHONE_NUMBER")
            
            test_result["tests"]["credentials_loaded"] = {
                "status": "PASS" if all([account_sid, auth_token, phone_number]) else "FAIL",
                "details": {
                    "account_sid_present": bool(account_sid),
                    "auth_token_present": bool(auth_token),
                    "phone_number_present": bool(phone_number),
                    "account_sid_preview": f"{account_sid[:8]}..." if account_sid else "Not found",
                    "phone_number": phone_number if phone_number else "Not found"
                }
            }
            
            # Test Twilio client initialization
            try:
                from twilio.rest import Client
                if account_sid and auth_token:
                    client = Client(account_sid, auth_token)
                    # Test account fetch (this validates credentials)
                    account = client.api.accounts(account_sid).fetch()
                    test_result["tests"]["client_validation"] = {
                        "status": "PASS",
                        "details": f"Account validated: {account.friendly_name}"
                    }
                else:
                    test_result["tests"]["client_validation"] = {
                        "status": "FAIL",
                        "details": "Missing credentials for client initialization"
                    }
            except ImportError:
                test_result["tests"]["client_validation"] = {
                    "status": "SKIP",
                    "details": "Twilio library not installed"
                }
            except Exception as e:
                test_result["tests"]["client_validation"] = {
                    "status": "FAIL",
                    "details": f"Client validation failed: {str(e)}"
                }
            
            # Test notification service Twilio integration
            if hasattr(self.notification_service, 'twilio_client'):
                test_result["tests"]["service_integration"] = {
                    "status": "PASS",
                    "details": "NotificationService has Twilio client"
                }
            else:
                test_result["tests"]["service_integration"] = {
                    "status": "FAIL",
                    "details": "NotificationService missing Twilio client"
                }
            
            # Overall status
            critical_tests = ["credentials_loaded", "client_validation"]
            critical_pass = all(
                test_result["tests"].get(test, {}).get("status") == "PASS"
                for test in critical_tests
                if test in test_result["tests"]
            )
            test_result["overall_status"] = "PASS" if critical_pass else "FAIL"
            
            print(f"✓ Credentials loaded: {test_result['tests']['credentials_loaded']['status']}")
            if "client_validation" in test_result["tests"]:
                print(f"✓ Client validation: {test_result['tests']['client_validation']['status']}")
            if "service_integration" in test_result["tests"]:
                print(f"✓ Service integration: {test_result['tests']['service_integration']['status']}")
            
        except Exception as e:
            test_result["tests"]["error"] = {
                "status": "FAIL",
                "details": str(e)
            }
            test_result["overall_status"] = "FAIL"
            print(f"❌ Twilio test failed: {e}")
        
        self.test_results["twilio"] = test_result
        return test_result["overall_status"] == "PASS"
    
    async def test_mistral_credentials(self):
        """Test Mistral AI credentials and configuration."""
        print("\n🤖 Testing Mistral AI Integration...")
        print("=" * 50)
        
        test_result = {
            "service": "Mistral AI",
            "tests": {},
            "overall_status": "UNKNOWN"
        }
        
        try:
            # Check if credentials are loaded
            api_key = os.getenv("MISTRAL_API_KEY")
            
            test_result["tests"]["credentials_loaded"] = {
                "status": "PASS" if api_key else "FAIL",
                "details": {
                    "api_key_present": bool(api_key),
                    "api_key_preview": f"{api_key[:8]}..." if api_key else "Not found"
                }
            }
            
            # Test LLM service initialization
            if self.llm_service and hasattr(self.llm_service, 'client'):
                test_result["tests"]["service_initialization"] = {
                    "status": "PASS",
                    "details": "LLMService initialized successfully"
                }
                
                # Test a simple API call using parse_intent method
                try:
                    response = await self.llm_service.parse_intent("Test activity: going for a walk")
                    if response and response.get("success"):
                        test_result["tests"]["api_call"] = {
                            "status": "PASS",
                            "details": f"API responded successfully with activity: {response.get('activity', {}).get('type', 'unknown')}"
                        }
                    else:
                        test_result["tests"]["api_call"] = {
                            "status": "PARTIAL",
                            "details": f"API responded but with issues: {response.get('error', 'Unknown error')}" if response else "No response"
                        }
                except Exception as e:
                    test_result["tests"]["api_call"] = {
                        "status": "FAIL",
                        "details": f"API call failed: {str(e)}"
                    }
            else:
                test_result["tests"]["service_initialization"] = {
                    "status": "FAIL",
                    "details": "LLMService not properly initialized"
                }
            
            # Overall status
            critical_tests = ["credentials_loaded", "service_initialization"]
            critical_pass = all(
                test_result["tests"].get(test, {}).get("status") in ["PASS", "PARTIAL"]
                for test in critical_tests
            )
            test_result["overall_status"] = "PASS" if critical_pass else "FAIL"
            
            print(f"✓ Credentials loaded: {test_result['tests']['credentials_loaded']['status']}")
            print(f"✓ Service initialization: {test_result['tests']['service_initialization']['status']}")
            if "api_call" in test_result["tests"]:
                print(f"✓ API call test: {test_result['tests']['api_call']['status']}")
            
        except Exception as e:
            test_result["tests"]["error"] = {
                "status": "FAIL",
                "details": str(e)
            }
            test_result["overall_status"] = "FAIL"
            print(f"❌ Mistral AI test failed: {e}")
        
        self.test_results["mistral"] = test_result
        return test_result["overall_status"] == "PASS"
    
    async def test_notification_templates(self):
        """Test notification templates and functionality."""
        print("\n📧 Testing Notification Templates...")
        print("=" * 50)
        
        test_result = {
            "service": "Notification Templates",
            "tests": {},
            "overall_status": "UNKNOWN"
        }
        
        try:
            # Test activity invitation template
            test_data = {
                "activity_title": "Test Activity",
                "activity_date": "2025-10-20",
                "activity_time": "14:00",
                "organizer_name": "Test Organizer",
                "invite_link": "https://test.com/invite/123",
                "recipient_email": "test@example.com"
            }
            
            # Test email template rendering (if available)
            if hasattr(self.notification_service, 'send_activity_invitation'):
                test_result["tests"]["invitation_template"] = {
                    "status": "PASS",
                    "details": "Activity invitation method available"
                }
            else:
                test_result["tests"]["invitation_template"] = {
                    "status": "FAIL",
                    "details": "Activity invitation method not found"
                }
            
            # Test SMS template (if available)
            if hasattr(self.notification_service, 'send_sms'):
                test_result["tests"]["sms_template"] = {
                    "status": "PASS",
                    "details": "SMS sending method available"
                }
            else:
                test_result["tests"]["sms_template"] = {
                    "status": "FAIL",
                    "details": "SMS sending method not found"
                }
            
            # Overall status
            test_result["overall_status"] = "PASS" if any(
                test["status"] == "PASS" for test in test_result["tests"].values()
            ) else "FAIL"
            
            for test_name, result in test_result["tests"].items():
                print(f"✓ {test_name}: {result['status']}")
            
        except Exception as e:
            test_result["tests"]["error"] = {
                "status": "FAIL",
                "details": str(e)
            }
            test_result["overall_status"] = "FAIL"
            print(f"❌ Template test failed: {e}")
        
        self.test_results["templates"] = test_result
        return test_result["overall_status"] == "PASS"
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE CREDENTIALS INTEGRATION REPORT")
        print("=" * 80)
        
        total_services = len(self.test_results)
        passed_services = sum(1 for result in self.test_results.values() 
                            if result["overall_status"] == "PASS")
        
        print(f"📈 Overall Status: {passed_services}/{total_services} services operational")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for service_name, result in self.test_results.items():
            print(f"\n🔧 {result['service']}:")
            print(f"   Status: {result['overall_status']}")
            
            for test_name, test_result in result["tests"].items():
                status_icon = "✅" if test_result["status"] == "PASS" else "⚠️" if test_result["status"] == "PARTIAL" else "❌"
                print(f"   {status_icon} {test_name}: {test_result['status']}")
                if isinstance(test_result["details"], dict):
                    for key, value in test_result["details"].items():
                        print(f"      - {key}: {value}")
                else:
                    print(f"      - {test_result['details']}")
        
        # Missing credentials analysis
        print(f"\n🔍 MISSING CREDENTIALS ANALYSIS:")
        missing_items = []
        
        # Check for any missing template IDs or other credentials
        if "emailjs" in self.test_results:
            emailjs_tests = self.test_results["emailjs"]["tests"]
            if "template_ids" in emailjs_tests:
                template_details = emailjs_tests["template_ids"]["details"]
                for template, present in template_details.items():
                    if not present:
                        missing_items.append(f"EmailJS template: {template}")
        
        if missing_items:
            for item in missing_items:
                print(f"   ❌ {item}")
        else:
            print("   ✅ All required credentials are present")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        recommendations = []
        
        for service_name, result in self.test_results.items():
            if result["overall_status"] == "FAIL":
                recommendations.append(f"Fix {result['service']} integration issues")
            elif result["overall_status"] == "PARTIAL":
                recommendations.append(f"Complete {result['service']} configuration")
        
        if not recommendations:
            recommendations.append("All services are operational - ready for production testing")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        return {
            "summary": {
                "total_services": total_services,
                "operational_services": passed_services,
                "success_rate": f"{(passed_services/total_services)*100:.1f}%"
            },
            "services": self.test_results,
            "missing_credentials": missing_items,
            "recommendations": recommendations
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.mongodb_client:
            self.mongodb_client.close()

async def main():
    print("🚀 Sunnyside Credentials Integration Testing")
    print("=" * 80)
    
    tester = CredentialsIntegrationTester()
    
    try:
        # Setup
        if not await tester.setup():
            print("❌ Setup failed, exiting")
            sys.exit(1)
        
        # Run all tests
        print("\n🧪 Running Integration Tests...")
        
        await tester.test_emailjs_credentials()
        await tester.test_twilio_credentials()
        await tester.test_mistral_credentials()
        await tester.test_notification_templates()
        
        # Generate report
        report = tester.generate_report()
        
        # Save report to file
        with open("credentials_integration_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: credentials_integration_report.json")
        
        # Exit with appropriate code
        success_rate = float(report["summary"]["success_rate"].rstrip("%"))
        sys.exit(0 if success_rate >= 75 else 1)
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())