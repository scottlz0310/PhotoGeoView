"""
AI Integration Test Suite

Comprehensive testing framework for multi-AI integration:
- Multi-AI test coordination
- Integration tests for AI component interactions
- Performance benchmarks comparing integrated vs individual AI performance
- Automated test discovery and execution

Author: Kiro AI Integration System
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models import AIComponent


@dataclass
class TestResult:
    """Test result data structure"""

    test_name: str
    ai_component: AIComponent
    status: str  # passed, failed, error, skipped
    duration: float
    error_message: Optional[str] = None
    performance_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class IntegrationTestResult:
    """Integration test result with multi-AI coordination"""

    test_name: str
    components_involved: List[AIComponent]
    status: str
    duration: float
    individual_results: List[TestResult]
