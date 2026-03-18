#!/usr/bin/env python3

import requests
import json
import time
from typing import Dict, Any

# Backend URL from frontend .env
BACKEND_URL = "https://unrestricted-ai-103.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class LunaBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data if response_data else {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")

    def test_health_check(self):
        """Test 1: Health Check - GET /api/"""
        try:
            response = self.session.get(f"{API_BASE}/")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "status" in data:
                    self.log_test("Health Check", True, "API is responding correctly", data)
                    return True
                else:
                    self.log_test("Health Check", False, "Response missing required fields", data)
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False

    def test_chat_with_luna(self):
        """Test 2: Chat with Luna - POST /api/chat"""
        try:
            payload = {
                "message": "Hi Luna! Tell me about yourself",
                "user_id": "test_user_1"
            }
            
            response = self.session.post(
                f"{API_BASE}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data and "conversation_id" in data:
                    # Check if Luna responds with personality
                    luna_response = data["response"].lower()
                    has_personality = any(word in luna_response for word in ["luna", "i am", "i'm", "companion", "ai"])
                    
                    if has_personality:
                        self.log_test("Chat with Luna", True, "Luna responded with personality", data)
                        return True
                    else:
                        self.log_test("Chat with Luna", False, "Luna response lacks personality", data)
                        return False
                else:
                    self.log_test("Chat with Luna", False, "Response missing required fields", data)
                    return False
            else:
                self.log_test("Chat with Luna", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Chat with Luna", False, f"Exception: {str(e)}")
            return False

    def test_conversation_memory(self):
        """Test 3: Follow-up Conversation (Memory Test)"""
        try:
            payload = {
                "message": "What did I just ask you?",
                "user_id": "test_user_1"
            }
            
            response = self.session.post(
                f"{API_BASE}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data:
                    # Check if Luna remembers the previous question
                    luna_response = data["response"].lower()
                    remembers = any(word in luna_response for word in ["yourself", "about", "tell", "asked", "previous"])
                    
                    if remembers:
                        self.log_test("Conversation Memory", True, "Luna remembers previous conversation", data)
                        return True
                    else:
                        self.log_test("Conversation Memory", False, "Luna doesn't remember previous conversation", data)
                        return False
                else:
                    self.log_test("Conversation Memory", False, "Response missing required fields", data)
                    return False
            else:
                self.log_test("Conversation Memory", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Conversation Memory", False, f"Exception: {str(e)}")
            return False

    def test_code_execution_request(self):
        """Test 4: Code Execution Request"""
        try:
            payload = {
                "message": "Can you write Python code to calculate fibonacci of 10? Wrap it in <execute> tags",
                "user_id": "test_user_2"
            }
            
            response = self.session.post(
                f"{API_BASE}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data:
                    # Check if code was executed
                    has_code_result = "code_executed" in data and data["code_executed"] is not None
                    has_fibonacci = "55" in str(data.get("response", "")) or "55" in str(data.get("code_result", ""))
                    
                    if has_code_result and has_fibonacci:
                        self.log_test("Code Execution Request", True, "Code executed and fibonacci calculated", data)
                        return True
                    elif has_code_result:
                        self.log_test("Code Execution Request", False, "Code executed but fibonacci result unclear", data)
                        return False
                    else:
                        self.log_test("Code Execution Request", False, "No code execution detected", data)
                        return False
                else:
                    self.log_test("Code Execution Request", False, "Response missing required fields", data)
                    return False
            else:
                self.log_test("Code Execution Request", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Code Execution Request", False, f"Exception: {str(e)}")
            return False

    def test_get_conversation_history(self):
        """Test 5: Get Conversation History - GET /api/conversation/test_user_1"""
        try:
            response = self.session.get(f"{API_BASE}/conversation/test_user_1")
            
            if response.status_code == 200:
                data = response.json()
                if "user_id" in data and "messages" in data:
                    messages = data["messages"]
                    if len(messages) >= 4:  # Should have at least 4 messages from our tests
                        self.log_test("Get Conversation History", True, f"Found {len(messages)} messages", data)
                        return True
                    else:
                        self.log_test("Get Conversation History", False, f"Expected at least 4 messages, got {len(messages)}", data)
                        return False
                else:
                    self.log_test("Get Conversation History", False, "Response missing required fields", data)
                    return False
            else:
                self.log_test("Get Conversation History", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Conversation History", False, f"Exception: {str(e)}")
            return False

    def test_clear_conversation(self):
        """Test 6: Clear Conversation - DELETE /api/conversation/test_user_1"""
        try:
            response = self.session.delete(f"{API_BASE}/conversation/test_user_1")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "user_id" in data:
                    # Verify conversation was actually cleared
                    time.sleep(1)
                    verify_response = self.session.get(f"{API_BASE}/conversation/test_user_1")
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        if len(verify_data.get("messages", [])) == 0:
                            self.log_test("Clear Conversation", True, "Conversation successfully cleared", data)
                            return True
                        else:
                            self.log_test("Clear Conversation", False, "Conversation not fully cleared", verify_data)
                            return False
                    else:
                        self.log_test("Clear Conversation", False, "Could not verify conversation clearing")
                        return False
                else:
                    self.log_test("Clear Conversation", False, "Response missing required fields", data)
                    return False
            else:
                self.log_test("Clear Conversation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Clear Conversation", False, f"Exception: {str(e)}")
            return False

    def test_direct_code_execution(self):
        """Test 7: Direct Code Execution - POST /api/execute-code"""
        try:
            payload = {
                "code": "print('Hello from Luna!')"
            }
            
            response = self.session.post(
                f"{API_BASE}/execute-code",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "success" in data and data["success"]:
                    output = data.get("output", "")
                    if "Hello from Luna!" in output:
                        self.log_test("Direct Code Execution", True, "Code executed successfully", data)
                        return True
                    else:
                        self.log_test("Direct Code Execution", False, "Unexpected output", data)
                        return False
                else:
                    error = data.get("error", "Unknown error")
                    self.log_test("Direct Code Execution", False, f"Code execution failed: {error}", data)
                    return False
            else:
                self.log_test("Direct Code Execution", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Direct Code Execution", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"🚀 Starting Luna AI Companion Backend Tests")
        print(f"📍 Backend URL: {BACKEND_URL}")
        print(f"🎯 API Base: {API_BASE}")
        
        tests = [
            self.test_health_check,
            self.test_chat_with_luna,
            self.test_conversation_memory,
            self.test_code_execution_request,
            self.test_get_conversation_history,
            self.test_clear_conversation,
            self.test_direct_code_execution
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
            time.sleep(1)  # Small delay between tests
        
        print(f"\n" + "="*60)
        print(f"📊 FINAL RESULTS")
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"📈 SUCCESS RATE: {passed/(passed+failed)*100:.1f}%")
        print(f"="*60)
        
        return {
            "passed": passed,
            "failed": failed,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = LunaBackendTester()
    results = tester.run_all_tests()