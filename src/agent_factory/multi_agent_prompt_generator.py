from enum import Enum
from typing import Dict, List, Optional, Callable
from pydantic import BaseModel, ValidationError, validator
import json
import yaml
import hashlib
import inspect

class AgentRole(str, Enum):
    ANALYZE = "requirements_analysis"
    PLAN = "architecture_planning"
    CODE = "code_generation"
    VALIDATE = "quality_validation"
    TEST = "test_engineering"
    DOC = "documentation_generation"
    DEPLOY = "deployment_management"

class AgentState(BaseModel):
    current_task: str
    dependencies: List[str]
    artifacts: Dict[str, str]
    constraints: List[str]
    quality_gates: List[str]

class SWEPromptConfig(BaseModel):
    role_instructions: Dict[AgentRole, str]
    quality_standards: Dict[str, List[str]]
    style_guides: Dict[str, Dict]
    domain_knowledge: Dict[str, List[str]]

class MultiAgentPromptGenerator:
    def __init__(self, config_path: str = None):
        self.state = AgentState(
            current_task="initializing",
            dependencies=[],
            artifacts={},
            constraints=[],
            quality_gates=[]
        )
        self.agent_personas = self._load_default_personas()
        self.validator = PromptValidator()
        self._init_core_templates()
        
        if config_path:
            self.load_config(config_path)

    def _load_default_personas(self) -> Dict[AgentRole, Dict]:
        return {
            AgentRole.ANALYZE: {
                "type": "critical_thinker",
                "traits": ["analytical", "skeptical", "detail-oriented"],
                "communication": "precise technical terminology"
            },
            AgentRole.CODE: {
                "type": "craftsman",
                "traits": ["pragmatic", "optimizer", "pattern-oriented"],
                "communication": "code examples with explanations"
            }
            # ... other agents
        }

    def _init_core_templates(self):
        self.templates = {
            AgentRole.ANALYZE: {
                "base": (
                    "As {system_role} analyzing {problem_domain}, "
                    "identify:\n1. Key requirements\n2. Hidden constraints\n"
                    "3. Domain-specific patterns\nOutput format: {format}"
                ),
                "validation": [
                    ("require_use_case_coverage", lambda x: "use cases" in x),
                    ("check_constraint_identification", lambda x: len(x.get("constraints", [])) >= 3)
                ]
            },
            AgentRole.CODE: {
                "base": (
                    "Generate {language} code meeting:\n{requirements}\n"
                    "Adhere to:\n- {style_guide}\n- {security_standards}\n"
                    "Include:\n- Error handling\n- Performance optimizations\n"
                    "Format: {format} with inline documentation"
                ),
                "validation": [
                    ("syntax_check", self._validate_code_syntax),
                    ("security_audit", self._check_security_patterns)
                ]
            }
            # ... templates for other agents
        }

    def generate_agent_prompt(
        self,
        role: AgentRole,
        task_context: Dict,
        previous_outputs: Dict[AgentRole, str] = None,
        quality_gate: str = "strict"
    ) -> str:
        persona = self.agent_personas[role]
        template = self.templates[role]["base"]
        
        prompt = template.format(
            system_role=persona["type"],
            **self._resolve_dynamic_vars(role, task_context),
            **self._get_style_guide(role),
            **self._get_domain_knowledge(task_context.get("domain"))
        )

        prompt += self._build_quality_section(quality_gate)
        prompt += self._build_artifact_context(previous_outputs)
        prompt += self._build_state_awareness()
        
        return self.validator.validate(prompt, role)

    def _resolve_dynamic_vars(self, role: AgentRole, context: Dict) -> Dict:
        resolvers = {
            AgentRole.ANALYZE: self._resolve_analysis_vars,
            AgentRole.CODE: self._resolve_code_vars,
            # ... other resolvers
        }
        return resolvers.get(role, lambda x: {})(context)

    def _resolve_code_vars(self, context: Dict) -> Dict:
        return {
            "requirements": "\n".join(context.get("requirements", [])),
            "security_standards": "OWASP Top 10, CWE/SANS Top 25",
            "style_guide": context.get("style_guide", "PEP8")
        }

    def _build_quality_section(self, quality_gate: str) -> str:
        return f"\n\nQuality Requirements ({quality_gate}):\n" + "\n".join([
            f"- {req}" for req in self.config.quality_standards.get(quality_gate, [])
        ])

    def _build_artifact_context(self, previous_outputs: Dict) -> str:
        if not previous_outputs:
            return ""
        
        context = "\n\nArtifact Context:\n"
        for agent, output in previous_outputs.items():
            context += f"{agent.value} Output:\n{output[:500]}\n\n"
        return context

    def _build_state_awareness(self) -> str:
        return (
            f"\n\nSystem State:\nCurrent Task: {self.state.current_task}\n"
            f"Active Constraints: {', '.join(self.state.constraints)}\n"
            f"Quality Gates Passed: {len(self.state.quality_gates)}"
        )

    def update_state(self, new_state: Dict):
        self.state = self.state.copy(update=new_state)

    def load_config(self, config_path: str):
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
        self.config = SWEPromptConfig(**config_data)

class PromptValidator:
    def validate(self, prompt: str, role: AgentRole) -> str:
        self._check_injection_attempts(prompt)
        self._validate_role_specific_rules(prompt, role)
        self._ensure_artifacts_integrity(prompt)
        return prompt

    def _check_injection_attempts(self, prompt: str):
        patterns = [
            r"ignore previous",
            r"secret\s*:",
            r"hidden\s*:",
            r"system\s*:"
        ]
        for pattern in patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                raise SecurityError(f"Potential injection detected: {pattern}")

    def _validate_role_specific_rules(self, prompt: str, role: AgentRole):
        role_rules = {
            AgentRole.DEPLOY: [
                ("security_references", lambda p: "OWASP" in p),
                ("environment_constraints", lambda p: "production" in p)
            ],
            AgentRole.VALIDATE: [
                ("validation_criteria", lambda p: "edge cases" in p)
            ]
        }
        for rule_name, check in role_rules.get(role, []):
            if not check(prompt):
                raise ValidationError(f"Failed {rule_name} validation")

class SWEPromptEnhancer:
    def enhance_prompt(self, prompt: str, enhancement_type: str) -> str:
        enhancements = {
            "security": self._add_security_enhancements,
            "performance": self._add_performance_enhancements,
            "maintainability": self._add_maintainability_enhancements
        }
        return enhancements.get(enhancement_type, lambda x: x)(prompt)

    def _add_security_enhancements(self, prompt: str) -> str:
        return prompt + "\n\nSecurity Requirements:\n- Input validation\n- Secure defaults\n- Principle of least privilege"

    def _add_performance_enhancements(self, prompt: str) -> str:
        return prompt + "\n\nPerformance Requirements:\n- O(n) complexity analysis\n- Memory usage limits\n- Parallelization strategy"
