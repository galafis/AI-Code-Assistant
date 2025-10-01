#!/usr/bin/env python3
"""
Advanced Code Assistant
Intelligent code generation, analysis, and collaboration platform
Author: Gabriel Demetrios Lafis
"""

import os
import json
import time
import logging
import asyncio
import hashlib
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
from pathlib import Path
import tempfile
import shutil

from flask import Flask, request, jsonify, render_template_string, send_file, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import openai
import ast
import radon.complexity as radon_cc
import radon.metrics as radon_metrics
from pylint import lint
from pylint.reporters.text import TextReporter
import bandit
from bandit.core import manager as bandit_manager
import autopep8
import black
import isort
from jinja2 import Template
import markdown
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import git
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LanguageType(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    R = "r"
    SQL = "sql"
    HTML = "html"
    CSS = "css"

class AnalysisType(Enum):
    """Types of code analysis"""
    COMPLEXITY = "complexity"
    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    DOCUMENTATION = "documentation"

class TaskType(Enum):
    """Types of AI tasks"""
    CODE_GENERATION = "code_generation"
    CODE_COMPLETION = "code_completion"
    CODE_REVIEW = "code_review"
    BUG_DETECTION = "bug_detection"
    REFACTORING = "refactoring"
    TEST_GENERATION = "test_generation"
    DOCUMENTATION = "documentation"
    EXPLANATION = "explanation"

@dataclass
class CodeAnalysisResult:
    """Code analysis result"""
    file_path: str
    language: LanguageType
    analysis_type: AnalysisType
    score: float
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    metrics: Dict[str, Any]
    timestamp: datetime

@dataclass
class AIResponse:
    """AI assistant response"""
    task_type: TaskType
    input_code: str
    output_code: str
    explanation: str
    confidence: float
    language: LanguageType
    processing_time: float
    suggestions: List[str]
    timestamp: datetime

@dataclass
class CollaborationSession:
    """Real-time collaboration session"""
    session_id: str
    participants: List[str]
    code_content: str
    language: LanguageType
    created_at: datetime
    last_modified: datetime
    is_active: bool

class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path: str = "code_assistant.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    language TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    score REAL NOT NULL,
                    issues TEXT NOT NULL,
                    suggestions TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create AI responses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    input_code TEXT NOT NULL,
                    output_code TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    language TEXT NOT NULL,
                    processing_time REAL NOT NULL,
                    suggestions TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create collaboration sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collaboration_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    participants TEXT NOT NULL,
                    code_content TEXT NOT NULL,
                    language TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_modified TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create code templates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS code_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    language TEXT NOT NULL,
                    template_code TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def save_analysis_result(self, result: CodeAnalysisResult) -> int:
        """Save analysis result to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analysis_results 
                (file_path, language, analysis_type, score, issues, suggestions, metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result.file_path,
                result.language.value,
                result.analysis_type.value,
                result.score,
                json.dumps(result.issues),
                json.dumps(result.suggestions),
                json.dumps(result.metrics)
            ))
            result_id = cursor.lastrowid
            conn.commit()
            return result_id
    
    def save_ai_response(self, response: AIResponse) -> int:
        """Save AI response to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_responses 
                (task_type, input_code, output_code, explanation, confidence, 
                 language, processing_time, suggestions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                response.task_type.value,
                response.input_code,
                response.output_code,
                response.explanation,
                response.confidence,
                response.language.value,
                response.processing_time,
                json.dumps(response.suggestions)
            ))
            response_id = cursor.lastrowid
            conn.commit()
            return response_id

class CodeAnalyzer:
    """Advanced code analysis engine"""
    
    def __init__(self):
        self.supported_languages = {
            LanguageType.PYTHON: ['.py'],
            LanguageType.JAVASCRIPT: ['.js', '.jsx'],
            LanguageType.TYPESCRIPT: ['.ts', '.tsx'],
            LanguageType.JAVA: ['.java'],
            LanguageType.CPP: ['.cpp', '.cc', '.cxx', '.c++'],
            LanguageType.CSHARP: ['.cs'],
            LanguageType.GO: ['.go'],
            LanguageType.RUST: ['.rs'],
            LanguageType.PHP: ['.php'],
            LanguageType.RUBY: ['.rb'],
            LanguageType.HTML: ['.html', '.htm'],
            LanguageType.CSS: ['.css'],
            LanguageType.SQL: ['.sql']
        }
    
    def detect_language(self, file_path: str) -> Optional[LanguageType]:
        """Detect programming language from file extension"""
        file_ext = Path(file_path).suffix.lower()
        
        for language, extensions in self.supported_languages.items():
            if file_ext in extensions:
                return language
        
        return None
    
    def analyze_complexity(self, code: str, language: LanguageType) -> CodeAnalysisResult:
        """Analyze code complexity"""
        if language != LanguageType.PYTHON:
            # For non-Python languages, provide basic analysis
            return self._basic_complexity_analysis(code, language)
        
        try:
            # Parse Python code
            tree = ast.parse(code)
            
            # Calculate complexity metrics
            complexity_visitor = radon_cc.ComplexityVisitor.from_code(code)
            complexity_blocks = complexity_visitor.blocks
            
            # Calculate metrics
            raw_metrics = radon_metrics.analyze(code)
            
            issues = []
            suggestions = []
            total_complexity = 0
            
            for block in complexity_blocks:
                total_complexity += block.complexity
                if block.complexity > 10:
                    issues.append({
                        'type': 'high_complexity',
                        'line': block.lineno,
                        'function': block.name,
                        'complexity': block.complexity,
                        'severity': 'high' if block.complexity > 15 else 'medium'
                    })
                    suggestions.append(f"Consider refactoring {block.name} (complexity: {block.complexity})")
            
            # Calculate overall score (0-100)
            avg_complexity = total_complexity / len(complexity_blocks) if complexity_blocks else 0
            score = max(0, 100 - (avg_complexity * 5))
            
            metrics = {
                'total_complexity': total_complexity,
                'average_complexity': avg_complexity,
                'functions_count': len(complexity_blocks),
                'lines_of_code': raw_metrics.loc,
                'logical_lines': raw_metrics.lloc,
                'source_lines': raw_metrics.sloc,
                'comments': raw_metrics.comments,
                'multi_line_strings': raw_metrics.multi,
                'blank_lines': raw_metrics.blank
            }
            
            return CodeAnalysisResult(
                file_path="<string>",
                language=language,
                analysis_type=AnalysisType.COMPLEXITY,
                score=score,
                issues=issues,
                suggestions=suggestions,
                metrics=metrics,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Complexity analysis error: {str(e)}")
            return self._basic_complexity_analysis(code, language)
    
    def analyze_security(self, code: str, language: LanguageType) -> CodeAnalysisResult:
        """Analyze code security"""
        if language != LanguageType.PYTHON:
            return self._basic_security_analysis(code, language)
        
        try:
            # Create temporary file for bandit analysis
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                # Run bandit security analysis
                b_mgr = bandit_manager.BanditManager(bandit.config.BanditConfig(), 'file')
                b_mgr.discover_files([temp_file_path])
                b_mgr.run_tests()
                
                issues = []
                suggestions = []
                
                for issue in b_mgr.get_issue_list():
                    issues.append({
                        'type': 'security_issue',
                        'line': issue.lineno,
                        'test_id': issue.test_id,
                        'severity': issue.severity,
                        'confidence': issue.confidence,
                        'text': issue.text
                    })
                    suggestions.append(f"Security issue at line {issue.lineno}: {issue.text}")
                
                # Calculate score based on severity
                high_severity = len([i for i in issues if i['severity'] == 'HIGH'])
                medium_severity = len([i for i in issues if i['severity'] == 'MEDIUM'])
                low_severity = len([i for i in issues if i['severity'] == 'LOW'])
                
                score = max(0, 100 - (high_severity * 20 + medium_severity * 10 + low_severity * 5))
                
                metrics = {
                    'total_issues': len(issues),
                    'high_severity': high_severity,
                    'medium_severity': medium_severity,
                    'low_severity': low_severity,
                    'lines_analyzed': len(code.split('\n'))
                }
                
                return CodeAnalysisResult(
                    file_path="<string>",
                    language=language,
                    analysis_type=AnalysisType.SECURITY,
                    score=score,
                    issues=issues,
                    suggestions=suggestions,
                    metrics=metrics,
                    timestamp=datetime.now()
                )
                
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Security analysis error: {str(e)}")
            return self._basic_security_analysis(code, language)
    
    def analyze_style(self, code: str, language: LanguageType) -> CodeAnalysisResult:
        """Analyze code style"""
        if language != LanguageType.PYTHON:
            return self._basic_style_analysis(code, language)
        
        try:
            # Create temporary file for pylint analysis
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                # Run pylint analysis
                from io import StringIO
                pylint_output = StringIO()
                reporter = TextReporter(pylint_output)
                
                lint.Run([temp_file_path], reporter=reporter, exit=False)
                pylint_result = pylint_output.getvalue()
                
                # Parse pylint output
                issues = []
                suggestions = []
                
                for line in pylint_result.split('\n'):
                    if ':' in line and ('error' in line.lower() or 'warning' in line.lower() or 'convention' in line.lower()):
                        parts = line.split(':')
                        if len(parts) >= 4:
                            line_num = parts[1].strip()
                            message = ':'.join(parts[3:]).strip()
                            
                            issues.append({
                                'type': 'style_issue',
                                'line': line_num,
                                'message': message,
                                'severity': 'medium'
                            })
                            suggestions.append(f"Line {line_num}: {message}")
                
                # Calculate score
                score = max(0, 100 - len(issues) * 2)
                
                metrics = {
                    'total_issues': len(issues),
                    'lines_analyzed': len(code.split('\n')),
                    'pylint_score': score
                }
                
                return CodeAnalysisResult(
                    file_path="<string>",
                    language=language,
                    analysis_type=AnalysisType.STYLE,
                    score=score,
                    issues=issues,
                    suggestions=suggestions,
                    metrics=metrics,
                    timestamp=datetime.now()
                )
                
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Style analysis error: {str(e)}")
            return self._basic_style_analysis(code, language)
    
    def _basic_complexity_analysis(self, code: str, language: LanguageType) -> CodeAnalysisResult:
        """Basic complexity analysis for non-Python languages"""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Simple heuristics
        complexity_indicators = ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch']
        complexity_count = sum(1 for line in non_empty_lines 
                              for indicator in complexity_indicators 
                              if indicator in line.lower())
        
        score = max(0, 100 - complexity_count * 2)
        
        return CodeAnalysisResult(
            file_path="<string>",
            language=language,
            analysis_type=AnalysisType.COMPLEXITY,
            score=score,
            issues=[],
            suggestions=[f"Consider simplifying complex logic (found {complexity_count} complexity indicators)"] if complexity_count > 10 else [],
            metrics={'complexity_indicators': complexity_count, 'lines_of_code': len(non_empty_lines)},
            timestamp=datetime.now()
        )
    
    def _basic_security_analysis(self, code: str, language: LanguageType) -> CodeAnalysisResult:
        """Basic security analysis for non-Python languages"""
        security_issues = []
        suggestions = []
        
        # Common security patterns
        security_patterns = {
            'sql_injection': ['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
            'xss': ['innerHTML', 'document.write', 'eval'],
            'hardcoded_secrets': ['password', 'api_key', 'secret', 'token'],
            'unsafe_functions': ['exec', 'system', 'shell_exec']
        }
        
        for issue_type, patterns in security_patterns.items():
            for pattern in patterns:
                if pattern.lower() in code.lower():
                    security_issues.append({
                        'type': issue_type,
                        'pattern': pattern,
                        'severity': 'medium'
                    })
                    suggestions.append(f"Potential {issue_type.replace('_', ' ')} risk with '{pattern}'")
        
        score = max(0, 100 - len(security_issues) * 10)
        
        return CodeAnalysisResult(
            file_path="<string>",
            language=language,
            analysis_type=AnalysisType.SECURITY,
            score=score,
            issues=security_issues,
            suggestions=suggestions,
            metrics={'potential_issues': len(security_issues)},
            timestamp=datetime.now()
        )
    
    def _basic_style_analysis(self, code: str, language: LanguageType) -> CodeAnalysisResult:
        """Basic style analysis for non-Python languages"""
        lines = code.split('\n')
        issues = []
        suggestions = []
        
        # Basic style checks
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append({
                    'type': 'line_too_long',
                    'line': i,
                    'length': len(line),
                    'severity': 'low'
                })
                suggestions.append(f"Line {i} is too long ({len(line)} characters)")
            
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                # Check for consistent indentation (basic)
                pass
        
        score = max(0, 100 - len(issues) * 5)
        
        return CodeAnalysisResult(
            file_path="<string>",
            language=language,
            analysis_type=AnalysisType.STYLE,
            score=score,
            issues=issues,
            suggestions=suggestions,
            metrics={'style_issues': len(issues)},
            timestamp=datetime.now()
        )

class CodeAssistant(CodeAnalyzer):
    """Advanced Intelligent code assistant"""
    
    def __init__(self):
        self.openai_client = None
        self.db_manager = DatabaseManager()
        self.code_analyzer = CodeAnalyzer()
        self.collaboration_sessions = {}
        
        # Initialize OpenAI client if API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            openai.api_key = api_key
            self.openai_client = openai
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OpenAI API key not found, using demo mode")
    
    async def generate_code(self, prompt: str, language: LanguageType, context: str = "") -> AIResponse:
        """Generate code based on prompt"""
        start_time = time.time()
        
        if self.openai_client:
            try:
                response = await self._call_openai_api(
                    task_type=TaskType.CODE_GENERATION,
                    prompt=prompt,
                    language=language,
                    context=context
                )
                processing_time = time.time() - start_time
                
                ai_response = AIResponse(
                    task_type=TaskType.CODE_GENERATION,
                    input_code=context,
                    output_code=response['code'],
                    explanation=response['explanation'],
                    confidence=response['confidence'],
                    language=language,
                    processing_time=processing_time,
                    suggestions=response['suggestions'],
                    timestamp=datetime.now()
                )
                
                self.db_manager.save_ai_response(ai_response)
                return ai_response
                
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                return self._generate_demo_response(prompt, language, TaskType.CODE_GENERATION)
        else:
            return self._generate_demo_response(prompt, language, TaskType.CODE_GENERATION)
    
    async def complete_code(self, partial_code: str, language: LanguageType) -> AIResponse:
        """Complete partial code"""
        start_time = time.time()
        
        if self.openai_client:
            try:
                response = await self._call_openai_api(
                    task_type=TaskType.CODE_COMPLETION,
                    prompt=f"Complete this {language.value} code:",
                    language=language,
                    context=partial_code
                )
                processing_time = time.time() - start_time
                
                ai_response = AIResponse(
                    task_type=TaskType.CODE_COMPLETION,
                    input_code=partial_code,
                    output_code=response['code'],
                    explanation=response['explanation'],
                    confidence=response['confidence'],
                    language=language,
                    processing_time=processing_time,
                    suggestions=response['suggestions'],
                    timestamp=datetime.now()
                )
                
                self.db_manager.save_ai_response(ai_response)
                return ai_response
                
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                return self._generate_demo_response(partial_code, language, TaskType.CODE_COMPLETION)
        else:
            return self._generate_demo_response(partial_code, language, TaskType.CODE_COMPLETION)
    
    async def review_code(self, code: str, language: LanguageType) -> AIResponse:
        """Review code and provide suggestions"""
        start_time = time.time()
        
        # Perform automated analysis first
        complexity_result = self.code_analyzer.analyze_complexity(code, language)
        security_result = self.code_analyzer.analyze_security(code, language)
        style_result = self.code_analyzer.analyze_style(code, language)
        
        if self.openai_client:
            try:
                analysis_summary = f"""
                Complexity Score: {complexity_result.score:.1f}/100
                Security Score: {security_result.score:.1f}/100
                Style Score: {style_result.score:.1f}/100
                
                Issues found:
                - Complexity: {len(complexity_result.issues)} issues
                - Security: {len(security_result.issues)} issues
                - Style: {len(style_result.issues)} issues
                """
                
                response = await self._call_openai_api(
                    task_type=TaskType.CODE_REVIEW,
                    prompt=f"Review this {language.value} code and provide detailed feedback. Automated analysis: {analysis_summary}",
                    language=language,
                    context=code
                )
                processing_time = time.time() - start_time
                
                # Combine AI suggestions with automated analysis
                all_suggestions = response['suggestions'] + complexity_result.suggestions + security_result.suggestions + style_result.suggestions
                
                ai_response = AIResponse(
                    task_type=TaskType.CODE_REVIEW,
                    input_code=code,
                    output_code=response['code'],
                    explanation=response['explanation'],
                    confidence=response['confidence'],
                    language=language,
                    processing_time=processing_time,
                    suggestions=all_suggestions,
                    timestamp=datetime.now()
                )
                
                self.db_manager.save_ai_response(ai_response)
                return ai_response
                
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                return self._generate_demo_review(code, language, complexity_result, security_result, style_result)
        else:
            return self._generate_demo_review(code, language, complexity_result, security_result, style_result)
    
    async def generate_tests(self, code: str, language: LanguageType) -> AIResponse:
        """Generate unit tests for code"""
        start_time = time.time()
        
        if self.openai_client:
            try:
                response = await self._call_openai_api(
                    task_type=TaskType.TEST_GENERATION,
                    prompt=f"Generate comprehensive unit tests for this {language.value} code:",
                    language=language,
                    context=code
                )
                processing_time = time.time() - start_time
                
                ai_response = AIResponse(
                    task_type=TaskType.TEST_GENERATION,
                    input_code=code,
                    output_code=response['code'],
                    explanation=response['explanation'],
                    confidence=response['confidence'],
                    language=language,
                    processing_time=processing_time,
                    suggestions=response['suggestions'],
                    timestamp=datetime.now()
                )
                
                self.db_manager.save_ai_response(ai_response)
                return ai_response
                
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                return self._generate_demo_response(code, language, TaskType.TEST_GENERATION)
        else:
            return self._generate_demo_response(code, language, TaskType.TEST_GENERATION)
    
    async def _call_openai_api(self, task_type: TaskType, prompt: str, language: LanguageType, context: str) -> Dict[str, Any]:
        """Call OpenAI API with proper formatting"""
        system_prompt = f"""
        You are an expert {language.value} developer and code assistant. 
        Task: {task_type.value.replace('_', ' ').title()}
        
        Provide responses in the following JSON format:
        {{
            "code": "generated/modified code here",
            "explanation": "detailed explanation of the code",
            "confidence": 0.95,
            "suggestions": ["suggestion 1", "suggestion 2"]
        }}
        
        Always provide working, production-ready code with proper error handling and documentation.
        """
        
        user_prompt = f"{prompt}\n\nCode context:\n```{language.value}\n{context}\n```"
        
        response = await self.openai_client.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback if response is not valid JSON
            return {
                "code": content,
                "explanation": "AI-generated code",
                "confidence": 0.8,
                "suggestions": ["Review the generated code carefully"]
            }
    
    def _generate_demo_response(self, input_code: str, language: LanguageType, task_type: TaskType) -> AIResponse:
        """Generate demo response when OpenAI is not available"""
        demo_responses = {
            TaskType.CODE_GENERATION: {
                "code": f"# Demo {language.value} code\n# This is a placeholder response\nprint('Hello, World!')",
                "explanation": "This is a demo response. Configure OpenAI API key for real AI assistance.",
                "suggestions": ["Add proper error handling", "Include documentation", "Add unit tests"]
            },
            TaskType.CODE_COMPLETION: {
                "code": input_code + "\n    # Completed code would appear here",
                "explanation": "Code completion demo. Real completion requires OpenAI API key.",
                "suggestions": ["Complete the function implementation", "Add return statement"]
            },
            TaskType.TEST_GENERATION: {
                "code": f"# Demo unit tests for {language.value}\nimport unittest\n\nclass TestDemo(unittest.TestCase):\n    def test_example(self):\n        self.assertTrue(True)",
                "explanation": "Demo test generation. Configure OpenAI for real test generation.",
                "suggestions": ["Add more test cases", "Test edge cases", "Add integration tests"]
            }
        }
        
        demo_data = demo_responses.get(task_type, demo_responses[TaskType.CODE_GENERATION])
        
        return AIResponse(
            task_type=task_type,
            input_code=input_code,
            output_code=demo_data["code"],
            explanation=demo_data["explanation"],
            confidence=0.5,
            language=language,
            processing_time=0.1,
            suggestions=demo_data["suggestions"],
            timestamp=datetime.now()
        )
    
    def _generate_demo_review(self, code: str, language: LanguageType, 
                            complexity_result: CodeAnalysisResult,
                            security_result: CodeAnalysisResult,
                            style_result: CodeAnalysisResult) -> AIResponse:
        """Generate demo code review"""
        review_text = f"""
        Code Review Summary:
        
        Complexity Analysis: {complexity_result.score:.1f}/100
        - {len(complexity_result.issues)} complexity issues found
        
        Security Analysis: {security_result.score:.1f}/100
        - {len(security_result.issues)} security issues found
        
        Style Analysis: {style_result.score:.1f}/100
        - {len(style_result.issues)} style issues found
        
        Overall Assessment: The code shows areas for improvement in complexity and style.
        Consider refactoring complex functions and following coding standards.
        """
        
        all_suggestions = (complexity_result.suggestions + 
                          security_result.suggestions + 
                          style_result.suggestions)
        
        return AIResponse(
            task_type=TaskType.CODE_REVIEW,
            input_code=code,
            output_code=code,  # No modifications in review
            explanation=review_text,
            confidence=0.8,
            language=language,
            processing_time=0.2,
            suggestions=all_suggestions,
            timestamp=datetime.now()
        )
    
    def create_collaboration_session(self, session_id: str, initial_code: str, language: LanguageType) -> CollaborationSession:
        """Create a new collaboration session"""
        session = CollaborationSession(
            session_id=session_id,
            participants=[],
            code_content=initial_code,
            language=language,
            created_at=datetime.now(),
            last_modified=datetime.now(),
            is_active=True
        )
        
        self.collaboration_sessions[session_id] = session
        return session
    
    def join_collaboration_session(self, session_id: str, user_id: str) -> Optional[CollaborationSession]:
        """Join an existing collaboration session"""
        if session_id in self.collaboration_sessions:
            session = self.collaboration_sessions[session_id]
            if user_id not in session.participants:
                session.participants.append(user_id)
            return session
        return None
    
    def update_collaboration_code(self, session_id: str, new_code: str, user_id: str) -> bool:
        """Update code in collaboration session"""
        if session_id in self.collaboration_sessions:
            session = self.collaboration_sessions[session_id]
            session.code_content = new_code
            session.last_modified = datetime.now()
            return True
        return False

# Initialize the AI assistant
ai_assistant = AICodeAssistant()

# Flask application with SocketIO for real-time collaboration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Advanced HTML template with Monaco Editor
ADVANCED_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Code Assistant</title>
    <script src="https://unpkg.com/monaco-editor@0.34.0/min/vs/loader.js"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
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
        }
        
        .header {
            background: rgba(0, 0, 0, 0.2);
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 20px;
            height: calc(100vh - 120px);
        }
        
        .editor-panel {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
            display: flex;
            flex-direction: column;
        }
        
        .sidebar {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
            overflow-y: auto;
        }
        
        .editor-container {
            flex: 1;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 10px;
            overflow: hidden;
            margin-top: 15px;
        }
        
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .btn {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .btn-secondary {
            background: linear-gradient(45deg, #2196F3, #1976D2);
        }
        
        .btn-warning {
            background: linear-gradient(45deg, #FF9800, #F57C00);
        }
        
        .btn-danger {
            background: linear-gradient(45deg, #f44336, #d32f2f);
        }
        
        .input-group {
            margin-bottom: 15px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        
        .input-group select,
        .input-group input,
        .input-group textarea {
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 5px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 14px;
        }
        
        .input-group select option {
            background: #333;
            color: white;
        }
        
        .input-group textarea {
            resize: vertical;
            min-height: 80px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .card h3 {
            margin-bottom: 10px;
            color: #fff;
            border-bottom: 2px solid rgba(255, 255, 255, 0.3);
            padding-bottom: 5px;
        }
        
        .analysis-result {
            margin-bottom: 10px;
        }
        
        .score {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .score.good {
            color: #4CAF50;
        }
        
        .score.medium {
            color: #FF9800;
        }
        
        .score.poor {
            color: #f44336;
        }
        
        .suggestions {
            list-style: none;
            padding: 0;
        }
        
        .suggestions li {
            background: rgba(255, 255, 255, 0.1);
            padding: 8px;
            margin-bottom: 5px;
            border-radius: 5px;
            font-size: 0.9em;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 4px solid #fff;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .collaboration-users {
            display: flex;
            gap: 5px;
            margin-bottom: 10px;
        }
        
        .user-badge {
            background: #4CAF50;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }
        
        .tabs {
            display: flex;
            margin-bottom: 15px;
        }
        
        .tab {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            padding: 10px 15px;
            color: white;
            cursor: pointer;
            border-radius: 5px 5px 0 0;
            margin-right: 2px;
        }
        
        .tab.active {
            background: rgba(255, 255, 255, 0.3);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @media (max-width: 1200px) {
            .container {
                grid-template-columns: 1fr;
                grid-template-rows: 1fr auto;
            }
            
            .sidebar {
                max-height: 400px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Advanced Code Assistant</h1>
        <p>Intelligent code generation, analysis, and collaboration platform</p>
    </div>
    
    <div class="container">
        <!-- Editor Panel -->
        <div class="editor-panel">
            <div class="controls">
                <select id="languageSelect">
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="typescript">TypeScript</option>
                    <option value="java">Java</option>
                    <option value="cpp">C++</option>
                    <option value="csharp">C#</option>
                    <option value="go">Go</option>
                    <option value="rust">Rust</option>
                    <option value="php">PHP</option>
                    <option value="ruby">Ruby</option>
                </select>
                
                <button class="btn" onclick="generateCode()">🎯 Generate Code</button>
                <button class="btn btn-secondary" onclick="completeCode()">✨ Complete Code</button>
                <button class="btn btn-warning" onclick="reviewCode()">🔍 Review Code</button>
                <button class="btn btn-danger" onclick="generateTests()">🧪 Generate Tests</button>
            </div>
            
            <div class="editor-container">
                <div id="editor" style="height: 100%; width: 100%;"></div>
            </div>
        </div>
        
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('ai-assistant')">AI Assistant</button>
                <button class="tab" onclick="switchTab('analysis')">Analysis</button>
                <button class="tab" onclick="switchTab('collaboration')">Collaborate</button>
            </div>
            
            <!-- AI Assistant Tab -->
            <div id="ai-assistant" class="tab-content active">
                <div class="card">
                    <h3>🤖 AI Assistant</h3>
                    <div class="input-group">
                        <label for="aiPrompt">Describe what you want to create:</label>
                        <textarea id="aiPrompt" placeholder="e.g., Create a function to sort a list of dictionaries by a specific key"></textarea>
                    </div>
                    <button class="btn" onclick="generateFromPrompt()">Generate Code</button>
                </div>
                
                <div class="card">
                    <h3>📝 AI Response</h3>
                    <div id="aiResponse">
                        <p>AI responses will appear here...</p>
                    </div>
                </div>
                
                <div class="card">
                    <h3>💡 Suggestions</h3>
                    <ul id="aiSuggestions" class="suggestions">
                        <li>Start by writing some code or describing what you want to create</li>
                    </ul>
                </div>
            </div>
            
            <!-- Analysis Tab -->
            <div id="analysis" class="tab-content">
                <div class="card">
                    <h3>📊 Code Analysis</h3>
                    <button class="btn" onclick="analyzeCode()">Analyze Current Code</button>
                </div>
                
                <div class="card">
                    <h3>🔧 Complexity</h3>
                    <div id="complexityResult" class="analysis-result">
                        <div class="score" id="complexityScore">-</div>
                        <div>Click analyze to see results</div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🔒 Security</h3>
                    <div id="securityResult" class="analysis-result">
                        <div class="score" id="securityScore">-</div>
                        <div>Click analyze to see results</div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🎨 Style</h3>
                    <div id="styleResult" class="analysis-result">
                        <div class="score" id="styleScore">-</div>
                        <div>Click analyze to see results</div>
                    </div>
                </div>
            </div>
            
            <!-- Collaboration Tab -->
            <div id="collaboration" class="tab-content">
                <div class="card">
                    <h3>👥 Real-time Collaboration</h3>
                    <div class="input-group">
                        <label for="sessionId">Session ID:</label>
                        <input type="text" id="sessionId" placeholder="Enter session ID">
                    </div>
                    <div class="controls">
                        <button class="btn" onclick="createSession()">Create Session</button>
                        <button class="btn btn-secondary" onclick="joinSession()">Join Session</button>
                    </div>
                    
                    <div class="collaboration-users" id="collaborationUsers">
                        <!-- Active users will appear here -->
                    </div>
                </div>
                
                <div class="card">
                    <h3>📈 Session Stats</h3>
                    <div id="sessionStats">
                        <p>No active session</p>
                    </div>
                </div>
            </div>
            
            <!-- Loading indicator -->
            <div class="loading" id="loadingIndicator">
                <div class="spinner"></div>
                <p>Processing...</p>
            </div>
        </div>
    </div>
    
    <script>
        let editor;
        let socket;
        let currentSession = null;
        
        // Initialize Monaco Editor
        require.config({ paths: { 'vs': 'https://unpkg.com/monaco-editor@0.34.0/min/vs' }});
        require(['vs/editor/editor.main'], function () {
            editor = monaco.editor.create(document.getElementById('editor'), {
                value: '# Welcome to Advanced Code Assistant\\n# Start typing or use AI features to generate code\\n\\ndef hello_world():\\n    print("Hello, World!")\\n    return "Hello, World!"\\n\\nif __name__ == "__main__":\\n    hello_world()',
                language: 'python',
                theme: 'vs-dark',
                automaticLayout: true,
                fontSize: 14,
                minimap: { enabled: true },
                scrollBeyondLastLine: false,
                wordWrap: 'on'
            });
            
            // Listen for language changes
            document.getElementById('languageSelect').addEventListener('change', function() {
                const language = this.value;
                monaco.editor.setModelLanguage(editor.getModel(), language);
            });
            
            // Auto-save and collaboration
            editor.onDidChangeModelContent(function() {
                if (currentSession) {
                    socket.emit('code_change', {
                        session_id: currentSession,
                        code: editor.getValue()
                    });
                }
            });
        });
        
        // Initialize Socket.IO for collaboration
        socket = io();
        
        socket.on('code_updated', function(data) {
            if (data.session_id === currentSession) {
                const currentPosition = editor.getPosition();
                editor.setValue(data.code);
                editor.setPosition(currentPosition);
            }
        });
        
        socket.on('user_joined', function(data) {
            updateCollaborationUsers(data.users);
        });
        
        socket.on('user_left', function(data) {
            updateCollaborationUsers(data.users);
        });
        
        function switchTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }
        
        function showLoading() {
            document.getElementById('loadingIndicator').style.display = 'block';
        }
        
        function hideLoading() {
            document.getElementById('loadingIndicator').style.display = 'none';
        }
        
        async function generateCode() {
            const code = editor.getValue();
            const language = document.getElementById('languageSelect').value;
            const prompt = document.getElementById('aiPrompt').value || 'Improve this code';
            
            showLoading();
            
            try {
                const response = await fetch('/api/generate-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        prompt: prompt,
                        language: language,
                        context: code
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    editor.setValue(result.output_code);
                    updateAIResponse(result);
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                hideLoading();
            }
        }
        
        async function completeCode() {
            const code = editor.getValue();
            const language = document.getElementById('languageSelect').value;
            
            showLoading();
            
            try {
                const response = await fetch('/api/complete-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        partial_code: code,
                        language: language
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    editor.setValue(result.output_code);
                    updateAIResponse(result);
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                hideLoading();
            }
        }
        
        async function reviewCode() {
            const code = editor.getValue();
            const language = document.getElementById('languageSelect').value;
            
            showLoading();
            
            try {
                const response = await fetch('/api/review-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        code: code,
                        language: language
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    updateAIResponse(result);
                    switchTab('ai-assistant');
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                hideLoading();
            }
        }
        
        async function generateTests() {
            const code = editor.getValue();
            const language = document.getElementById('languageSelect').value;
            
            showLoading();
            
            try {
                const response = await fetch('/api/generate-tests', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        code: code,
                        language: language
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    // Open tests in a new editor or append to current
                    const currentCode = editor.getValue();
                    const testsCode = result.output_code;
                    editor.setValue(currentCode + '\\n\\n# Generated Tests\\n' + testsCode);
                    updateAIResponse(result);
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                hideLoading();
            }
        }
        
        async function analyzeCode() {
            const code = editor.getValue();
            const language = document.getElementById('languageSelect').value;
            
            showLoading();
            
            try {
                const response = await fetch('/api/analyze-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        code: code,
                        language: language
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    updateAnalysisResults(result.analysis);
                    switchTab('analysis');
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                hideLoading();
            }
        }
        
        function generateFromPrompt() {
            generateCode();
        }
        
        function updateAIResponse(result) {
            const responseDiv = document.getElementById('aiResponse');
            responseDiv.innerHTML = `
                <h4>Task: ${result.task_type.replace('_', ' ').toUpperCase()}</h4>
                <p><strong>Confidence:</strong> ${(result.confidence * 100).toFixed(1)}%</p>
                <p><strong>Processing Time:</strong> ${result.processing_time.toFixed(2)}s</p>
                <div style="margin-top: 10px;">
                    <strong>Explanation:</strong>
                    <p style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-top: 5px;">
                        ${result.explanation}
                    </p>
                </div>
            `;
            
            const suggestionsUl = document.getElementById('aiSuggestions');
            suggestionsUl.innerHTML = '';
            result.suggestions.forEach(suggestion => {
                const li = document.createElement('li');
                li.textContent = suggestion;
                suggestionsUl.appendChild(li);
            });
        }
        
        function updateAnalysisResults(analysis) {
            // Update complexity
            const complexityScore = document.getElementById('complexityScore');
            complexityScore.textContent = analysis.complexity.score.toFixed(1) + '/100';
            complexityScore.className = 'score ' + getScoreClass(analysis.complexity.score);
            
            // Update security
            const securityScore = document.getElementById('securityScore');
            securityScore.textContent = analysis.security.score.toFixed(1) + '/100';
            securityScore.className = 'score ' + getScoreClass(analysis.security.score);
            
            // Update style
            const styleScore = document.getElementById('styleScore');
            styleScore.textContent = analysis.style.score.toFixed(1) + '/100';
            styleScore.className = 'score ' + getScoreClass(analysis.style.score);
        }
        
        function getScoreClass(score) {
            if (score >= 80) return 'good';
            if (score >= 60) return 'medium';
            return 'poor';
        }
        
        function createSession() {
            const sessionId = document.getElementById('sessionId').value || generateSessionId();
            document.getElementById('sessionId').value = sessionId;
            
            socket.emit('create_session', {
                session_id: sessionId,
                code: editor.getValue(),
                language: document.getElementById('languageSelect').value
            });
            
            currentSession = sessionId;
            updateSessionStats(sessionId, 'created');
        }
        
        function joinSession() {
            const sessionId = document.getElementById('sessionId').value;
            if (!sessionId) {
                alert('Please enter a session ID');
                return;
            }
            
            socket.emit('join_session', {
                session_id: sessionId
            });
            
            currentSession = sessionId;
            updateSessionStats(sessionId, 'joined');
        }
        
        function generateSessionId() {
            return 'session_' + Math.random().toString(36).substr(2, 9);
        }
        
        function updateCollaborationUsers(users) {
            const usersDiv = document.getElementById('collaborationUsers');
            usersDiv.innerHTML = '';
            
            users.forEach(user => {
                const badge = document.createElement('div');
                badge.className = 'user-badge';
                badge.textContent = user;
                usersDiv.appendChild(badge);
            });
        }
        
        function updateSessionStats(sessionId, action) {
            const statsDiv = document.getElementById('sessionStats');
            statsDiv.innerHTML = `
                <p><strong>Session ID:</strong> ${sessionId}</p>
                <p><strong>Status:</strong> ${action}</p>
                <p><strong>Language:</strong> ${document.getElementById('languageSelect').value}</p>
            `;
        }
        
        // Initialize with welcome message
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                updateAIResponse({
                    task_type: 'welcome',
                    confidence: 1.0,
                    processing_time: 0,
                    explanation: 'Welcome to the Advanced Code Assistant! Start by writing code or describing what you want to create.',
                    suggestions: [
                        'Try the code generation feature',
                        'Use code completion for faster development',
                        'Analyze your code for improvements',
                        'Generate unit tests automatically',
                        'Collaborate with others in real-time'
                    ]
                });
            }, 1000);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Serve the advanced AI assistant dashboard"""
    return render_template_string(ADVANCED_HTML_TEMPLATE)

@app.route('/api/generate-code', methods=['POST'])
def generate_code_endpoint():
    """Generate code using AI"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Missing prompt in request', 'status': 'error'}), 400
        
        prompt = data['prompt']
        language = LanguageType(data.get('language', 'python'))
        context = data.get('context', '')
        
        # Generate code using AI assistant
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(ai_assistant.generate_code(prompt, language, context))
        
        return jsonify({
            'status': 'success',
            'task_type': result.task_type.value,
            'output_code': result.output_code,
            'explanation': result.explanation,
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'suggestions': result.suggestions,
            'timestamp': result.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Code generation error: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/complete-code', methods=['POST'])
def complete_code_endpoint():
    """Complete partial code using AI"""
    try:
        data = request.get_json()
        
        if not data or 'partial_code' not in data:
            return jsonify({'error': 'Missing partial_code in request', 'status': 'error'}), 400
        
        partial_code = data['partial_code']
        language = LanguageType(data.get('language', 'python'))
        
        # Complete code using AI assistant
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(ai_assistant.complete_code(partial_code, language))
        
        return jsonify({
            'status': 'success',
            'task_type': result.task_type.value,
            'output_code': result.output_code,
            'explanation': result.explanation,
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'suggestions': result.suggestions,
            'timestamp': result.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Code completion error: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/review-code', methods=['POST'])
def review_code_endpoint():
    """Review code and provide suggestions"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({'error': 'Missing code in request', 'status': 'error'}), 400
        
        code = data['code']
        language = LanguageType(data.get('language', 'python'))
        
        # Review code using AI assistant
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(ai_assistant.review_code(code, language))
        
        return jsonify({
            'status': 'success',
            'task_type': result.task_type.value,
            'output_code': result.output_code,
            'explanation': result.explanation,
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'suggestions': result.suggestions,
            'timestamp': result.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Code review error: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/generate-tests', methods=['POST'])
def generate_tests_endpoint():
    """Generate unit tests for code"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({'error': 'Missing code in request', 'status': 'error'}), 400
        
        code = data['code']
        language = LanguageType(data.get('language', 'python'))
        
        # Generate tests using AI assistant
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(ai_assistant.generate_tests(code, language))
        
        return jsonify({
            'status': 'success',
            'task_type': result.task_type.value,
            'output_code': result.output_code,
            'explanation': result.explanation,
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'suggestions': result.suggestions,
            'timestamp': result.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Test generation error: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/analyze-code', methods=['POST'])
def analyze_code_endpoint():
    """Analyze code for complexity, security, and style"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({'error': 'Missing code in request', 'status': 'error'}), 400
        
        code = data['code']
        language = LanguageType(data.get('language', 'python'))
        
        # Perform analysis
        complexity_result = ai_assistant.code_analyzer.analyze_complexity(code, language)
        security_result = ai_assistant.code_analyzer.analyze_security(code, language)
        style_result = ai_assistant.code_analyzer.analyze_style(code, language)
        
        # Save results to database
        ai_assistant.db_manager.save_analysis_result(complexity_result)
        ai_assistant.db_manager.save_analysis_result(security_result)
        ai_assistant.db_manager.save_analysis_result(style_result)
        
        return jsonify({
            'status': 'success',
            'analysis': {
                'complexity': asdict(complexity_result),
                'security': asdict(security_result),
                'style': asdict(style_result)
            }
        })
        
    except Exception as e:
        logger.error(f"Code analysis error: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

# SocketIO events for real-time collaboration
@socketio.on('create_session')
def handle_create_session(data):
    """Create a new collaboration session"""
    session_id = data['session_id']
    code = data['code']
    language = LanguageType(data['language'])
    
    session = ai_assistant.create_collaboration_session(session_id, code, language)
    join_room(session_id)
    
    emit('session_created', {
        'session_id': session_id,
        'status': 'success'
    })

@socketio.on('join_session')
def handle_join_session(data):
    """Join an existing collaboration session"""
    session_id = data['session_id']
    user_id = session.get('user_id', f'user_{len(ai_assistant.collaboration_sessions.get(session_id, {}).get("participants", []))}')
    
    session_obj = ai_assistant.join_collaboration_session(session_id, user_id)
    
    if session_obj:
        join_room(session_id)
        emit('session_joined', {
            'session_id': session_id,
            'code': session_obj.code_content,
            'language': session_obj.language.value,
            'status': 'success'
        })
        
        emit('user_joined', {
            'session_id': session_id,
            'user_id': user_id,
            'users': session_obj.participants
        }, room=session_id)
    else:
        emit('session_error', {
            'error': 'Session not found'
        })

@socketio.on('code_change')
def handle_code_change(data):
    """Handle real-time code changes"""
    session_id = data['session_id']
    new_code = data['code']
    user_id = session.get('user_id', 'anonymous')
    
    if ai_assistant.update_collaboration_code(session_id, new_code, user_id):
        emit('code_updated', {
            'session_id': session_id,
            'code': new_code,
            'user_id': user_id
        }, room=session_id, include_self=False)

@app.route('/api/status')
def status():
    """Enhanced API status endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'features': [
            'Code Generation',
            'Code Completion',
            'Code Review',
            'Test Generation',
            'Code Analysis',
            'Real-time Collaboration',
            'Multi-language Support'
        ],
        'supported_languages': [lang.value for lang in LanguageType],
        'openai_available': ai_assistant.openai_client is not None,
        'active_sessions': len(ai_assistant.collaboration_sessions),
        'author': 'Gabriel Demetrios Lafis',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    logger.info("Starting Advanced Code Assistant")
    logger.info("Author: Gabriel Demetrios Lafis")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
