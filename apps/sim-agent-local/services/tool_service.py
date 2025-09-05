#!/usr/bin/env python3
"""
Tool Service for Local SIM Agent API

Handles tool completion tracking, status management,
and analytics for the copilot functionality.
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from collections import defaultdict

from utils.logging import get_logger

logger = get_logger(__name__)

class ToolStatus(Enum):
    """Tool execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class ToolType(Enum):
    """Tool types"""
    FILE_OPERATION = "file_operation"
    CODE_GENERATION = "code_generation"
    SEARCH = "search"
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    OTHER = "other"

@dataclass
class ToolExecution:
    """Tool execution record"""
    tool_id: str
    session_id: str
    tool_name: str
    tool_type: ToolType
    status: ToolStatus
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert enums to strings
        data['status'] = self.status.value
        data['tool_type'] = self.tool_type.value
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'updated_at', 'started_at', 'completed_at']:
            if data[field]:
                data[field] = data[field].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolExecution':
        """Create from dictionary"""
        # Convert string enums back to enums
        data['status'] = ToolStatus(data['status'])
        data['tool_type'] = ToolType(data['tool_type'])
        # Convert ISO strings back to datetime objects
        for field in ['created_at', 'updated_at', 'started_at', 'completed_at']:
            if data[field]:
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)

@dataclass
class ToolAnalytics:
    """Tool usage analytics"""
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_duration_ms: float
    success_rate: float
    executions_by_type: Dict[str, int]
    executions_by_status: Dict[str, int]
    recent_executions: List[Dict[str, Any]]
    performance_trends: Dict[str, Any]
    error_patterns: List[Dict[str, Any]]

class ToolService:
    """Service for managing tool executions"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.tools: Dict[str, ToolExecution] = {}
        self.session_tools: Dict[str, List[str]] = defaultdict(list)
        self.cleanup_interval = 3600  # 1 hour
        self.max_tool_age_hours = 24  # Keep tools for 24 hours
        
        # Start cleanup task
        asyncio.create_task(self._periodic_cleanup())
    
    def create_tool(self, session_id: str, tool_name: str, tool_type: str, 
                   input_data: Optional[Dict[str, Any]] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new tool execution record"""
        tool_id = str(uuid.uuid4())
        
        try:
            tool_type_enum = ToolType(tool_type)
        except ValueError:
            tool_type_enum = ToolType.OTHER
        
        now = datetime.now()
        
        tool = ToolExecution(
            tool_id=tool_id,
            session_id=session_id,
            tool_name=tool_name,
            tool_type=tool_type_enum,
            status=ToolStatus.PENDING,
            created_at=now,
            updated_at=now,
            input_data=input_data or {},
            metadata=metadata or {}
        )
        
        self.tools[tool_id] = tool
        self.session_tools[session_id].append(tool_id)
        
        self.logger.info(f"Created tool {tool_id} for session {session_id}")
        return tool_id
    
    def start_tool(self, tool_id: str) -> bool:
        """Mark tool as started"""
        if tool_id not in self.tools:
            self.logger.warning(f"Tool {tool_id} not found")
            return False
        
        tool = self.tools[tool_id]
        tool.status = ToolStatus.RUNNING
        tool.started_at = datetime.now()
        tool.updated_at = datetime.now()
        
        self.logger.info(f"Started tool {tool_id}")
        return True
    
    def complete_tool(self, tool_id: str, output_data: Optional[Dict[str, Any]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Mark tool as completed"""
        if tool_id not in self.tools:
            self.logger.warning(f"Tool {tool_id} not found")
            return False
        
        tool = self.tools[tool_id]
        now = datetime.now()
        
        tool.status = ToolStatus.COMPLETED
        tool.completed_at = now
        tool.updated_at = now
        
        if tool.started_at:
            tool.duration_ms = int((now - tool.started_at).total_seconds() * 1000)
        
        if output_data:
            tool.output_data = output_data
        
        if metadata:
            tool.metadata = {**(tool.metadata or {}), **metadata}
        
        self.logger.info(f"Completed tool {tool_id} in {tool.duration_ms}ms")
        return True
    
    def fail_tool(self, tool_id: str, error_message: str,
                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Mark tool as failed"""
        if tool_id not in self.tools:
            self.logger.warning(f"Tool {tool_id} not found")
            return False
        
        tool = self.tools[tool_id]
        now = datetime.now()
        
        tool.status = ToolStatus.FAILED
        tool.completed_at = now
        tool.updated_at = now
        tool.error_message = error_message
        
        if tool.started_at:
            tool.duration_ms = int((now - tool.started_at).total_seconds() * 1000)
        
        if metadata:
            tool.metadata = {**(tool.metadata or {}), **metadata}
        
        self.logger.error(f"Tool {tool_id} failed: {error_message}")
        return True
    
    def cancel_tool(self, tool_id: str, reason: str = "Cancelled by user") -> bool:
        """Cancel a tool execution"""
        if tool_id not in self.tools:
            self.logger.warning(f"Tool {tool_id} not found")
            return False
        
        tool = self.tools[tool_id]
        now = datetime.now()
        
        tool.status = ToolStatus.CANCELLED
        tool.completed_at = now
        tool.updated_at = now
        tool.error_message = reason
        
        if tool.started_at:
            tool.duration_ms = int((now - tool.started_at).total_seconds() * 1000)
        
        self.logger.info(f"Cancelled tool {tool_id}: {reason}")
        return True
    
    def get_tool_status(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get tool status"""
        if tool_id not in self.tools:
            return None
        
        return self.tools[tool_id].to_dict()
    
    def get_session_tools(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all tools for a session"""
        tool_ids = self.session_tools.get(session_id, [])
        return [self.tools[tool_id].to_dict() for tool_id in tool_ids if tool_id in self.tools]
    
    def update_tool(self, tool_id: str, updates: Dict[str, Any]) -> bool:
        """Update tool information"""
        if tool_id not in self.tools:
            self.logger.warning(f"Tool {tool_id} not found")
            return False
        
        tool = self.tools[tool_id]
        
        # Update allowed fields
        allowed_updates = ['tool_name', 'input_data', 'output_data', 'metadata']
        
        for key, value in updates.items():
            if key in allowed_updates:
                setattr(tool, key, value)
        
        tool.updated_at = datetime.now()
        
        self.logger.info(f"Updated tool {tool_id}")
        return True
    
    def delete_tool(self, tool_id: str) -> bool:
        """Delete a tool"""
        if tool_id not in self.tools:
            self.logger.warning(f"Tool {tool_id} not found")
            return False
        
        tool = self.tools[tool_id]
        session_id = tool.session_id
        
        # Remove from tools
        del self.tools[tool_id]
        
        # Remove from session tools
        if session_id in self.session_tools:
            self.session_tools[session_id] = [
                tid for tid in self.session_tools[session_id] if tid != tool_id
            ]
        
        self.logger.info(f"Deleted tool {tool_id}")
        return True
    
    def bulk_complete_tools(self, tool_ids: List[str], 
                           output_data: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """Mark multiple tools as completed"""
        results = {}
        
        for tool_id in tool_ids:
            results[tool_id] = self.complete_tool(tool_id, output_data)
        
        completed_count = sum(1 for success in results.values() if success)
        self.logger.info(f"Bulk completed {completed_count}/{len(tool_ids)} tools")
        
        return results
    
    def get_analytics(self, session_id: Optional[str] = None, 
                     hours_back: int = 24) -> ToolAnalytics:
        """Get tool usage analytics"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # Filter tools
        if session_id:
            tool_ids = self.session_tools.get(session_id, [])
            tools = [self.tools[tid] for tid in tool_ids if tid in self.tools]
        else:
            tools = list(self.tools.values())
        
        # Filter by time
        tools = [tool for tool in tools if tool.created_at >= cutoff_time]
        
        if not tools:
            return ToolAnalytics(
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                average_duration_ms=0.0,
                success_rate=0.0,
                executions_by_type={},
                executions_by_status={},
                recent_executions=[],
                performance_trends={},
                error_patterns=[]
            )
        
        # Calculate metrics
        total_executions = len(tools)
        successful_executions = len([t for t in tools if t.status == ToolStatus.COMPLETED])
        failed_executions = len([t for t in tools if t.status == ToolStatus.FAILED])
        
        # Calculate average duration
        completed_tools = [t for t in tools if t.duration_ms is not None]
        average_duration_ms = (
            sum(t.duration_ms for t in completed_tools) / len(completed_tools)
            if completed_tools else 0.0
        )
        
        success_rate = successful_executions / total_executions if total_executions > 0 else 0.0
        
        # Group by type
        executions_by_type = defaultdict(int)
        for tool in tools:
            executions_by_type[tool.tool_type.value] += 1
        
        # Group by status
        executions_by_status = defaultdict(int)
        for tool in tools:
            executions_by_status[tool.status.value] += 1
        
        # Recent executions (last 10)
        recent_tools = sorted(tools, key=lambda t: t.created_at, reverse=True)[:10]
        recent_executions = [tool.to_dict() for tool in recent_tools]
        
        # Performance trends (simplified)
        performance_trends = self._calculate_performance_trends(tools)
        
        # Error patterns
        error_patterns = self._analyze_error_patterns(tools)
        
        return ToolAnalytics(
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            average_duration_ms=average_duration_ms,
            success_rate=success_rate,
            executions_by_type=dict(executions_by_type),
            executions_by_status=dict(executions_by_status),
            recent_executions=recent_executions,
            performance_trends=performance_trends,
            error_patterns=error_patterns
        )
    
    def _calculate_performance_trends(self, tools: List[ToolExecution]) -> Dict[str, Any]:
        """Calculate performance trends"""
        if not tools:
            return {}
        
        # Group by hour
        hourly_stats = defaultdict(lambda: {'count': 0, 'success': 0, 'total_duration': 0})
        
        for tool in tools:
            hour_key = tool.created_at.strftime('%Y-%m-%d %H:00')
            hourly_stats[hour_key]['count'] += 1
            
            if tool.status == ToolStatus.COMPLETED:
                hourly_stats[hour_key]['success'] += 1
            
            if tool.duration_ms:
                hourly_stats[hour_key]['total_duration'] += tool.duration_ms
        
        # Calculate trends
        trends = []
        for hour, stats in sorted(hourly_stats.items()):
            avg_duration = stats['total_duration'] / stats['count'] if stats['count'] > 0 else 0
            success_rate = stats['success'] / stats['count'] if stats['count'] > 0 else 0
            
            trends.append({
                'hour': hour,
                'executions': stats['count'],
                'success_rate': success_rate,
                'average_duration_ms': avg_duration
            })
        
        return {
            'hourly_trends': trends,
            'trend_direction': 'stable'  # Could be calculated based on recent vs older data
        }
    
    def _analyze_error_patterns(self, tools: List[ToolExecution]) -> List[Dict[str, Any]]:
        """Analyze error patterns"""
        failed_tools = [t for t in tools if t.status == ToolStatus.FAILED and t.error_message]
        
        if not failed_tools:
            return []
        
        # Group by error message patterns
        error_groups = defaultdict(list)
        
        for tool in failed_tools:
            # Simple pattern matching - could be more sophisticated
            error_key = tool.error_message[:50] if tool.error_message else "Unknown error"
            error_groups[error_key].append(tool)
        
        patterns = []
        for error_pattern, error_tools in error_groups.items():
            patterns.append({
                'pattern': error_pattern,
                'count': len(error_tools),
                'percentage': len(error_tools) / len(failed_tools) * 100,
                'first_occurrence': min(t.created_at for t in error_tools).isoformat(),
                'last_occurrence': max(t.created_at for t in error_tools).isoformat(),
                'affected_tool_types': list(set(t.tool_type.value for t in error_tools))
            })
        
        # Sort by count descending
        patterns.sort(key=lambda p: p['count'], reverse=True)
        
        return patterns[:10]  # Return top 10 patterns
    
    async def _periodic_cleanup(self):
        """Periodically clean up old tools"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_tools()
            except Exception as e:
                self.logger.error(f"Cleanup task failed: {e}")
    
    async def _cleanup_old_tools(self):
        """Clean up tools older than max_tool_age_hours"""
        cutoff_time = datetime.now() - timedelta(hours=self.max_tool_age_hours)
        
        tools_to_remove = []
        for tool_id, tool in self.tools.items():
            if tool.created_at < cutoff_time:
                tools_to_remove.append(tool_id)
        
        for tool_id in tools_to_remove:
            self.delete_tool(tool_id)
        
        if tools_to_remove:
            self.logger.info(f"Cleaned up {len(tools_to_remove)} old tools")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        total_tools = len(self.tools)
        active_sessions = len([s for s in self.session_tools.values() if s])
        
        # Calculate recent performance
        recent_tools = [
            tool for tool in self.tools.values()
            if tool.created_at >= datetime.now() - timedelta(hours=1)
        ]
        
        recent_success_rate = 0.0
        if recent_tools:
            recent_successful = len([t for t in recent_tools if t.status == ToolStatus.COMPLETED])
            recent_success_rate = recent_successful / len(recent_tools)
        
        return {
            'status': 'healthy',
            'total_tools': total_tools,
            'active_sessions': active_sessions,
            'recent_tools_count': len(recent_tools),
            'recent_success_rate': recent_success_rate,
            'memory_usage': {
                'tools_in_memory': total_tools,
                'sessions_tracked': len(self.session_tools)
            },
            'uptime_info': {
                'cleanup_interval_seconds': self.cleanup_interval,
                'max_tool_age_hours': self.max_tool_age_hours
            }
        }
    
    def export_tools(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Export tools data"""
        if session_id:
            tool_ids = self.session_tools.get(session_id, [])
            tools = [self.tools[tid] for tid in tool_ids if tid in self.tools]
        else:
            tools = list(self.tools.values())
        
        return [tool.to_dict() for tool in tools]
    
    def import_tools(self, tools_data: List[Dict[str, Any]]) -> int:
        """Import tools data"""
        imported_count = 0
        
        for tool_data in tools_data:
            try:
                tool = ToolExecution.from_dict(tool_data)
                self.tools[tool.tool_id] = tool
                self.session_tools[tool.session_id].append(tool.tool_id)
                imported_count += 1
            except Exception as e:
                self.logger.error(f"Failed to import tool: {e}")
        
        self.logger.info(f"Imported {imported_count} tools")
        return imported_count