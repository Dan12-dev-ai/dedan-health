import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate

from .base_agent import BaseDEDANAgent
from .triage_agent import TriageAgent
from .safety_guard_agent import SafetyGuardAgent
from .guideline_agent import GuidelineAgent
from .risk_prediction_agent import RiskPredictionAgent
try:
    from models_v2 import (
    AgentInput, AgentOutput, AgentType,
    CoordinatorAgentInput, TriageResponseV2,
    TriageLevel, RiskScore, RiskTimeHorizon
    )
except ImportError:  # pragma: no cover - package-relative fallback
    from ..models_v2 import (
    AgentInput, AgentOutput, AgentType,
    CoordinatorAgentInput, TriageResponseV2,
    TriageLevel, RiskScore, RiskTimeHorizon
    )

class CoordinatorAgent(BaseDEDANAgent):
    """
    DEDAN Coordinator Agent - Orchestrates all specialized agents.
    Manages the complete triage workflow and synthesizes results.
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_type=AgentType.COORDINATOR, **kwargs)
        
        # Initialize specialized agents
        self.triage_agent = TriageAgent(**kwargs)
        self.safety_guard_agent = SafetyGuardAgent(**kwargs)
        self.guideline_agent = GuidelineAgent(**kwargs)
        self.risk_prediction_agent = RiskPredictionAgent(**kwargs)
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build specialized prompt template for coordination."""
        
        template = """
You are the DEDAN Health coordinator AI, orchestrating a comprehensive medical triage system.
Your role is to synthesize outputs from specialized agents into a unified, patient-friendly response.

COORDINATION RESPONSIBILITIES:
1. Integrate triage assessment with safety validation
2. Incorporate clinical guidelines and local considerations
3. Combine risk predictions with current presentation
4. Ensure patient safety is prioritized
5. Provide clear, actionable recommendations

AGENT OUTPUTS TO SYNTHESIZE:
{agent_outputs}

PATIENT INFORMATION:
{patient_info}

SYMPTOMS:
{symptoms}

{language_context}

{region_context}

SYNTHESIS INSTRUCTIONS:
1. Prioritize safety guard findings above all else
2. Use triage level as primary classification
3. Incorporate risk prediction for chronic conditions
4. Apply guideline recommendations
5. Generate patient-friendly summary

RESPONSE FORMAT:
Provide your synthesis in this exact JSON format:
{{
    "patient_summary": "Clear, simple explanation for patient",
    "final_triage_level": "emergency|urgent|routine|self_care",
    "final_risk_score": "low|medium|high",
    "final_risk_time_horizon": "immediate|30_days|90_days|1_year|5_years",
    "suggested_next_step": "Specific, actionable next step",
    "risk_flags": ["flag1", "flag2"],
    "confidence_score": 0.85,
    "reasoning": "Coordination reasoning and synthesis logic"
}}

SAFETY FIRST RULES:
- If safety guard detects emergency: FINAL TRIAGE = EMERGENCY
- If risk prediction shows high risk: UPGRADE TRIAGE by one level
- If multiple risk flags: Recommend urgent evaluation
- Always provide clear action steps

{chronic_care_info}

{home_measurements}

Respond with ONLY JSON format above. Ensure patient safety and clarity.
"""
        
        return ChatPromptTemplate.from_template(template)
    
    async def process(self, input_data: CoordinatorAgentInput) -> TriageResponseV2:
        """
        Main coordination method - orchestrates all agents and synthesizes results.
        """
        
        start_time = datetime.utcnow()
        session_id = input_data.session_id
        
        try:
            print(f"Starting DEDAN 2.0 coordination for session {session_id}")
            
            # Step 1: Run Triage Agent
            print("Step 1: Running Triage Agent...")
            triage_input = AgentInput(
                agent_type=AgentType.TRIAGE,
                session_id=session_id,
                patient=input_data.patient,
                symptoms=input_data.symptoms,
                chronic_care_data=input_data.chronic_care_data,
                home_measurements=input_data.home_measurements,
                context=input_data.context
            )
            
            triage_output = await self.triage_agent.process(triage_input)
            
            # Step 2: Run Safety Guard Agent
            print("Step 2: Running Safety Guard Agent...")
            from models_v2 import SafetyGuardAgentInput, TriageAgentOutput, TriageLevel
            # Convert AgentOutput to TriageAgentOutput
            triage_result = triage_output.result
            triage_agent_output = TriageAgentOutput(
                agent_type=AgentType.TRIAGE,
                session_id=session_id,
                confidence_score=triage_output.confidence_score,
                reasoning=triage_output.reasoning,
                result=triage_result,
                risk_flags=triage_output.risk_flags,
                metadata=triage_output.metadata,
                triage_level=TriageLevel(triage_result.get('triage_level', 'routine')),
                differential_diagnoses=triage_result.get('differential_diagnoses', []),
                recommended_tests=triage_result.get('recommended_tests', []),
                next_step=triage_result.get('next_step', ''),
            )
            safety_input = SafetyGuardAgentInput(
                agent_type=AgentType.SAFETY_GUARD,
                session_id=session_id,
                patient=input_data.patient,
                symptoms=input_data.symptoms,
                chronic_care_data=input_data.chronic_care_data,
                home_measurements=input_data.home_measurements,
                triage_output=triage_agent_output,
            )
            
            safety_output = await self.safety_guard_agent.process(safety_input)
            
            # Step 3: Run Guideline Agent
            print("Step 3: Running Guideline Agent...")
            from models_v2 import GuidelineAgentInput, GuidelineAgentOutput, SafetyGuardAgentOutput
            # Convert safety_output to SafetyGuardAgentOutput
            safety_result = safety_output.result
            safety_agent_output = SafetyGuardAgentOutput(
                agent_type=AgentType.SAFETY_GUARD,
                session_id=session_id,
                confidence_score=safety_output.confidence_score,
                reasoning=safety_output.reasoning,
                result=safety_result,
                risk_flags=safety_output.risk_flags,
                metadata=safety_output.metadata,
                emergency_detected=safety_result.get('emergency_detected', False),
                emergency_type=safety_result.get('emergency_type'),
                safety_concerns=safety_result.get('safety_concerns', []),
                requires_immediate_action=safety_result.get('requires_immediate_action', False),
                recommended_action=safety_result.get('recommended_action', ''),
            )
            guideline_input = GuidelineAgentInput(
                agent_type=AgentType.GUIDELINE,
                session_id=session_id,
                patient=input_data.patient,
                symptoms=input_data.symptoms,
                chronic_care_data=input_data.chronic_care_data,
                home_measurements=input_data.home_measurements,
                triage_output=triage_agent_output,
                safety_output=safety_agent_output,
            )
            
            guideline_output = await self.guideline_agent.process(guideline_input)
            
            # Step 4: Run Risk Prediction Agent
            print("Step 4: Running Risk Prediction Agent...")
            from models_v2 import RiskPredictionAgentInput, RiskPredictionAgentOutput
            # Convert guideline_output to GuidelineAgentOutput
            guideline_result = guideline_output.result
            guideline_agent_output = GuidelineAgentOutput(
                agent_type=AgentType.GUIDELINE,
                session_id=session_id,
                confidence_score=guideline_output.confidence_score,
                reasoning=guideline_output.reasoning,
                result=guideline_result,
                risk_flags=guideline_output.risk_flags,
                metadata=guideline_output.metadata,
                relevant_guidelines=guideline_result.get('relevant_guidelines', []),
                local_considerations=guideline_result.get('local_considerations', []),
                evidence_level=guideline_result.get('evidence_level', 'C'),
                recommendations=guideline_result.get('recommendations', []),
            )
            risk_input = RiskPredictionAgentInput(
                agent_type=AgentType.RISK_PREDICTION,
                session_id=session_id,
                patient=input_data.patient,
                symptoms=input_data.symptoms,
                chronic_care_data=input_data.chronic_care_data,
                home_measurements=input_data.home_measurements,
                triage_output=triage_agent_output,
                safety_output=safety_agent_output,
                guideline_output=guideline_agent_output,
            )
            
            risk_output = await self.risk_prediction_agent.process(risk_input)
            
            # Step 5: Synthesize all agent outputs
            print("Step 5: Synthesizing agent outputs...")
            agent_outputs = {
                AgentType.TRIAGE: triage_output,
                AgentType.SAFETY_GUARD: safety_output,
                AgentType.GUIDELINE: guideline_output,
                AgentType.RISK_PREDICTION: risk_output
            }
            
            synthesis_result = await self._synthesize_agent_outputs(
                input_data, agent_outputs
            )
            
            # Create final response
            response = TriageResponseV2(
                session_id=session_id,
                patient_summary=synthesis_result['patient_summary'],
                triage_level=synthesis_result['final_triage_level'],
                risk_score=synthesis_result['final_risk_score'],
                risk_time_horizon=synthesis_result['final_risk_time_horizon'],
                confidence_score=synthesis_result['confidence_score'],
                suggested_next_step=synthesis_result['suggested_next_step'],
                risk_flags=synthesis_result['risk_flags'],
                differential_diagnoses=triage_output.result.get('differential_diagnoses', []),
                recommended_tests=triage_output.result.get('recommended_tests', []),
                relevant_guidelines=guideline_output.result.get('relevant_guidelines', []),
                risk_explanation=risk_output.result.get('risk_explanation', ''),
                preventive_actions=risk_output.result.get('preventive_actions', []),
                follow_up_interval=risk_output.result.get('follow_up_interval'),
                agent_outputs={agent_type.value: output.dict() for agent_type, output in agent_outputs.items()},
                safety_concerns=safety_output.result.get('safety_concerns', []),
                requires_immediate_action=safety_output.result.get('requires_immediate_action', False),
                metadata={
                    'coordination_time': (datetime.utcnow() - start_time).total_seconds(),
                    'agent_count': len(agent_outputs),
                    'total_tokens': sum(
                        output.metadata.get('tokens_used', 0) 
                        for output in agent_outputs.values()
                    )
                }
            )
            
            print(f"Completed DEDAN 2.0 coordination for session {session_id}")
            return response
            
        except Exception as e:
            print(f"Error in coordination for session {session_id}: {str(e)}")
            raise
    
    async def _synthesize_agent_outputs(
        self, 
        input_data: CoordinatorAgentInput,
        agent_outputs: Dict[AgentType, AgentOutput]
    ) -> Dict[str, Any]:
        """Synthesize outputs from all agents into unified response."""
        
        triage_output = agent_outputs[AgentType.TRIAGE]
        safety_output = agent_outputs[AgentType.SAFETY_GUARD]
        guideline_output = agent_outputs[AgentType.GUIDELINE]
        risk_output = agent_outputs[AgentType.RISK_PREDICTION]
        
        # Apply safety-first rules
        final_triage_level = self._apply_safety_first_rules(
            triage_output.result.get('triage_level'),
            safety_output.result,
            risk_output.result
        )
        
        # Determine final risk score
        final_risk_score = self._determine_final_risk_score(
            risk_output.result.get('risk_score'),
            safety_output.result,
            triage_output.result
        )
        
        # Determine risk time horizon
        final_risk_time_horizon = self._determine_final_time_horizon(
            risk_output.result.get('risk_time_horizon'),
            final_triage_level,
            safety_output.result
        )
        
        # Generate patient summary
        patient_summary = self._generate_patient_summary(
            input_data, agent_outputs, final_triage_level, final_risk_score
        )
        
        # Determine suggested next step
        suggested_next_step = self._determine_final_next_step(
            final_triage_level,
            safety_output.result,
            risk_output.result,
            guideline_output.result
        )
        
        # Combine risk flags
        all_risk_flags = []
        for output in agent_outputs.values():
            all_risk_flags.extend(output.risk_flags)
        
        # Calculate overall confidence
        confidence_scores = [
            output.confidence_score for output in agent_outputs.values()
        ]
        overall_confidence = sum(confidence_scores) / len(confidence_scores)
        
        return {
            'patient_summary': patient_summary,
            'final_triage_level': final_triage_level,
            'final_risk_score': final_risk_score,
            'final_risk_time_horizon': final_risk_time_horizon,
            'suggested_next_step': suggested_next_step,
            'risk_flags': list(set(all_risk_flags)),  # Remove duplicates
            'confidence_score': overall_confidence
        }
    
    def _apply_safety_first_rules(
        self, 
        triage_level: str,
        safety_output: Dict[str, Any],
        risk_output: Dict[str, Any]
    ) -> str:
        """Apply safety-first rules to determine final triage level."""
        
        # Rule 1: Safety guard emergency overrides everything
        if safety_output.get('emergency_detected'):
            return TriageLevel.EMERGENCY
        
        # Rule 2: High risk with immediate time horizon upgrades triage
        risk_score = risk_output.get('risk_score')
        risk_time_horizon = risk_output.get('risk_time_horizon')
        
        if risk_score == 'high' and risk_time_horizon == 'immediate':
            return TriageLevel.EMERGENCY
        elif risk_score == 'high':
            return TriageLevel.URGENT
        
        # Rule 3: Safety concerns requiring immediate action
        if safety_output.get('requires_immediate_action'):
            if triage_level == 'self_care':
                return TriageLevel.ROUTINE
            elif triage_level == 'routine':
                return TriageLevel.URGENT
        
        # Rule 4: Multiple safety concerns
        safety_concerns = safety_output.get('safety_concerns', [])
        if len(safety_concerns) >= 3:
            if triage_level in ['self_care', 'routine']:
                return TriageLevel.URGENT
        
        # Default to original triage level
        return triage_level
    
    def _determine_final_risk_score(
        self,
        risk_score: str,
        safety_output: Dict[str, Any],
        triage_output: Dict[str, Any]
    ) -> str:
        """Determine final risk score considering all factors."""
        
        # Start with ML risk prediction
        final_risk = risk_score
        
        # Upgrade risk if safety concerns present
        if safety_output.get('emergency_detected'):
            final_risk = 'high'
        elif safety_output.get('requires_immediate_action'):
            if final_risk == 'low':
                final_risk = 'medium'
            elif final_risk == 'medium':
                final_risk = 'high'
        
        # Upgrade risk based on triage level
        triage_level = triage_output.get('triage_level')
        if triage_level == 'emergency':
            final_risk = 'high'
        elif triage_level == 'urgent' and final_risk == 'low':
            final_risk = 'medium'
        
        return final_risk
    
    def _determine_final_time_horizon(
        self,
        risk_time_horizon: str,
        final_triage_level: str,
        safety_output: Dict[str, Any]
    ) -> str:
        """Determine final risk time horizon."""
        
        # Emergency cases always immediate
        if final_triage_level == 'emergency' or safety_output.get('emergency_detected'):
            return RiskTimeHorizon.IMMEDIATE
        
        # Urgent cases are short-term
        if final_triage_level == 'urgent':
            if risk_time_horizon in ['90_days', '1_year', '5_years']:
                return RiskTimeHorizon.THIRTY_DAYS
        
        # Use risk prediction time horizon for non-emergency cases
        return risk_time_horizon
    
    def _generate_patient_summary(
        self,
        input_data: CoordinatorAgentInput,
        agent_outputs: Dict[AgentType, AgentOutput],
        final_triage_level: str,
        final_risk_score: str
    ) -> str:
        """Generate patient-friendly summary of assessment."""
        
        patient = input_data.patient
        symptoms = input_data.symptoms.symptoms
        
        # Base summary based on triage level
        triage_summaries = {
            'emergency': "Based on your symptoms, this appears to be a medical emergency requiring immediate attention.",
            'urgent': "Based on your symptoms, you need medical attention within the next 24 hours.",
            'routine': "Based on your symptoms, you should see a healthcare provider for evaluation.",
            'self_care': "Based on your symptoms, this appears to be a minor condition that can be managed at home."
        }
        
        base_summary = triage_summaries.get(final_triage_level, triage_summaries['routine'])
        
        # Add risk information
        risk_explanations = {
            'high': "Your overall health risk is high, which means you have an increased chance of complications.",
            'medium': "Your overall health risk is moderate, which means you should monitor your condition closely.",
            'low': "Your overall health risk is low, which is good news for your recovery."
        }
        
        risk_explanation = risk_explanations.get(final_risk_score, risk_explanations['medium'])
        
        # Add chronic condition context
        chronic_context = ""
        if patient.chronic_conditions:
            conditions = ", ".join([c.value.replace('_', ' ') for c in patient.chronic_conditions])
            chronic_context = f" Considering your history of {conditions}, "
        
        # Combine into final summary
        summary = f"{base_summary}{chronic_context}{risk_explanation} "
        
        # Add specific guidance based on safety output
        safety_output = agent_outputs[AgentType.SAFETY_GUARD].result
        if safety_output.get('safety_concerns'):
            summary += "We've identified some safety concerns that require attention. "
        
        # Add guideline context
        guideline_output = agent_outputs[AgentType.GUIDELINE].result
        if guideline_output.get('recommendations'):
            summary += "Our recommendations are based on clinical guidelines appropriate for your region. "
        
        return summary.strip()
    
    def _determine_final_next_step(
        self,
        final_triage_level: str,
        safety_output: Dict[str, Any],
        risk_output: Dict[str, Any],
        guideline_output: Dict[str, Any]
    ) -> str:
        """Determine final recommended next step."""
        
        # Start with safety guard recommendation (highest priority)
        if safety_output.get('recommended_action'):
            return safety_output['recommended_action']
        
        # Use triage-based next steps
        triage_steps = {
            'emergency': "Go to the nearest emergency department immediately. Call emergency services if available.",
            'urgent': "Seek medical attention within 24 hours. Contact your local clinic or hospital.",
            'routine': "Schedule an appointment with a healthcare provider within 1-2 weeks.",
            'self_care': "Monitor your symptoms at home. Seek medical care if they worsen or persist."
        }
        
        next_step = triage_steps.get(final_triage_level, triage_steps['routine'])
        
        # Add risk-specific guidance
        if risk_output.get('preventive_actions'):
            top_action = risk_output['preventive_actions'][0] if risk_output['preventive_actions'] else ""
            if top_action:
                next_step += f" Additionally, {top_action.lower()}."
        
        # Add guideline-specific guidance
        if guideline_output.get('recommendations'):
            top_guideline = guideline_output['recommendations'][0] if guideline_output['recommendations'] else ""
            if top_guideline:
                next_step += f" {top_guideline}"
        
        return next_step
    
    def _process_agent_specific_logic(self, input_data: AgentInput) -> Dict[str, Any]:
        """Not used in coordinator - logic is in process method."""
        return {}
    
    def _validate_output(self, output: Dict[str, Any]) -> bool:
        """Not used in coordinator - validation is in process method."""
        return True
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Return capabilities of coordinator and all sub-agents."""
        
        base_capabilities = super().get_agent_capabilities()
        
        # Add sub-agent capabilities
        sub_agents = {
            'triage_agent': self.triage_agent.get_agent_capabilities(),
            'safety_guard_agent': self.safety_guard_agent.get_agent_capabilities(),
            'guideline_agent': self.guideline_agent.get_agent_capabilities(),
            'risk_prediction_agent': self.risk_prediction_agent.get_agent_capabilities()
        }
        
        base_capabilities['sub_agents'] = sub_agents
        base_capabilities['coordination_features'] = [
            'safety_first_rules',
            'risk_escalation',
            'guideline_integration',
            'multi_agent_synthesis',
            'patient_friendly_summaries'
        ]
        
        return base_capabilities
