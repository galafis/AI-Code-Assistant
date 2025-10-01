#!/usr/bin/env python3
"""
AI Code Assistant
Intelligent code assistance and generation system
Author: Gabriel Demetrios Lafis
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from flask import Flask, request, jsonify, render_template_string
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Types of AI assistance tasks"""
    CODE_GENERATION = "code_generation"
    CODE_COMPLETION = "code_completion"
    BUG_DETECTION = "bug_detection"
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"
    OPTIMIZATION = "optimization"

@dataclass
class CodeRequest:
    """Code assistance request model"""
    task_type: TaskType
    language: str
    prompt: str
    code: Optional[str] = None
    context: Optional[str] = None

@dataclass
class CodeResponse:
    """Code assistance response model"""
    task_type: TaskType
    language: str
    result: str
    suggestions: List[str]
    confidence: float
    timestamp: datetime

class AICodeAssistant:
    """Main AI Code Assistant class"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
            self.ai_enabled = True
            logger.info("OpenAI API initialized successfully")
        else:
            self.ai_enabled = False
            logger.warning("OpenAI API key not found. Running in demo mode.")
        
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'sql', 'html', 'css'
        ]
    
    def generate_code(self, request: CodeRequest) -> CodeResponse:
        """Generate code based on natural language description"""
        if self.ai_enabled:
            try:
                prompt = f"""
                Generate {request.language} code for the following task:
                {request.prompt}
                
                Requirements:
                - Write clean, well-commented code
                - Follow best practices for {request.language}
                - Include error handling where appropriate
                - Make the code production-ready
                
                Context: {request.context or 'None provided'}
                """
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert software developer. Generate high-quality, production-ready code."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                
                result = response.choices[0].message.content
                suggestions = [
                    "Consider adding unit tests for this code",
                    "Review error handling and edge cases",
                    "Optimize for performance if needed"
                ]
                confidence = 0.9
                
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                result = self._generate_demo_code(request)
                suggestions = ["This is a demo response. Configure OpenAI API for full functionality."]
                confidence = 0.5
        else:
            result = self._generate_demo_code(request)
            suggestions = ["This is a demo response. Configure OpenAI API for full functionality."]
            confidence = 0.5
        
        return CodeResponse(
            task_type=request.task_type,
            language=request.language,
            result=result,
            suggestions=suggestions,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def complete_code(self, request: CodeRequest) -> CodeResponse:
        """Complete partial code"""
        if self.ai_enabled and request.code:
            try:
                prompt = f"""
                Complete the following {request.language} code:
                
                {request.code}
                
                Instructions: {request.prompt}
                Context: {request.context or 'None provided'}
                
                Provide the completed code with proper formatting and comments.
                """
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert programmer. Complete the code following best practices."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.2
                )
                
                result = response.choices[0].message.content
                suggestions = [
                    "Review the completed code for correctness",
                    "Test the functionality thoroughly",
                    "Consider refactoring for better readability"
                ]
                confidence = 0.85
                
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                result = self._generate_demo_completion(request)
                suggestions = ["This is a demo response. Configure OpenAI API for full functionality."]
                confidence = 0.5
        else:
            result = self._generate_demo_completion(request)
            suggestions = ["This is a demo response. Configure OpenAI API for full functionality."]
            confidence = 0.5
        
        return CodeResponse(
            task_type=request.task_type,
            language=request.language,
            result=result,
            suggestions=suggestions,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def detect_bugs(self, request: CodeRequest) -> CodeResponse:
        """Detect potential bugs in code"""
        if not request.code:
            raise ValueError("Code is required for bug detection")
        
        # Simple static analysis for demo
        bugs_found = []
        suggestions = []
        
        if request.language.lower() == 'python':
            if 'except:' in request.code:
                bugs_found.append("Bare except clause detected - should catch specific exceptions")
            if 'eval(' in request.code:
                bugs_found.append("Use of eval() detected - potential security risk")
            if 'input(' in request.code and 'int(' in request.code:
                bugs_found.append("Potential ValueError if non-numeric input provided")
        
        if request.language.lower() == 'javascript':
            if '==' in request.code and '===' not in request.code:
                bugs_found.append("Use === instead of == for strict equality")
            if 'var ' in request.code:
                bugs_found.append("Consider using 'let' or 'const' instead of 'var'")
        
        if bugs_found:
            result = "Potential issues found:\n" + "\n".join(f"- {bug}" for bug in bugs_found)
            suggestions = [
                "Fix the identified issues",
                "Add proper error handling",
                "Consider using a linter for additional checks"
            ]
        else:
            result = "No obvious issues detected. Code looks good!"
            suggestions = [
                "Consider adding unit tests",
                "Review for edge cases",
                "Use a comprehensive linter for thorough analysis"
            ]
        
        return CodeResponse(
            task_type=request.task_type,
            language=request.language,
            result=result,
            suggestions=suggestions,
            confidence=0.7,
            timestamp=datetime.now()
        )
    
    def generate_documentation(self, request: CodeRequest) -> CodeResponse:
        """Generate documentation for code"""
        if not request.code:
            raise ValueError("Code is required for documentation generation")
        
        if self.ai_enabled:
            try:
                prompt = f"""
                Generate comprehensive documentation for the following {request.language} code:
                
                {request.code}
                
                Include:
                - Function/class descriptions
                - Parameter explanations
                - Return value descriptions
                - Usage examples
                - Any important notes or warnings
                """
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a technical writer. Generate clear, comprehensive documentation."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1200,
                    temperature=0.3
                )
                
                result = response.choices[0].message.content
                confidence = 0.9
                
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                result = self._generate_demo_documentation(request)
                confidence = 0.5
        else:
            result = self._generate_demo_documentation(request)
            confidence = 0.5
        
        suggestions = [
            "Review the generated documentation for accuracy",
            "Add code examples if not included",
            "Keep documentation updated with code changes"
        ]
        
        return CodeResponse(
            task_type=request.task_type,
            language=request.language,
            result=result,
            suggestions=suggestions,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def _generate_demo_code(self, request: CodeRequest) -> str:
        """Generate demo code for when AI is not available"""
        if request.language.lower() == 'python':
            return f'''# Generated Python code for: {request.prompt}

def example_function():
    """
    This is a demo function created by Gabriel Demetrios Lafis.
    Configure OpenAI API for full AI-powered code generation.
    """
    print("Hello from AI Code Assistant!")
    return "Demo result"

if __name__ == "__main__":
    result = example_function()
    print(f"Result: {{result}}")'''
        
        elif request.language.lower() == 'javascript':
            return f'''// Generated JavaScript code for: {request.prompt}

function exampleFunction() {{
    /**
     * This is a demo function created by Gabriel Demetrios Lafis.
     * Configure OpenAI API for full AI-powered code generation.
     */
    console.log("Hello from AI Code Assistant!");
    return "Demo result";
}}

// Usage example
const result = exampleFunction();
console.log(`Result: ${{result}}`);'''
        
        else:
            return f"// Demo code for {request.language}\n// Task: {request.prompt}\n// Configure OpenAI API for full functionality"
    
    def _generate_demo_completion(self, request: CodeRequest) -> str:
        """Generate demo code completion"""
        return f"{request.code}\n\n// Code completion demo\n// Configure OpenAI API for intelligent code completion"
    
    def _generate_demo_documentation(self, request: CodeRequest) -> str:
        """Generate demo documentation"""
        return f"""# Code Documentation

## Overview
This is demo documentation created by Gabriel Demetrios Lafis.

## Code Analysis
The provided {request.language} code has been analyzed.

## Recommendations
- Configure OpenAI API for comprehensive documentation generation
- Add proper comments and docstrings
- Include usage examples

## Note
This is a demonstration. Configure OpenAI API key for full AI-powered documentation generation.
"""

# Initialize the AI assistant
assistant = AICodeAssistant()

# Flask application
app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Code Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .feature-card {
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        .feature-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .api-section {
            background: rgba(0, 0, 0, 0.2);
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        
        .endpoint {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
        }
        
        .method {
            color: #4CAF50;
            font-weight: bold;
        }
        
        .url {
            color: #FFC107;
        }
        
        .status {
            text-align: center;
            margin-top: 20px;
            padding: 15px;
            background: rgba(76, 175, 80, 0.2);
            border-radius: 8px;
        }
        
        .author {
            text-align: center;
            margin-top: 30px;
            font-style: italic;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Code Assistant</h1>
        
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">💡</div>
                <h3>Code Generation</h3>
                <p>Generate code from natural language descriptions</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🔧</div>
                <h3>Code Completion</h3>
                <p>Intelligent code completion and suggestions</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🐛</div>
                <h3>Bug Detection</h3>
                <p>Identify potential issues and bugs in your code</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">📚</div>
                <h3>Documentation</h3>
                <p>Auto-generate comprehensive code documentation</p>
            </div>
        </div>
        
        <div class="api-section">
            <h2>🚀 API Endpoints</h2>
            
            <div class="endpoint">
                <span class="method">POST</span> <span class="url">/api/generate</span><br>
                Generate code from natural language description
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span> <span class="url">/api/complete</span><br>
                Complete partial code with intelligent suggestions
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span> <span class="url">/api/detect-bugs</span><br>
                Analyze code for potential bugs and issues
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span> <span class="url">/api/document</span><br>
                Generate documentation for existing code
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <span class="url">/api/status</span><br>
                Check system status and capabilities
            </div>
        </div>
        
        <div class="status">
            <h3>System Status</h3>
            <p><strong>Status:</strong> <span style="color: #4CAF50;">Active</span></p>
            <p><strong>AI Engine:</strong> {{ 'OpenAI GPT' if ai_enabled else 'Demo Mode' }}</p>
            <p><strong>Supported Languages:</strong> Python, JavaScript, TypeScript, Java, C++, and more</p>
        </div>
        
        <div class="author">
            <p>Developed by Gabriel Demetrios Lafis</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the web interface"""
    return render_template_string(HTML_TEMPLATE, ai_enabled=assistant.ai_enabled)

@app.route('/api/generate', methods=['POST'])
def generate_code():
    """Generate code from natural language description"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data or 'language' not in data:
            return jsonify({
                'error': 'Missing required fields: prompt, language',
                'status': 'error'
            }), 400
        
        code_request = CodeRequest(
            task_type=TaskType.CODE_GENERATION,
            language=data['language'],
            prompt=data['prompt'],
            context=data.get('context')
        )
        
        response = assistant.generate_code(code_request)
        
        return jsonify({
            'status': 'success',
            'task_type': response.task_type.value,
            'language': response.language,
            'result': response.result,
            'suggestions': response.suggestions,
            'confidence': response.confidence,
            'timestamp': response.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Code generation error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/complete', methods=['POST'])
def complete_code():
    """Complete partial code"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data or 'language' not in data:
            return jsonify({
                'error': 'Missing required fields: code, language',
                'status': 'error'
            }), 400
        
        code_request = CodeRequest(
            task_type=TaskType.CODE_COMPLETION,
            language=data['language'],
            prompt=data.get('prompt', 'Complete this code'),
            code=data['code'],
            context=data.get('context')
        )
        
        response = assistant.complete_code(code_request)
        
        return jsonify({
            'status': 'success',
            'task_type': response.task_type.value,
            'language': response.language,
            'result': response.result,
            'suggestions': response.suggestions,
            'confidence': response.confidence,
            'timestamp': response.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Code completion error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/detect-bugs', methods=['POST'])
def detect_bugs():
    """Detect bugs in code"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data or 'language' not in data:
            return jsonify({
                'error': 'Missing required fields: code, language',
                'status': 'error'
            }), 400
        
        code_request = CodeRequest(
            task_type=TaskType.BUG_DETECTION,
            language=data['language'],
            prompt='Detect bugs in this code',
            code=data['code']
        )
        
        response = assistant.detect_bugs(code_request)
        
        return jsonify({
            'status': 'success',
            'task_type': response.task_type.value,
            'language': response.language,
            'result': response.result,
            'suggestions': response.suggestions,
            'confidence': response.confidence,
            'timestamp': response.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Bug detection error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/document', methods=['POST'])
def document_code():
    """Generate documentation for code"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data or 'language' not in data:
            return jsonify({
                'error': 'Missing required fields: code, language',
                'status': 'error'
            }), 400
        
        code_request = CodeRequest(
            task_type=TaskType.DOCUMENTATION,
            language=data['language'],
            prompt='Generate documentation for this code',
            code=data['code']
        )
        
        response = assistant.generate_documentation(code_request)
        
        return jsonify({
            'status': 'success',
            'task_type': response.task_type.value,
            'language': response.language,
            'result': response.result,
            'suggestions': response.suggestions,
            'confidence': response.confidence,
            'timestamp': response.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Documentation generation error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/status')
def status():
    """API status endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'ai_enabled': assistant.ai_enabled,
        'supported_languages': assistant.supported_languages,
        'features': [
            'Code Generation',
            'Code Completion',
            'Bug Detection',
            'Documentation Generation'
        ],
        'author': 'Gabriel Demetrios Lafis',
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error',
        'available_endpoints': [
            '/api/generate',
            '/api/complete',
            '/api/detect-bugs',
            '/api/document',
            '/api/status'
        ]
    }), 404

if __name__ == '__main__':
    logger.info("Starting AI Code Assistant")
    logger.info("Author: Gabriel Demetrios Lafis")
    app.run(debug=True, host='0.0.0.0', port=5000)
