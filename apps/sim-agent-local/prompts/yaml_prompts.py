"""YAML processing prompts for the Local SIM Agent API"""

def get_description_to_workflow_prompt() -> str:
    """Get the prompt for converting descriptions to workflow YAML"""
    return DESCRIPTION_TO_YAML_PROMPT

def get_workflow_to_yaml_prompt() -> str:
    """Get the prompt for converting workflow structures to YAML"""
    return DESCRIPTION_TO_YAML_PROMPT  # Reuse the same prompt for now

def get_diff_analysis_prompt() -> str:
    """Get the prompt for analyzing workflow diffs"""
    return CREATE_DIFF_PROMPT

def get_optimization_prompt() -> str:
    """Get the prompt for optimizing workflows"""
    return OPTIMIZE_WORKFLOW_PROMPT

# Prompt for converting natural language descriptions to workflow YAML
DESCRIPTION_TO_YAML_PROMPT = """
You are an expert workflow designer. Convert the following natural language description into a valid workflow YAML.

Description: {description}
Workflow Type: {workflow_type}

Requirements:
1. Create a valid YAML structure for a workflow
2. Include appropriate blocks, connections, and metadata
3. Use realistic block types and configurations
4. Ensure the workflow logically follows the description
5. Include proper error handling where appropriate
6. Add meaningful names and descriptions

The YAML should follow this general structure:
```yaml
name: "Workflow Name"
description: "Brief description"
version: "1.0.0"
blocks:
  - id: "block_1"
    type: "block_type"
    name: "Block Name"
    config:
      # Block-specific configuration
    position:
      x: 100
      y: 100
connections:
  - from: "block_1"
    to: "block_2"
    condition: "success"
triggers:
  - type: "manual"
    config: {{}}
metadata:
  created_at: "{timestamp}"
  complexity: "medium"
  category: "{category}"
```

Generate only the YAML content, no additional text or explanations.
"""

# Prompt for creating intelligent diffs between YAML workflows
CREATE_DIFF_PROMPT = """
You are an expert at analyzing workflow differences. Create an intelligent diff between two workflow YAML files.

Original YAML:
{original_yaml}

Modified YAML:
{modified_yaml}

Requirements:
1. Identify all meaningful changes between the workflows
2. Categorize changes as: added, removed, modified, moved
3. Focus on structural and functional differences
4. Ignore insignificant whitespace or formatting changes
5. Provide clear descriptions of what changed
6. Include the specific values that were changed

Return a JSON object with this structure:
{{
  "summary": "Brief description of overall changes",
  "changes": [
    {{
      "type": "added|removed|modified|moved",
      "path": "yaml.path.to.changed.element",
      "description": "Human-readable description of the change",
      "old_value": "previous value (for modified/removed)",
      "new_value": "new value (for added/modified)"
    }}
  ],
  "impact": "low|medium|high",
  "recommendations": ["List of recommendations based on changes"]
}}

Generate only the JSON object, no additional text.
"""

# Prompt for optimizing workflow performance
OPTIMIZE_WORKFLOW_PROMPT = """
You are a workflow optimization expert. Analyze the given workflow and suggest optimizations for better performance.

Workflow YAML:
{workflow_yaml}

Analyze the workflow for:
1. Performance bottlenecks
2. Redundant or unnecessary blocks
3. Inefficient connections or flow patterns
4. Resource usage optimization
5. Error handling improvements
6. Parallel execution opportunities
7. Caching and optimization strategies

Return a JSON object with this structure:
{{
  "analysis": {{
    "current_complexity": "low|medium|high",
    "performance_score": 85,
    "bottlenecks": ["List of identified bottlenecks"],
    "strengths": ["List of workflow strengths"]
  }},
  "optimizations": [
    {{
      "type": "performance|structure|error_handling|resource",
      "priority": "high|medium|low",
      "description": "Description of the optimization",
      "implementation": "How to implement this optimization",
      "expected_impact": "Expected performance improvement"
    }}
  ],
  "optimized_yaml": "The optimized workflow YAML",
  "summary": "Summary of all optimizations made"
}}

Generate only the JSON object, no additional text.
"""

# Prompt for analyzing workflows and providing insights
ANALYZE_WORKFLOW_PROMPT = """
You are a workflow analysis expert. Provide comprehensive insights about the given workflow.

Workflow YAML:
{workflow_yaml}

Analyze the workflow for:
1. Overall structure and design quality
2. Complexity assessment
3. Potential issues or risks
4. Best practices compliance
5. Scalability considerations
6. Maintainability factors
7. Security implications
8. Performance characteristics

Return a JSON object with this structure:
{{
  "overview": {{
    "name": "Workflow name",
    "description": "Brief description",
    "complexity_score": 75,
    "quality_score": 85,
    "block_count": 10,
    "connection_count": 12
  }},
  "analysis": {{
    "strengths": ["List of workflow strengths"],
    "weaknesses": ["List of potential issues"],
    "risks": ["List of identified risks"],
    "opportunities": ["List of improvement opportunities"]
  }},
  "metrics": {{
    "complexity": "low|medium|high",
    "maintainability": "low|medium|high",
    "scalability": "low|medium|high",
    "performance": "low|medium|high",
    "security": "low|medium|high"
  }},
  "recommendations": [
    {{
      "category": "structure|performance|security|maintainability",
      "priority": "high|medium|low",
      "recommendation": "Specific recommendation",
      "rationale": "Why this recommendation is important"
    }}
  ],
  "summary": "Overall assessment and key takeaways"
}}

Generate only the JSON object, no additional text.
"""

# Prompt for fixing common YAML issues
FIX_YAML_PROMPT = """
You are a YAML expert. Fix the following YAML content that has formatting or structural issues.

Problematic YAML:
{yaml_content}

Common issues to fix:
1. Indentation problems
2. Missing quotes around strings with special characters
3. Invalid YAML syntax
4. Inconsistent formatting
5. Missing required fields
6. Type mismatches

Requirements:
1. Fix all YAML syntax errors
2. Ensure proper indentation (2 spaces)
3. Add quotes where necessary
4. Maintain the original structure and meaning
5. Follow YAML best practices

Return only the corrected YAML content, no additional text or explanations.
"""

# Prompt for validating workflow structure
VALIDATE_WORKFLOW_PROMPT = """
You are a workflow validation expert. Validate the structure and content of the given workflow.

Workflow YAML:
{workflow_yaml}

Validation criteria:
1. Required fields are present (name, blocks, connections)
2. Block IDs are unique and properly referenced
3. Connections reference valid block IDs
4. Block types are valid and properly configured
5. Workflow logic is sound and executable
6. No circular dependencies exist
7. Proper error handling is in place

Return a JSON object with this structure:
{{
  "is_valid": true,
  "errors": [
    {{
      "type": "error|warning",
      "path": "yaml.path.to.issue",
      "message": "Description of the issue",
      "suggestion": "How to fix this issue"
    }}
  ],
  "warnings": [
    {{
      "type": "warning",
      "path": "yaml.path.to.issue",
      "message": "Description of the warning",
      "suggestion": "Recommended improvement"
    }}
  ],
  "summary": "Overall validation summary",
  "score": 85
}}

Generate only the JSON object, no additional text.
"""

# Prompt for extracting metadata from workflows
EXTRACT_METADATA_PROMPT = """
You are a workflow metadata extraction expert. Extract comprehensive metadata from the given workflow.

Workflow YAML:
{workflow_yaml}

Extract the following metadata:
1. Basic information (name, description, version)
2. Structural metrics (block count, connection count, complexity)
3. Block type distribution
4. Workflow characteristics (has triggers, has error handling, etc.)
5. Performance indicators
6. Category and classification

Return a JSON object with this structure:
{{
  "basic": {{
    "name": "Workflow name",
    "description": "Description",
    "version": "1.0.0",
    "created_at": "timestamp",
    "category": "automation|data_processing|integration|other"
  }},
  "structure": {{
    "block_count": 10,
    "connection_count": 12,
    "trigger_count": 1,
    "max_depth": 5,
    "has_loops": false,
    "has_parallel_paths": true
  }},
  "blocks": {{
    "types": {{"input": 2, "process": 5, "output": 3}},
    "most_common_type": "process",
    "unique_types": ["input", "process", "output"]
  }},
  "complexity": {{
    "score": 75,
    "level": "medium",
    "factors": ["List of complexity factors"]
  }},
  "characteristics": {{
    "has_error_handling": true,
    "has_conditional_logic": true,
    "has_loops": false,
    "has_parallel_execution": true,
    "has_external_integrations": false
  }},
  "estimated_runtime": "5-10 minutes",
  "resource_requirements": "low|medium|high"
}}

Generate only the JSON object, no additional text.
"""