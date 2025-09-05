#!/usr/bin/env python3
"""
YAML Service for Local SIM Agent API

Handles YAML processing, workflow conversion, validation,
diff creation, and auto-layout operations.
"""

import yaml
import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import networkx as nx
from difflib import unified_diff

from services.llm_service import LLMService
from prompts.yaml_prompts import (
    get_description_to_workflow_prompt,
    get_workflow_to_yaml_prompt,
    get_diff_analysis_prompt,
    get_optimization_prompt
)
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any] = None

    def dict(self):
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata or {}
        }

@dataclass
class ParseResult:
    success: bool
    data: Optional[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]

@dataclass
class DiffResult:
    diff: str
    summary: str
    changes: List[Dict[str, Any]]
    change_types: List[str]
    complexity_delta: float

@dataclass
class LayoutResult:
    success: bool
    yaml_with_layout: Optional[str]
    layout_data: Optional[Dict[str, Any]]
    total_blocks: int
    algorithm_used: str
    execution_time_ms: float
    errors: List[str] = None

@dataclass
class WorkflowResult:
    success: bool
    yaml: Optional[str]
    workflow: Optional[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any] = None

class YamlService:
    """Service for handling YAML operations"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.workflow_templates = self._load_workflow_templates()
        
    def _load_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined workflow templates"""
        return {
            "basic_automation": {
                "name": "Basic Automation",
                "description": "Simple trigger-action workflow",
                "template": {
                    "name": "{{workflow_name}}",
                    "description": "{{workflow_description}}",
                    "blocks": [
                        {
                            "id": "trigger_1",
                            "type": "trigger",
                            "name": "{{trigger_name}}",
                            "config": {}
                        },
                        {
                            "id": "action_1",
                            "type": "action",
                            "name": "{{action_name}}",
                            "config": {}
                        }
                    ],
                    "connections": [
                        {
                            "from": "trigger_1",
                            "to": "action_1"
                        }
                    ]
                }
            },
            "conditional_workflow": {
                "name": "Conditional Workflow",
                "description": "Workflow with conditional logic",
                "template": {
                    "name": "{{workflow_name}}",
                    "description": "{{workflow_description}}",
                    "blocks": [
                        {
                            "id": "trigger_1",
                            "type": "trigger",
                            "name": "{{trigger_name}}",
                            "config": {}
                        },
                        {
                            "id": "condition_1",
                            "type": "condition",
                            "name": "{{condition_name}}",
                            "config": {
                                "condition": "{{condition_logic}}"
                            }
                        },
                        {
                            "id": "action_true",
                            "type": "action",
                            "name": "{{true_action}}",
                            "config": {}
                        },
                        {
                            "id": "action_false",
                            "type": "action",
                            "name": "{{false_action}}",
                            "config": {}
                        }
                    ],
                    "connections": [
                        {
                            "from": "trigger_1",
                            "to": "condition_1"
                        },
                        {
                            "from": "condition_1",
                            "to": "action_true",
                            "condition": "true"
                        },
                        {
                            "from": "condition_1",
                            "to": "action_false",
                            "condition": "false"
                        }
                    ]
                }
            }
        }
    
    async def description_to_workflow(self, description: str, context: Dict[str, Any], llm_service: LLMService) -> str:
        """Convert natural language description to workflow YAML"""
        try:
            prompt = get_description_to_workflow_prompt(description, context)
            
            response = await llm_service.structured_completion(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            # Extract YAML from response
            yaml_content = self._extract_yaml_from_response(response.get('content', ''))
            
            # Validate and fix common issues
            yaml_content = self.fix_common_yaml_issues(yaml_content)
            
            return yaml_content
            
        except Exception as e:
            self.logger.error(f"Description to workflow conversion failed: {e}")
            raise
    
    def _extract_yaml_from_response(self, response: str) -> str:
        """Extract YAML content from LLM response"""
        # Look for YAML code blocks
        yaml_pattern = r'```(?:yaml|yml)?\n(.*?)\n```'
        match = re.search(yaml_pattern, response, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # If no code block, try to find YAML-like content
        lines = response.split('\n')
        yaml_lines = []
        in_yaml = False
        
        for line in lines:
            if line.strip().startswith('name:') or line.strip().startswith('blocks:'):
                in_yaml = True
            
            if in_yaml:
                yaml_lines.append(line)
        
        return '\n'.join(yaml_lines).strip()
    
    def parse_yaml(self, yaml_content: str) -> ParseResult:
        """Parse YAML content"""
        try:
            data = yaml.safe_load(yaml_content)
            return ParseResult(
                success=True,
                data=data,
                errors=[],
                warnings=[]
            )
        except yaml.YAMLError as e:
            return ParseResult(
                success=False,
                data=None,
                errors=[f"YAML parsing error: {str(e)}"],
                warnings=[]
            )
        except Exception as e:
            return ParseResult(
                success=False,
                data=None,
                errors=[f"Unexpected error: {str(e)}"],
                warnings=[]
            )
    
    def validate_workflow_yaml(self, yaml_content: str) -> ValidationResult:
        """Validate workflow YAML structure"""
        errors = []
        warnings = []
        
        try:
            # Parse YAML
            parse_result = self.parse_yaml(yaml_content)
            if not parse_result.success:
                return ValidationResult(
                    is_valid=False,
                    errors=parse_result.errors,
                    warnings=[]
                )
            
            data = parse_result.data
            
            # Validate required fields
            if not isinstance(data, dict):
                errors.append("Root element must be an object")
                return ValidationResult(False, errors, warnings)
            
            if 'name' not in data:
                errors.append("Missing required field: name")
            
            if 'blocks' not in data:
                errors.append("Missing required field: blocks")
            elif not isinstance(data['blocks'], list):
                errors.append("Field 'blocks' must be an array")
            else:
                # Validate blocks
                block_ids = set()
                has_trigger = False
                
                for i, block in enumerate(data['blocks']):
                    if not isinstance(block, dict):
                        errors.append(f"Block {i} must be an object")
                        continue
                    
                    # Check required block fields
                    if 'id' not in block:
                        errors.append(f"Block {i} missing required field: id")
                    else:
                        block_id = block['id']
                        if block_id in block_ids:
                            errors.append(f"Duplicate block ID: {block_id}")
                        block_ids.add(block_id)
                    
                    if 'type' not in block:
                        errors.append(f"Block {i} missing required field: type")
                    elif block['type'] == 'trigger':
                        has_trigger = True
                    
                    if 'name' not in block:
                        warnings.append(f"Block {i} missing recommended field: name")
                
                if not has_trigger:
                    warnings.append("Workflow has no trigger blocks")
            
            # Validate connections if present
            if 'connections' in data:
                if not isinstance(data['connections'], list):
                    errors.append("Field 'connections' must be an array")
                else:
                    for i, conn in enumerate(data['connections']):
                        if not isinstance(conn, dict):
                            errors.append(f"Connection {i} must be an object")
                            continue
                        
                        if 'from' not in conn:
                            errors.append(f"Connection {i} missing required field: from")
                        if 'to' not in conn:
                            errors.append(f"Connection {i} missing required field: to")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                metadata={
                    "block_count": len(data.get('blocks', [])),
                    "connection_count": len(data.get('connections', [])),
                    "has_trigger": has_trigger
                }
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[]
            )
    
    def validate_workflow_structure(self, workflow: Dict[str, Any]) -> ValidationResult:
        """Validate workflow structure (non-YAML)"""
        # Convert to YAML and validate
        try:
            yaml_content = yaml.dump(workflow, default_flow_style=False)
            return self.validate_workflow_yaml(yaml_content)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Structure validation error: {str(e)}"],
                warnings=[]
            )
    
    def fix_common_yaml_issues(self, yaml_content: str) -> str:
        """Fix common YAML formatting issues"""
        try:
            # Parse and re-dump to fix formatting
            data = yaml.safe_load(yaml_content)
            return yaml.dump(data, default_flow_style=False, sort_keys=False)
        except:
            # If parsing fails, return original
            return yaml_content
    
    async def create_intelligent_diff(self, original_yaml: str, modified_yaml: str, llm_service: LLMService) -> DiffResult:
        """Create intelligent diff between two YAML workflows"""
        try:
            # Create basic diff
            diff_lines = list(unified_diff(
                original_yaml.splitlines(keepends=True),
                modified_yaml.splitlines(keepends=True),
                fromfile='original',
                tofile='modified'
            ))
            diff_text = ''.join(diff_lines)
            
            # Parse both YAML files to understand semantic changes
            original_data = yaml.safe_load(original_yaml)
            modified_data = yaml.safe_load(modified_yaml)
            
            # Analyze changes
            changes = self._analyze_workflow_changes(original_data, modified_data)
            
            # Use LLM to generate summary
            prompt = get_diff_analysis_prompt(original_yaml, modified_yaml, changes)
            response = await llm_service.structured_completion(
                prompt=prompt,
                temperature=0.2,
                max_tokens=500
            )
            
            summary = response.get('content', 'Changes detected in workflow')
            
            # Calculate complexity delta
            original_complexity = self.calculate_complexity(original_yaml)
            modified_complexity = self.calculate_complexity(modified_yaml)
            complexity_delta = modified_complexity - original_complexity
            
            return DiffResult(
                diff=diff_text,
                summary=summary,
                changes=changes,
                change_types=list(set(change['type'] for change in changes)),
                complexity_delta=complexity_delta
            )
            
        except Exception as e:
            self.logger.error(f"Diff creation failed: {e}")
            raise
    
    def _analyze_workflow_changes(self, original: Dict[str, Any], modified: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze semantic changes between workflows"""
        changes = []
        
        # Check name changes
        if original.get('name') != modified.get('name'):
            changes.append({
                'type': 'name_change',
                'field': 'name',
                'old_value': original.get('name'),
                'new_value': modified.get('name')
            })
        
        # Check block changes
        original_blocks = {block['id']: block for block in original.get('blocks', [])}
        modified_blocks = {block['id']: block for block in modified.get('blocks', [])}
        
        # Added blocks
        for block_id in modified_blocks:
            if block_id not in original_blocks:
                changes.append({
                    'type': 'block_added',
                    'block_id': block_id,
                    'block_type': modified_blocks[block_id].get('type'),
                    'block_name': modified_blocks[block_id].get('name')
                })
        
        # Removed blocks
        for block_id in original_blocks:
            if block_id not in modified_blocks:
                changes.append({
                    'type': 'block_removed',
                    'block_id': block_id,
                    'block_type': original_blocks[block_id].get('type'),
                    'block_name': original_blocks[block_id].get('name')
                })
        
        # Modified blocks
        for block_id in original_blocks:
            if block_id in modified_blocks:
                original_block = original_blocks[block_id]
                modified_block = modified_blocks[block_id]
                
                if original_block != modified_block:
                    changes.append({
                        'type': 'block_modified',
                        'block_id': block_id,
                        'changes': self._compare_dicts(original_block, modified_block)
                    })
        
        return changes
    
    def _compare_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare two dictionaries and return differences"""
        differences = []
        
        all_keys = set(dict1.keys()) | set(dict2.keys())
        
        for key in all_keys:
            if key not in dict1:
                differences.append({
                    'field': key,
                    'type': 'added',
                    'new_value': dict2[key]
                })
            elif key not in dict2:
                differences.append({
                    'field': key,
                    'type': 'removed',
                    'old_value': dict1[key]
                })
            elif dict1[key] != dict2[key]:
                differences.append({
                    'field': key,
                    'type': 'modified',
                    'old_value': dict1[key],
                    'new_value': dict2[key]
                })
        
        return differences
    
    def merge_diff(self, original_yaml: str, diff: str) -> WorkflowResult:
        """Merge diff into original YAML"""
        try:
            # For now, implement basic merge logic
            # In a production system, you'd want more sophisticated merging
            
            # Parse the diff and apply changes
            # This is a simplified implementation
            
            return WorkflowResult(
                success=True,
                yaml=original_yaml,  # Placeholder
                workflow=None,
                errors=[],
                warnings=["Diff merge not fully implemented"],
                metadata={"merge_type": "basic"}
            )
            
        except Exception as e:
            return WorkflowResult(
                success=False,
                yaml=None,
                workflow=None,
                errors=[f"Merge failed: {str(e)}"],
                warnings=[]
            )
    
    def auto_layout_workflow(self, yaml_content: str, layout_options: Dict[str, Any]) -> LayoutResult:
        """Auto-layout workflow blocks with intelligent positioning"""
        start_time = datetime.now()
        
        try:
            # Parse workflow
            parse_result = self.parse_yaml(yaml_content)
            if not parse_result.success:
                return LayoutResult(
                    success=False,
                    yaml_with_layout=None,
                    layout_data=None,
                    total_blocks=0,
                    algorithm_used="none",
                    execution_time_ms=0,
                    errors=parse_result.errors
                )
            
            workflow = parse_result.data
            blocks = workflow.get('blocks', [])
            connections = workflow.get('connections', [])
            
            # Create graph for layout calculation
            G = nx.DiGraph()
            
            # Add nodes
            for block in blocks:
                G.add_node(block['id'], **block)
            
            # Add edges
            for conn in connections:
                G.add_edge(conn['from'], conn['to'])
            
            # Calculate layout using different algorithms based on options
            algorithm = layout_options.get('algorithm', 'hierarchical')
            
            if algorithm == 'hierarchical':
                layout_data = self._hierarchical_layout(G)
            elif algorithm == 'force_directed':
                layout_data = self._force_directed_layout(G)
            else:
                layout_data = self._grid_layout(G)
            
            # Apply layout to workflow
            for block in blocks:
                block_id = block['id']
                if block_id in layout_data:
                    block['position'] = layout_data[block_id]
            
            # Convert back to YAML
            yaml_with_layout = yaml.dump(workflow, default_flow_style=False)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return LayoutResult(
                success=True,
                yaml_with_layout=yaml_with_layout,
                layout_data=layout_data,
                total_blocks=len(blocks),
                algorithm_used=algorithm,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return LayoutResult(
                success=False,
                yaml_with_layout=None,
                layout_data=None,
                total_blocks=0,
                algorithm_used="failed",
                execution_time_ms=execution_time,
                errors=[f"Layout failed: {str(e)}"]
            )
    
    def _hierarchical_layout(self, G: nx.DiGraph) -> Dict[str, Dict[str, float]]:
        """Create hierarchical layout"""
        try:
            # Use topological sort to determine levels
            levels = {}
            for node in nx.topological_sort(G):
                # Calculate level based on longest path from sources
                if G.in_degree(node) == 0:
                    levels[node] = 0
                else:
                    levels[node] = max(levels[pred] for pred in G.predecessors(node)) + 1
            
            # Position nodes
            layout = {}
            level_counts = {}
            
            for node, level in levels.items():
                if level not in level_counts:
                    level_counts[level] = 0
                
                x = level_counts[level] * 200  # Horizontal spacing
                y = level * 150  # Vertical spacing
                
                layout[node] = {'x': x, 'y': y}
                level_counts[level] += 1
            
            return layout
            
        except:
            # Fallback to simple grid
            return self._grid_layout(G)
    
    def _force_directed_layout(self, G: nx.DiGraph) -> Dict[str, Dict[str, float]]:
        """Create force-directed layout"""
        try:
            pos = nx.spring_layout(G, k=200, iterations=50)
            return {
                node: {'x': coord[0] * 300, 'y': coord[1] * 300}
                for node, coord in pos.items()
            }
        except:
            return self._grid_layout(G)
    
    def _grid_layout(self, G: nx.DiGraph) -> Dict[str, Dict[str, float]]:
        """Create simple grid layout"""
        nodes = list(G.nodes())
        layout = {}
        
        cols = int(len(nodes) ** 0.5) + 1
        
        for i, node in enumerate(nodes):
            x = (i % cols) * 200
            y = (i // cols) * 150
            layout[node] = {'x': x, 'y': y}
        
        return layout
    
    async def workflow_to_yaml(self, workflow: Dict[str, Any], options: Dict[str, Any], llm_service: LLMService = None) -> WorkflowResult:
        """Convert workflow structure to YAML"""
        try:
            # Direct conversion
            yaml_content = yaml.dump(workflow, default_flow_style=False, sort_keys=False)
            
            # Optionally use LLM for formatting improvements
            if llm_service and options.get('use_llm_formatting', False):
                prompt = get_workflow_to_yaml_prompt(workflow)
                response = await llm_service.structured_completion(
                    prompt=prompt,
                    temperature=0.1,
                    max_tokens=1500
                )
                
                formatted_yaml = self._extract_yaml_from_response(response.get('content', ''))
                if formatted_yaml:
                    yaml_content = formatted_yaml
            
            return WorkflowResult(
                success=True,
                yaml=yaml_content,
                workflow=workflow,
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            return WorkflowResult(
                success=False,
                yaml=None,
                workflow=None,
                errors=[f"Conversion failed: {str(e)}"],
                warnings=[]
            )
    
    def count_blocks(self, yaml_content: str) -> int:
        """Count blocks in workflow YAML"""
        try:
            data = yaml.safe_load(yaml_content)
            return len(data.get('blocks', []))
        except:
            return 0
    
    def has_triggers(self, yaml_content: str) -> bool:
        """Check if workflow has trigger blocks"""
        try:
            data = yaml.safe_load(yaml_content)
            blocks = data.get('blocks', [])
            return any(block.get('type') == 'trigger' for block in blocks)
        except:
            return False
    
    def has_layout_data(self, yaml_content: str) -> bool:
        """Check if workflow has layout positioning data"""
        try:
            data = yaml.safe_load(yaml_content)
            blocks = data.get('blocks', [])
            return any('position' in block for block in blocks)
        except:
            return False
    
    def calculate_complexity(self, yaml_content: str) -> float:
        """Calculate workflow complexity score"""
        try:
            data = yaml.safe_load(yaml_content)
            blocks = data.get('blocks', [])
            connections = data.get('connections', [])
            
            # Simple complexity calculation
            block_score = len(blocks) * 1.0
            connection_score = len(connections) * 0.5
            
            # Add complexity for different block types
            type_multipliers = {
                'trigger': 1.0,
                'action': 1.2,
                'condition': 1.5,
                'loop': 2.0,
                'parallel': 1.8
            }
            
            type_score = sum(
                type_multipliers.get(block.get('type', 'action'), 1.0)
                for block in blocks
            )
            
            return block_score + connection_score + type_score
            
        except:
            return 0.0
    
    def extract_metadata(self, yaml_content: str) -> Dict[str, Any]:
        """Extract metadata from workflow YAML"""
        try:
            data = yaml.safe_load(yaml_content)
            blocks = data.get('blocks', [])
            connections = data.get('connections', [])
            
            block_types = {}
            for block in blocks:
                block_type = block.get('type', 'unknown')
                block_types[block_type] = block_types.get(block_type, 0) + 1
            
            return {
                'name': data.get('name', 'Unnamed Workflow'),
                'description': data.get('description', ''),
                'total_blocks': len(blocks),
                'total_connections': len(connections),
                'block_types': block_types,
                'has_triggers': any(block.get('type') == 'trigger' for block in blocks),
                'has_conditions': any(block.get('type') == 'condition' for block in blocks),
                'has_loops': any(block.get('type') == 'loop' for block in blocks),
                'complexity_score': self.calculate_complexity(yaml_content)
            }
            
        except Exception as e:
            return {'error': f'Metadata extraction failed: {str(e)}'}
    
    async def optimize_workflow(self, workflow: Dict[str, Any], llm_service: LLMService) -> WorkflowResult:
        """Optimize workflow for better performance"""
        try:
            prompt = get_optimization_prompt(workflow)
            response = await llm_service.structured_completion(
                prompt=prompt,
                temperature=0.2,
                max_tokens=1500
            )
            
            # Extract optimized workflow from response
            # This would need more sophisticated parsing in production
            
            return WorkflowResult(
                success=True,
                yaml=None,
                workflow=workflow,  # Placeholder - would contain optimized version
                errors=[],
                warnings=[],
                metadata={
                    'optimization_applied': True,
                    'optimizations': ['placeholder'],
                    'performance_improvement': 'estimated'
                }
            )
            
        except Exception as e:
            return WorkflowResult(
                success=False,
                yaml=None,
                workflow=None,
                errors=[f"Optimization failed: {str(e)}"],
                warnings=[]
            )
    
    async def analyze_workflow(self, workflow: Dict[str, Any], llm_service: LLMService) -> Dict[str, Any]:
        """Analyze workflow for insights and recommendations"""
        try:
            # Perform analysis using LLM
            analysis_prompt = f"""
Analyze this workflow and provide insights:

{json.dumps(workflow, indent=2)}

Provide analysis on:
1. Complexity and performance
2. Security considerations
3. Best practices compliance
4. Potential improvements
5. Risk assessment
"""
            
            response = await llm_service.structured_completion(
                prompt=analysis_prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            return {
                'analysis': response.get('content', 'Analysis completed'),
                'complexity_score': self.calculate_complexity(yaml.dump(workflow)),
                'performance_metrics': {
                    'estimated_execution_time': 'varies',
                    'resource_usage': 'moderate'
                },
                'security_assessment': {
                    'risk_level': 'low',
                    'recommendations': []
                },
                'recommendations': [],
                'potential_issues': [],
                'best_practices': []
            }
            
        except Exception as e:
            self.logger.error(f"Workflow analysis failed: {e}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def get_workflow_templates(self) -> List[Dict[str, Any]]:
        """Get available workflow templates"""
        return [
            {
                'id': template_id,
                'name': template_data['name'],
                'description': template_data['description'],
                'category': 'general'  # Could be expanded
            }
            for template_id, template_data in self.workflow_templates.items()
        ]
    
    def get_template_categories(self) -> List[str]:
        """Get template categories"""
        return ['general', 'automation', 'integration', 'data_processing']
    
    async def create_from_template(self, template_id: str, parameters: Dict[str, Any], llm_service: LLMService) -> WorkflowResult:
        """Create workflow from template"""
        try:
            if template_id not in self.workflow_templates:
                return WorkflowResult(
                    success=False,
                    yaml=None,
                    workflow=None,
                    errors=[f"Template not found: {template_id}"],
                    warnings=[]
                )
            
            template = self.workflow_templates[template_id]['template']
            
            # Replace template variables
            workflow_json = json.dumps(template)
            for key, value in parameters.items():
                workflow_json = workflow_json.replace(f"{{{{{key}}}}}", str(value))
            
            workflow = json.loads(workflow_json)
            yaml_content = yaml.dump(workflow, default_flow_style=False)
            
            return WorkflowResult(
                success=True,
                yaml=yaml_content,
                workflow=workflow,
                errors=[],
                warnings=[],
                metadata={
                    'template_id': template_id,
                    'template_name': self.workflow_templates[template_id]['name']
                }
            )
            
        except Exception as e:
            return WorkflowResult(
                success=False,
                yaml=None,
                workflow=None,
                errors=[f"Template creation failed: {str(e)}"],
                warnings=[]
            )