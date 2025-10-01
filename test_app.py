#!/usr/bin/env python3
"""
Unit tests for AI Code Assistant
Author: Gabriel Demetrios Lafis
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

from app import app, AICodeAssistant, TaskType, CodeRequest, CodeResponse

class TestTaskType(unittest.TestCase):
    """Test cases for TaskType enum"""
    
    def test_task_type_values(self):
        """Test TaskType enum values"""
        self.assertEqual(TaskType.CODE_GENERATION.value, "code_generation")
        self.assertEqual(TaskType.CODE_COMPLETION.value, "code_completion")
        self.assertEqual(TaskType.BUG_DETECTION.value, "bug_detection")
        self.assertEqual(TaskType.DOCUMENTATION.value, "documentation")
        self.assertEqual(TaskType.CODE_REVIEW.value, "code_review")
        self.assertEqual(TaskType.OPTIMIZATION.value, "optimization")

class TestCodeRequest(unittest.TestCase):
    """Test cases for CodeRequest data class"""
    
    def test_code_request_creation(self):
        """Test CodeRequest creation"""
        request = CodeRequest(
            task_type=TaskType.CODE_GENERATION,
            language="python",
            prompt="Create a function",
            code="def example():",
            context="Test context"
        )
        
        self.assertEqual(request.task_type, TaskType.CODE_GENERATION)
        self.assertEqual(request.language, "python")
        self.assertEqual(request.prompt, "Create a function")
        self.assertEqual(request.code, "def example():")
        self.assertEqual(request.context, "Test context")
    
    def test_code_request_optional_fields(self):
        """Test CodeRequest with optional fields"""
        request = CodeRequest(
            task_type=TaskType.BUG_DETECTION,
            language="javascript",
            prompt="Find bugs"
        )
        
        self.assertEqual(request.task_type, TaskType.BUG_DETECTION)
        self.assertEqual(request.language, "javascript")
        self.assertEqual(request.prompt, "Find bugs")
        self.assertIsNone(request.code)
        self.assertIsNone(request.context)

class TestCodeResponse(unittest.TestCase):
    """Test cases for CodeResponse data class"""
    
    def test_code_response_creation(self):
        """Test CodeResponse creation"""
        now = datetime.now()
        response = CodeResponse(
            task_type=TaskType.CODE_GENERATION,
            language="python",
            result="def example(): pass",
            suggestions=["Add docstring", "Add tests"],
            confidence=0.9,
            timestamp=now
        )
        
        self.assertEqual(response.task_type, TaskType.CODE_GENERATION)
        self.assertEqual(response.language, "python")
        self.assertEqual(response.result, "def example(): pass")
        self.assertEqual(response.suggestions, ["Add docstring", "Add tests"])
        self.assertEqual(response.confidence, 0.9)
        self.assertEqual(response.timestamp, now)

class TestAICodeAssistant(unittest.TestCase):
    """Test cases for AICodeAssistant class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.assistant = AICodeAssistant()
    
    def test_initialization_without_api_key(self):
        """Test assistant initialization without OpenAI API key"""
        with patch.dict(os.environ, {}, clear=True):
            assistant = AICodeAssistant()
            self.assertFalse(assistant.ai_enabled)
            self.assertIn('python', assistant.supported_languages)
            self.assertIn('javascript', assistant.supported_languages)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('app.openai')
    def test_initialization_with_api_key(self, mock_openai):
        """Test assistant initialization with OpenAI API key"""
        assistant = AICodeAssistant()
        self.assertTrue(assistant.ai_enabled)
        self.assertEqual(mock_openai.api_key, 'test-key')
    
    def test_generate_code_demo_mode(self):
        """Test code generation in demo mode"""
        request = CodeRequest(
            task_type=TaskType.CODE_GENERATION,
            language="python",
            prompt="Create a hello world function"
        )
        
        response = self.assistant.generate_code(request)
        
        self.assertIsInstance(response, CodeResponse)
        self.assertEqual(response.task_type, TaskType.CODE_GENERATION)
        self.assertEqual(response.language, "python")
        self.assertIn("def", response.result)
        self.assertGreater(len(response.suggestions), 0)
        self.assertEqual(response.confidence, 0.5)
    
    def test_generate_code_javascript(self):
        """Test JavaScript code generation in demo mode"""
        request = CodeRequest(
            task_type=TaskType.CODE_GENERATION,
            language="javascript",
            prompt="Create a hello world function"
        )
        
        response = self.assistant.generate_code(request)
        
        self.assertEqual(response.language, "javascript")
        self.assertIn("function", response.result)
    
    def test_generate_code_other_language(self):
        """Test code generation for other languages"""
        request = CodeRequest(
            task_type=TaskType.CODE_GENERATION,
            language="java",
            prompt="Create a hello world function"
        )
        
        response = self.assistant.generate_code(request)
        
        self.assertEqual(response.language, "java")
        self.assertIn("java", response.result.lower())
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('app.openai.ChatCompletion.create')
    def test_generate_code_with_openai(self, mock_openai):
        """Test code generation with OpenAI API"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "def hello_world():\n    print('Hello, World!')"
        mock_openai.return_value = mock_response
        
        assistant = AICodeAssistant()
        request = CodeRequest(
            task_type=TaskType.CODE_GENERATION,
            language="python",
            prompt="Create a hello world function"
        )
        
        response = assistant.generate_code(request)
        
        self.assertEqual(response.result, "def hello_world():\n    print('Hello, World!')")
        self.assertEqual(response.confidence, 0.9)
        mock_openai.assert_called_once()
    
    def test_complete_code_demo_mode(self):
        """Test code completion in demo mode"""
        request = CodeRequest(
            task_type=TaskType.CODE_COMPLETION,
            language="python",
            prompt="Complete this function",
            code="def calculate_sum(a, b):"
        )
        
        response = self.assistant.complete_code(request)
        
        self.assertEqual(response.task_type, TaskType.CODE_COMPLETION)
        self.assertIn("def calculate_sum(a, b):", response.result)
        self.assertEqual(response.confidence, 0.5)
    
    def test_detect_bugs_python(self):
        """Test bug detection for Python code"""
        request = CodeRequest(
            task_type=TaskType.BUG_DETECTION,
            language="python",
            prompt="Find bugs",
            code="try:\n    x = int(input())\nexcept:\n    pass"
        )
        
        response = self.assistant.detect_bugs(request)
        
        self.assertEqual(response.task_type, TaskType.BUG_DETECTION)
        self.assertIn("except", response.result.lower())
        self.assertGreater(len(response.suggestions), 0)
    
    def test_detect_bugs_javascript(self):
        """Test bug detection for JavaScript code"""
        request = CodeRequest(
            task_type=TaskType.BUG_DETECTION,
            language="javascript",
            prompt="Find bugs",
            code="if (x == null) { var y = 5; }"
        )
        
        response = self.assistant.detect_bugs(request)
        
        self.assertIn("===", response.result)
        self.assertIn("var", response.result)
    
    def test_detect_bugs_no_issues(self):
        """Test bug detection with clean code"""
        request = CodeRequest(
            task_type=TaskType.BUG_DETECTION,
            language="python",
            prompt="Find bugs",
            code="def add(a, b):\n    return a + b"
        )
        
        response = self.assistant.detect_bugs(request)
        
        self.assertIn("No obvious issues", response.result)
    
    def test_detect_bugs_no_code(self):
        """Test bug detection without code"""
        request = CodeRequest(
            task_type=TaskType.BUG_DETECTION,
            language="python",
            prompt="Find bugs"
        )
        
        with self.assertRaises(ValueError):
            self.assistant.detect_bugs(request)
    
    def test_generate_documentation_demo_mode(self):
        """Test documentation generation in demo mode"""
        request = CodeRequest(
            task_type=TaskType.DOCUMENTATION,
            language="python",
            prompt="Generate docs",
            code="def add(a, b):\n    return a + b"
        )
        
        response = self.assistant.generate_documentation(request)
        
        self.assertEqual(response.task_type, TaskType.DOCUMENTATION)
        self.assertIn("Documentation", response.result)
        self.assertEqual(response.confidence, 0.5)
    
    def test_generate_documentation_no_code(self):
        """Test documentation generation without code"""
        request = CodeRequest(
            task_type=TaskType.DOCUMENTATION,
            language="python",
            prompt="Generate docs"
        )
        
        with self.assertRaises(ValueError):
            self.assistant.generate_documentation(request)

class TestFlaskAPI(unittest.TestCase):
    """Test cases for Flask API endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_index_endpoint(self):
        """Test the index endpoint"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.content_type)
    
    def test_status_endpoint(self):
        """Test the status endpoint"""
        response = self.app.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['version'], '1.0.0')
        self.assertIn('ai_enabled', data)
        self.assertIn('supported_languages', data)
        self.assertEqual(data['author'], 'Gabriel Demetrios Lafis')
    
    def test_generate_endpoint_valid_request(self):
        """Test generate endpoint with valid request"""
        payload = {
            'prompt': 'Create a hello world function',
            'language': 'python',
            'context': 'Test context'
        }
        
        response = self.app.post('/api/generate',
                               data=json.dumps(payload),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['task_type'], 'code_generation')
        self.assertEqual(data['language'], 'python')
        self.assertIn('result', data)
        self.assertIn('suggestions', data)
        self.assertIn('confidence', data)
    
    def test_generate_endpoint_missing_fields(self):
        """Test generate endpoint with missing fields"""
        payload = {'prompt': 'Create a function'}  # Missing language
        
        response = self.app.post('/api/generate',
                               data=json.dumps(payload),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('error', data)
    
    def test_complete_endpoint_valid_request(self):
        """Test complete endpoint with valid request"""
        payload = {
            'code': 'def hello():',
            'language': 'python',
            'prompt': 'Complete this function'
        }
        
        response = self.app.post('/api/complete',
                               data=json.dumps(payload),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['task_type'], 'code_completion')
    
    def test_detect_bugs_endpoint_valid_request(self):
        """Test detect-bugs endpoint with valid request"""
        payload = {
            'code': 'try:\n    x = int(input())\nexcept:\n    pass',
            'language': 'python'
        }
        
        response = self.app.post('/api/detect-bugs',
                               data=json.dumps(payload),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['task_type'], 'bug_detection')
    
    def test_document_endpoint_valid_request(self):
        """Test document endpoint with valid request"""
        payload = {
            'code': 'def add(a, b):\n    return a + b',
            'language': 'python'
        }
        
        response = self.app.post('/api/document',
                               data=json.dumps(payload),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['task_type'], 'documentation')
    
    def test_404_error_handler(self):
        """Test 404 error handler"""
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('available_endpoints', data)

class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_full_code_generation_workflow(self):
        """Test complete code generation workflow"""
        payload = {
            'prompt': 'Create a function that calculates the factorial of a number',
            'language': 'python',
            'context': 'Mathematical function for educational purposes'
        }
        
        response = self.app.post('/api/generate',
                               data=json.dumps(payload),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('def', data['result'])
        self.assertIsInstance(data['suggestions'], list)
        self.assertGreater(data['confidence'], 0)
    
    def test_full_bug_detection_workflow(self):
        """Test complete bug detection workflow"""
        payload = {
            'code': '''
def divide(a, b):
    return a / b

def process_input():
    try:
        x = int(input("Enter a number: "))
        y = int(input("Enter another number: "))
        result = divide(x, y)
        print(f"Result: {result}")
    except:
        print("An error occurred")
            ''',
            'language': 'python'
        }
        
        response = self.app.post('/api/detect-bugs',
                               data=json.dumps(payload),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        # Should detect the bare except clause
        self.assertIn('except', data['result'].lower())

class TestPerformance(unittest.TestCase):
    """Performance tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_api_response_time(self):
        """Test API response time"""
        import time
        
        payload = {
            'prompt': 'Create a simple function',
            'language': 'python'
        }
        
        start_time = time.time()
        
        response = self.app.post('/api/generate',
                               data=json.dumps(payload),
                               content_type='application/json')
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        # Response should be fast (less than 5 seconds in demo mode)
        self.assertLess(response_time, 5.0)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestTaskType))
    test_suite.addTest(unittest.makeSuite(TestCodeRequest))
    test_suite.addTest(unittest.makeSuite(TestCodeResponse))
    test_suite.addTest(unittest.makeSuite(TestAICodeAssistant))
    test_suite.addTest(unittest.makeSuite(TestFlaskAPI))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    test_suite.addTest(unittest.makeSuite(TestPerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
