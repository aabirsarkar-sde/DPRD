import requests
import sys
import json
from datetime import datetime

class PRDGeneratorAPITester:
    def __init__(self, base_url="https://clearprd.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "status": "PASS" if success else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name}: {details}")
        return success

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'N/A')}"
            return self.log_test("API Root", success, details)
        except Exception as e:
            return self.log_test("API Root", False, f"Error: {str(e)}")

    def test_analyze_endpoint(self):
        """Test /api/analyze endpoint"""
        test_idea = "I want to build a task management app where users can create, organize, and track their daily tasks with categories and due dates."
        
        try:
            response = requests.post(
                f"{self.api_url}/analyze",
                json={"idea": test_idea},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                questions = data.get("questions", [])
                details += f", Questions count: {len(questions)}"
                
                # Validate question structure
                if len(questions) == 8:
                    categories = [q.get("category") for q in questions]
                    expected_categories = ["auth", "data_complexity", "ui_layout", "ui_components", "features", "edge_cases", "integrations"]
                    has_all_categories = len(set(categories)) >= 6  # At least 6 different categories
                    
                    if has_all_categories:
                        details += f", Categories found: {len(set(categories))}/7"
                        # Check question structure
                        valid_structure = True
                        for q in questions:
                            if not all(key in q for key in ["id", "question", "options", "category"]):
                                valid_structure = False
                                break
                            if len(q.get("options", [])) < 3:
                                valid_structure = False
                                break
                        
                        if valid_structure:
                            details += ", Valid question structure"
                        else:
                            success = False
                            details += ", Invalid question structure"
                    else:
                        success = False
                        details += f", Missing categories. Found: {categories}"
                else:
                    success = False
                    details += f", Expected 8 questions, got {len(questions)}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"
            
            return self.log_test("Analyze Endpoint", success, details)
            
        except Exception as e:
            return self.log_test("Analyze Endpoint", False, f"Error: {str(e)}")

    def test_generate_prd_endpoint(self):
        """Test /api/generate-prd endpoint"""
        test_data = {
            "idea": "A simple note-taking app",
            "answers": {
                "q1": "basic_auth",
                "q2": "simple_storage", 
                "q3": "basic_validation"
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/generate-prd",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                prd = data.get("prd", "")
                details += f", PRD length: {len(prd)} chars"
                
                # Check if PRD contains expected sections
                expected_sections = ["# ", "## ", "Tech Stack", "Data Schema", "Core Features"]
                found_sections = sum(1 for section in expected_sections if section in prd)
                details += f", Sections found: {found_sections}/{len(expected_sections)}"
                
                if len(prd) < 100:
                    success = False
                    details += ", PRD too short"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"
            
            return self.log_test("Generate PRD Endpoint", success, details)
            
        except Exception as e:
            return self.log_test("Generate PRD Endpoint", False, f"Error: {str(e)}")

    def test_status_endpoints(self):
        """Test status check endpoints"""
        # Test POST /status
        try:
            test_data = {"client_name": "test_client"}
            response = requests.post(
                f"{self.api_url}/status",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            success = response.status_code == 200
            details = f"POST Status: {response.status_code}"
            
            if success:
                data = response.json()
                if "id" in data and "client_name" in data:
                    details += ", Valid response structure"
                else:
                    success = False
                    details += ", Invalid response structure"
            
            post_success = self.log_test("POST Status Endpoint", success, details)
            
        except Exception as e:
            post_success = self.log_test("POST Status Endpoint", False, f"Error: {str(e)}")
        
        # Test GET /status
        try:
            response = requests.get(f"{self.api_url}/status", timeout=10)
            success = response.status_code == 200
            details = f"GET Status: {response.status_code}"
            
            if success:
                data = response.json()
                if isinstance(data, list):
                    details += f", Found {len(data)} status checks"
                else:
                    success = False
                    details += ", Expected list response"
            
            get_success = self.log_test("GET Status Endpoint", success, details)
            
        except Exception as e:
            get_success = self.log_test("GET Status Endpoint", False, f"Error: {str(e)}")
        
        return post_success and get_success

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        # Test analyze with empty idea
        try:
            response = requests.post(
                f"{self.api_url}/analyze",
                json={"idea": ""},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            # Should handle empty idea gracefully
            success = response.status_code in [400, 422, 500]  # Any error status is acceptable
            details = f"Empty idea status: {response.status_code}"
            
            empty_idea_test = self.log_test("Error Handling - Empty Idea", success, details)
            
        except Exception as e:
            empty_idea_test = self.log_test("Error Handling - Empty Idea", False, f"Error: {str(e)}")
        
        # Test generate-prd with missing answers
        try:
            response = requests.post(
                f"{self.api_url}/generate-prd",
                json={"idea": "test", "answers": {}},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            # Should handle missing answers gracefully
            success = response.status_code in [400, 422, 500]
            details = f"Missing answers status: {response.status_code}"
            
            missing_answers_test = self.log_test("Error Handling - Missing Answers", success, details)
            
        except Exception as e:
            missing_answers_test = self.log_test("Error Handling - Missing Answers", False, f"Error: {str(e)}")
        
        return empty_idea_test and missing_answers_test

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting PRD Generator API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run tests
        self.test_api_root()
        self.test_status_endpoints()
        self.test_analyze_endpoint()
        self.test_generate_prd_endpoint()
        self.test_error_handling()
        
        # Print summary
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check details above.")
            return 1

    def get_test_summary(self):
        """Get test summary for reporting"""
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "test_results": self.test_results
        }

def main():
    tester = PRDGeneratorAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())