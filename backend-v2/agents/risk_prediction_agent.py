import json
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

from langchain_core.prompts import ChatPromptTemplate

from .base_agent import BaseDEDANAgent
try:
    from models_v2 import (
    AgentInput, AgentOutput, AgentType,
    RiskPredictionAgentInput, RiskPredictionAgentOutput,
    TriageAgentOutput, SafetyGuardAgentOutput, GuidelineAgentOutput,
    RiskScore, RiskTimeHorizon, ChronicCondition, ChronicCareData
    )
except ImportError:  # pragma: no cover - package-relative fallback
    from ..models_v2 import (
    AgentInput, AgentOutput, AgentType,
    RiskPredictionAgentInput, RiskPredictionAgentOutput,
    TriageAgentOutput, SafetyGuardAgentOutput, GuidelineAgentOutput,
    RiskScore, RiskTimeHorizon, ChronicCondition, ChronicCareData
    )

class RiskPredictionAgent(BaseDEDANAgent):
    """
    DEDAN Risk Prediction Agent - Chronic disease risk assessment.
    Uses patient history, triage data, and chronic care data to predict future risk.
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_type=AgentType.RISK_PREDICTION, **kwargs)
        self.risk_models = {}
        self.scalers = {}
        self._load_risk_models()
    
    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build specialized prompt template for risk prediction."""
        
        template = """
You are a chronic disease risk prediction specialist for DEDAN Health.
Your role is to assess long-term health risks based on current presentation and history.

RISK ASSESSMENT FRAMEWORK:
1. Current acute condition severity
2. Chronic disease progression risk
3. Complication probability
4. Medication adherence impact
5. Lifestyle and environmental factors

RISK SCORES:
- LOW: <5% probability of serious complications
- MEDIUM: 5-20% probability of serious complications  
- HIGH: >20% probability of serious complications

TIME HORIZONS:
- IMMEDIATE: Risk within 24-48 hours
- 30_DAYS: Risk within next 30 days
- 90_DAYS: Risk within next 90 days
- 1_YEAR: Risk within next year
- 5_YEARS: Long-term risk projection

CHRONIC DISEASE RISK FACTORS:
DIABETES: HbA1c >7%, poor adherence, hypertension, obesity
HYPERTENSION: BP >140/90, poor adherence, smoking, obesity
ASTHMA: Frequent attacks, poor inhaler use, environmental triggers
HIV: Low CD4 count, poor adherence, opportunistic infections
HEART DISEASE: Uncontrolled BP, high cholesterol, smoking, diabetes

PATIENT INFORMATION:
{patient_info}

CURRENT SYMPTOMS:
{symptoms}

TRIAGE ASSESSMENT:
{triage_output}

SAFETY ASSESSMENT:
{safety_output}

GUIDELINE ANALYSIS:
{guideline_output}

{language_context}

{region_context}

CHRONIC CARE DATA:
{chronic_care_info}

HOME MEASUREMENTS:
{home_measurements}

RISK ANALYSIS INSTRUCTIONS:
1. Assess immediate complication risk
2. Evaluate chronic disease control
3. Consider medication adherence
4. Analyze measurement trends
5. Project future risk trajectory

RESPONSE FORMAT:
Provide your analysis in this exact JSON format:
{{
    "risk_score": "low|medium|high",
    "risk_time_horizon": "immediate|30_days|90_days|1_year|5_years",
    "risk_factors": ["factor1", "factor2", "factor3"],
    "risk_explanation": "Plain language explanation of risk",
    "preventive_actions": ["action1", "action2"],
    "follow_up_interval": "1 week|2 weeks|1 month|3 months",
    "reasoning": "Detailed risk assessment reasoning",
    "confidence": 0.85
}}

IMPORTANT: Provide clear, actionable risk information that patients can understand.
Avoid medical jargon. Focus on practical prevention strategies.

Respond with ONLY JSON format above.
"""
        
        return ChatPromptTemplate.from_template(template)
    
    def _process_agent_specific_logic(self, input_data: RiskPredictionAgentInput) -> Dict[str, Any]:
        """Process risk prediction specific logic."""
        
        patient = input_data.patient
        chronic_care_data = input_data.chronic_care_data
        home_measurements = input_data.home_measurements or []
        
        # Calculate risk scores using ML models
        ml_risk_assessment = self._calculate_ml_risk_score(input_data)
        
        # Rule-based risk assessment
        rule_based_risk = self._calculate_rule_based_risk(input_data)
        
        # Combine risk assessments
        combined_risk_score = self._combine_risk_assessments(ml_risk_assessment, rule_based_risk)
        
        # Determine time horizon
        risk_time_horizon = self._determine_risk_time_horizon(
            combined_risk_score, input_data, chronic_care_data
        )
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(input_data, chronic_care_data)
        
        # Generate risk explanation
        risk_explanation = self._generate_risk_explanation(
            combined_risk_score, risk_factors, input_data
        )
        
        # Generate preventive actions
        preventive_actions = self._generate_preventive_actions(
            combined_risk_score, risk_factors, input_data
        )
        
        # Determine follow-up interval
        follow_up_interval = self._determine_follow_up_interval(
            combined_risk_score, risk_time_horizon
        )
        
        return {
            "risk_score": combined_risk_score,
            "risk_time_horizon": risk_time_horizon,
            "risk_factors": risk_factors,
            "risk_explanation": risk_explanation,
            "preventive_actions": preventive_actions,
            "follow_up_interval": follow_up_interval
        }
    
    def _calculate_ml_risk_score(self, input_data: RiskPredictionAgentInput) -> Dict[str, Any]:
        """Calculate risk score using machine learning models."""
        
        try:
            # Prepare features for ML model
            features = self._prepare_ml_features(input_data)
            
            if not features:
                return {"risk_score": "medium", "confidence": 0.5}
            
            # Get appropriate model based on chronic conditions
            primary_condition = self._get_primary_condition(input_data)
            
            if primary_condition and primary_condition in self.risk_models:
                model = self.risk_models[primary_condition]
                scaler = self.scalers[primary_condition]
                
                # Scale features
                features_scaled = scaler.transform([features])
                
                # Predict risk
                risk_probability = model.predict_proba(features_scaled)[0]
                risk_class = model.predict(features_scaled)[0]
                
                return {
                    "risk_score": risk_class,
                    "confidence": np.max(risk_probability),
                    "probability": float(np.max(risk_probability))
                }
            else:
                # Use general risk model
                return {"risk_score": "medium", "confidence": 0.6}
                
        except Exception as e:
            print(f"ML risk calculation error: {e}")
            return {"risk_score": "medium", "confidence": 0.4}
    
    def _calculate_rule_based_risk(self, input_data: RiskPredictionAgentInput) -> Dict[str, Any]:
        """Calculate risk score using rule-based logic."""
        
        patient = input_data.patient
        chronic_care_data = input_data.chronic_care_data
        triage_output = input_data.triage_output
        safety_output = input_data.safety_output
        
        risk_score = 0
        
        # Age-based risk
        if patient.age > 65:
            risk_score += 2
        elif patient.age > 45:
            risk_score += 1
        
        # Chronic condition risk
        high_risk_conditions = [
            ChronicCondition.DIABETES,
            ChronicCondition.HEART_DISEASE,
            ChronicCondition.STROKE
        ]
        
        for condition in patient.chronic_conditions:
            if condition in high_risk_conditions:
                risk_score += 2
            else:
                risk_score += 1
        
        # Triage level risk
        triage_risk_map = {
            "emergency": 3,
            "urgent": 2,
            "routine": 1,
            "self_care": 0
        }
        risk_score += triage_risk_map.get(triage_output.triage_level, 1)
        
        # Safety concerns risk
        if safety_output.emergency_detected:
            risk_score += 3
        
        if safety_output.safety_concerns:
            risk_score += len(safety_output.safety_concerns)
        
        # Chronic care data risk
        if chronic_care_data:
            # Diabetes-specific risks
            if chronic_care_data.last_hba1c and chronic_care_data.last_hba1c > 7:
                risk_score += 2
            
            # Hypertension-specific risks
            if chronic_care_data.last_bp_systolic and chronic_care_data.last_bp_systolic > 140:
                risk_score += 1
            if chronic_care_data.last_bp_diastolic and chronic_care_data.last_bp_diastolic > 90:
                risk_score += 1
            
            # Medication adherence risk
            if chronic_care_data.medication_adherence and chronic_care_data.medication_adherence < 0.8:
                risk_score += 2
        
        # Convert risk score to risk level
        if risk_score >= 8:
            return {"risk_score": "high", "confidence": 0.8, "raw_score": risk_score}
        elif risk_score >= 4:
            return {"risk_score": "medium", "confidence": 0.7, "raw_score": risk_score}
        else:
            return {"risk_score": "low", "confidence": 0.6, "raw_score": risk_score}
    
    def _combine_risk_assessments(
        self, 
        ml_assessment: Dict[str, Any], 
        rule_assessment: Dict[str, Any]
    ) -> str:
        """Combine ML and rule-based risk assessments."""
        
        # Weight the assessments
        ml_weight = 0.6
        rule_weight = 0.4
        
        # Convert to numeric scores
        risk_scores = {"low": 1, "medium": 2, "high": 3}
        
        ml_score = risk_scores.get(ml_assessment.get("risk_score", "medium"), 2)
        rule_score = risk_scores.get(rule_assessment.get("risk_score", "medium"), 2)
        
        # Weighted average
        combined_score = (ml_score * ml_weight + rule_score * rule_weight)
        
        # Convert back to risk level
        if combined_score >= 2.5:
            return "high"
        elif combined_score >= 1.5:
            return "medium"
        else:
            return "low"
    
    def _determine_risk_time_horizon(
        self, 
        risk_score: str, 
        input_data: RiskPredictionAgentInput,
        chronic_care_data: Optional[ChronicCareData]
    ) -> str:
        """Determine appropriate risk time horizon."""
        
        triage_output = input_data.triage_output
        safety_output = input_data.safety_output
        
        # Immediate risks
        if triage_output.triage_level == "emergency" or safety_output.emergency_detected:
            return RiskTimeHorizon.IMMEDIATE
        
        # Short-term risks
        if triage_output.triage_level == "urgent" or risk_score == "high":
            return RiskTimeHorizon.THIRTY_DAYS
        
        # Medium-term risks
        if risk_score == "medium":
            return RiskTimeHorizon.NINETY_DAYS
        
        # Long-term risks for chronic conditions
        if chronic_care_data and input_data.patient.chronic_conditions:
            return RiskTimeHorizon.ONE_YEAR
        
        # Default
        return RiskTimeHorizon.NINETY_DAYS
    
    def _identify_risk_factors(
        self, 
        input_data: RiskPredictionAgentInput, 
        chronic_care_data: Optional[ChronicCareData]
    ) -> List[str]:
        """Identify specific risk factors for the patient."""
        
        patient = input_data.patient
        risk_factors = []
        
        # Age-related factors
        if patient.age > 65:
            risk_factors.append("advanced_age")
        elif patient.age > 45:
            risk_factors.append("middle_age")
        
        # Chronic condition factors
        for condition in patient.chronic_conditions:
            risk_factors.append(f"chronic_{condition.value}")
        
        # Chronic care data factors
        if chronic_care_data:
            if chronic_care_data.last_hba1c and chronic_care_data.last_hba1c > 8:
                risk_factors.append("poor_glycemic_control")
            
            if chronic_care_data.last_bp_systolic and chronic_care_data.last_bp_systolic > 160:
                risk_factors.append("uncontrolled_hypertension")
            
            if chronic_care_data.medication_adherence and chronic_care_data.medication_adherence < 0.7:
                risk_factors.append("poor_medication_adherence")
        
        # Lifestyle factors (inferred from symptoms)
        symptoms_text = input_data.symptoms.symptoms.lower()
        if "smoking" in symptoms_text or "tobacco" in symptoms_text:
            risk_factors.append("smoking")
        
        if "alcohol" in symptoms_text:
            risk_factors.append("alcohol_use")
        
        # Triage-related factors
        if input_data.triage_output.triage_level in ["emergency", "urgent"]:
            risk_factors.append("acute_complication")
        
        # Safety-related factors
        if input_data.safety_output.safety_concerns:
            risk_factors.extend(input_data.safety_output.safety_concerns)
        
        return list(set(risk_factors))
    
    def _generate_risk_explanation(
        self, 
        risk_score: str, 
        risk_factors: List[str], 
        input_data: RiskPredictionAgentInput
    ) -> str:
        """Generate plain language risk explanation."""
        
        patient = input_data.patient
        
        explanations = {
            "low": f"Based on your current health status and {patient.age}-year-old age, your risk of serious complications is low. Continue current treatment and monitor symptoms.",
            "medium": f"Based on your current health status and {patient.age}-year-old age, you have a moderate risk of complications. Close monitoring and follow-up care are recommended.",
            "high": f"Based on your current health status and {patient.age}-year-old age, you have a high risk of complications. Immediate medical attention and intensive monitoring are required."
        }
        
        base_explanation = explanations.get(risk_score, explanations["medium"])
        
        # Add specific factor explanations
        factor_explanations = []
        
        if "advanced_age" in risk_factors:
            factor_explanations.append("Your age increases health risks.")
        
        if "poor_glycemic_control" in risk_factors:
            factor_explanations.append("High blood sugar levels increase diabetes complications.")
        
        if "uncontrolled_hypertension" in risk_factors:
            factor_explanations.append("High blood pressure increases heart and stroke risk.")
        
        if "poor_medication_adherence" in risk_factors:
            factor_explanations.append("Missing medications increases complication risk.")
        
        if factor_explanations:
            base_explanation += " Key factors: " + "; ".join(factor_explanations) + "."
        
        return base_explanation
    
    def _generate_preventive_actions(
        self, 
        risk_score: str, 
        risk_factors: List[str], 
        input_data: RiskPredictionAgentInput
    ) -> List[str]:
        """Generate preventive actions based on risk factors."""
        
        actions = []
        
        # General actions based on risk level
        if risk_score == "high":
            actions.extend([
                "Seek immediate medical evaluation",
                "Take all prescribed medications as directed",
                "Monitor vital signs twice daily"
            ])
        elif risk_score == "medium":
            actions.extend([
                "Schedule medical appointment within 1 week",
                "Ensure medication adherence",
                "Monitor symptoms daily"
            ])
        else:  # low risk
            actions.extend([
                "Continue current treatment plan",
                "Schedule routine follow-up",
                "Maintain healthy lifestyle"
            ])
        
        # Specific actions based on risk factors
        if "poor_glycemic_control" in risk_factors:
            actions.extend([
                "Check blood sugar daily",
                "Follow diabetic diet plan",
                "Exercise regularly as tolerated"
            ])
        
        if "uncontrolled_hypertension" in risk_factors:
            actions.extend([
                "Monitor blood pressure daily",
                "Reduce salt intake",
                "Take antihypertensive medications regularly"
            ])
        
        if "poor_medication_adherence" in risk_factors:
            actions.extend([
                "Use medication reminders",
                "Set up pill organizers",
                "Ask family for support with medications"
            ])
        
        if "smoking" in risk_factors:
            actions.append("Seek smoking cessation support")
        
        return list(set(actions))[:8]  # Limit to 8 actions
    
    def _determine_follow_up_interval(
        self, 
        risk_score: str, 
        risk_time_horizon: str
    ) -> str:
        """Determine appropriate follow-up interval."""
        
        if risk_score == "high" or risk_time_horizon == "immediate":
            return "1 week"
        elif risk_score == "medium" or risk_time_horizon == "30_days":
            return "2 weeks"
        elif risk_time_horizon == "90_days":
            return "1 month"
        else:
            return "3 months"
    
    def _prepare_ml_features(self, input_data: RiskPredictionAgentInput) -> List[float]:
        """Prepare features for ML model."""
        
        features = []
        
        # Demographic features
        features.append(float(input_data.patient.age))
        features.append(1.0 if input_data.patient.sex == "male" else 0.0)
        features.append(float(len(input_data.patient.chronic_conditions)))
        
        # Triage features
        triage_level_map = {"emergency": 3, "urgent": 2, "routine": 1, "self_care": 0}
        features.append(float(triage_level_map.get(input_data.triage_output.triage_level, 1)))
        features.append(input_data.triage_output.confidence_score)
        
        # Safety features
        features.append(1.0 if input_data.safety_output.emergency_detected else 0.0)
        features.append(float(len(input_data.safety_output.safety_concerns)))
        
        # Chronic care features
        if input_data.chronic_care_data:
            features.append(input_data.chronic_care_data.last_hba1c or 0.0)
            features.append(float(input_data.chronic_care_data.last_bp_systolic or 0))
            features.append(float(input_data.chronic_care_data.last_bp_diastolic or 0))
            features.append(input_data.chronic_care_data.medication_adherence or 1.0)
            features.append(float(len(input_data.chronic_care_data.symptom_evolution)))
        else:
            features.extend([0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        
        return features
    
    def _get_primary_condition(self, input_data: RiskPredictionAgentInput) -> Optional[str]:
        """Get primary chronic condition for model selection."""
        
        if not input_data.patient.chronic_conditions:
            return None
        
        # Priority order for model selection
        priority_conditions = [
            ChronicCondition.DIABETES,
            ChronicCondition.HYPERTENSION,
            ChronicCondition.HEART_DISEASE,
            ChronicCondition.ASTHMA,
            ChronicCondition.HIV
        ]
        
        for condition in priority_conditions:
            if condition in input_data.patient.chronic_conditions:
                return condition.value
        
        return input_data.patient.chronic_conditions[0].value
    
    def _load_risk_models(self):
        """Load pre-trained risk prediction models."""
        
        try:
            # Try to load existing models
            for condition in ["diabetes", "hypertension", "heart_disease", "asthma", "hiv"]:
                model_path = f"models/risk_{condition}.pkl"
                scaler_path = f"models/scaler_{condition}.pkl"
                
                try:
                    self.risk_models[condition] = joblib.load(model_path)
                    self.scalers[condition] = joblib.load(scaler_path)
                    print(f"Loaded risk model for {condition}")
                except FileNotFoundError:
                    print(f"No pre-trained model found for {condition}")
        except Exception as e:
            print(f"Error loading risk models: {e}")
    
    def _validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate risk prediction agent output."""
        
        required_fields = [
            'risk_score', 'risk_time_horizon', 'risk_factors',
            'risk_explanation', 'preventive_actions', 'follow_up_interval'
        ]
        
        for field in required_fields:
            if field not in output:
                return False
        
        # Validate risk score
        valid_scores = [score.value for score in RiskScore]
        if output['risk_score'] not in valid_scores:
            return False
        
        # Validate time horizon
        valid_horizons = [horizon.value for horizon in RiskTimeHorizon]
        if output['risk_time_horizon'] not in valid_horizons:
            return False
        
        # Validate lists
        if not isinstance(output['risk_factors'], list):
            return False
        
        if not isinstance(output['preventive_actions'], list):
            return False
        
        # Validate explanation
        if not output['risk_explanation'] or len(output['risk_explanation'].strip()) == 0:
            return False
        
        return True
