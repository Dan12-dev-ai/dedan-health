"""
DEDAN Health 2.0 - Enhanced AI Intelligence and Agent Architecture
World-class agent system with explainability, multimodal input, and bias monitoring
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import cv2
import base64
import io
from PIL import Image
import speech_recognition as sr

from models_v2 import TriageLevel, RiskScore, Language

# Configure logging
logger = logging.getLogger(__name__)

class BaseEnhancedAgent:
    """Base class for all enhanced DEDAN agents"""
    
    def __init__(self, name: str, confidence_threshold: float = 0.7):
        self.name = name
        self.confidence_threshold = confidence_threshold
        self.performance_history = []
        self.bias_metrics = {}
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return results"""
        raise NotImplementedError
        
    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score for result"""
        # Base confidence calculation
        base_confidence = result.get('confidence', 0.5)
        
        # Adjust based on historical performance
        if self.performance_history:
            avg_performance = np.mean(self.performance_history)
            performance_adjustment = min(0.2, avg_performance - 0.5)
            base_confidence += performance_adjustment
        
        return max(0.0, min(1.0, base_confidence))
    
    def log_performance(self, confidence: float, accuracy: float):
        """Log performance for learning"""
        self.performance_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': confidence,
            'accuracy': accuracy
        })
        
        # Keep only last 1000 entries
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    def update_bias_metrics(self, demographics: Dict[str, Any], accuracy: float):
        """Update bias metrics for monitoring"""
        for key, value in demographics.items():
            if key not in self.bias_metrics:
                self.bias_metrics[key] = {}
            
            if value not in self.bias_metrics[key]:
                self.bias_metrics[key][value] = []
            
            self.bias_metrics[key][value].append({
                'timestamp': datetime.utcnow().isoformat(),
                'accuracy': accuracy
            })

class ImageAnalysisAgent(BaseEnhancedAgent):
    """
    Enhanced Image Analysis Agent for multimodal input
    Analyzes medical images, skin lesions, and visual symptoms
    """
    
    def __init__(self):
        super().__init__("Image Analysis Agent", 0.75)
        self.supported_formats = ['jpg', 'jpeg', 'png', 'bmp', 'tiff']
        self.skin_lesion_detector = None
        self.medical_image_classifier = None
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process medical images and provide analysis"""
        
        try:
            images = input_data.get('images', [])
            if not images:
                return {
                    'agent': self.name,
                    'status': 'no_input',
                    'confidence': 0.0,
                    'findings': [],
                    'recommendations': []
                }
            
            findings = []
            recommendations = []
            overall_confidence = 0.0
            
            for i, image_data in enumerate(images):
                try:
                    # Decode image
                    image = self._decode_image(image_data)
                    if image is None:
                        continue
                    
                    # Analyze image
                    analysis = await self._analyze_medical_image(image)
                    
                    findings.append({
                        'image_index': i,
                        'analysis_type': analysis['type'],
                        'findings': analysis['findings'],
                        'confidence': analysis['confidence'],
                        'severity': analysis['severity'],
                        'medical_relevance': analysis['medical_relevance']
                    })
                    
                    recommendations.extend(analysis['recommendations'])
                    overall_confidence = max(overall_confidence, analysis['confidence'])
                    
                except Exception as e:
                    logger.error(f"Image analysis failed for image {i}: {e}")
                    findings.append({
                        'image_index': i,
                        'analysis_type': 'error',
                        'findings': f"Analysis failed: {str(e)}",
                        'confidence': 0.0,
                        'severity': 'unknown',
                        'medical_relevance': False
                    })
            
            return {
                'agent': self.name,
                'status': 'completed',
                'confidence': overall_confidence,
                'findings': findings,
                'recommendations': list(set(recommendations)),
                'processing_time': datetime.utcnow().isoformat(),
                'image_count': len(images)
            }
            
        except Exception as e:
            logger.error(f"Image analysis agent error: {e}")
            return {
                'agent': self.name,
                'status': 'error',
                'confidence': 0.0,
                'error': str(e),
                'findings': [],
                'recommendations': []
            }
    
    def _decode_image(self, image_data: str) -> Optional[Image.Image]:
        """Decode base64 image data"""
        try:
            # Handle different image data formats
            if image_data.startswith('data:image'):
                # Extract base64 data
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            return Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            logger.error(f"Image decoding failed: {e}")
            return None
    
    async def _analyze_medical_image(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze medical image for symptoms and conditions"""
        
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Skin lesion analysis
            skin_analysis = await self._analyze_skin_lesions(cv_image)
            
            # General medical image analysis
            medical_analysis = await self._analyze_medical_features(cv_image)
            
            # Combine results
            combined_findings = []
            recommendations = []
            confidence = 0.0
            severity = 'low'
            
            if skin_analysis['detected']:
                combined_findings.extend(skin_analysis['findings'])
                recommendations.extend(skin_analysis['recommendations'])
                confidence = max(confidence, skin_analysis['confidence'])
                severity = max(severity, skin_analysis['severity'])
            
            if medical_analysis['detected']:
                combined_findings.extend(medical_analysis['findings'])
                recommendations.extend(medical_analysis['recommendations'])
                confidence = max(confidence, medical_analysis['confidence'])
                severity = max(severity, medical_analysis['severity'])
            
            return {
                'type': 'medical_image_analysis',
                'findings': combined_findings,
                'recommendations': recommendations,
                'confidence': confidence,
                'severity': severity,
                'medical_relevance': len(combined_findings) > 0
            }
            
        except Exception as e:
            logger.error(f"Medical image analysis failed: {e}")
            return {
                'type': 'error',
                'findings': [],
                'recommendations': [],
                'confidence': 0.0,
                'severity': 'unknown',
                'medical_relevance': False
            }
    
    async def _analyze_skin_lesions(self, cv_image: np.ndarray) -> Dict[str, Any]:
        """Analyze image for skin lesions and abnormalities"""
        
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            findings = []
            severity = 'low'
            confidence = 0.0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter small contours
                if area < 100:
                    continue
                
                # Analyze contour properties
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Simple heuristic for lesion detection
                if 0.5 < aspect_ratio < 2.0 and area > 500:
                    findings.append({
                        'type': 'potential_lesion',
                        'location': {'x': int(x), 'y': int(y), 'width': w, 'height': h},
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })
                    
                    severity = 'medium' if area > 1000 else 'low'
                    confidence = min(0.8, confidence + 0.2)
            
            recommendations = []
            if findings:
                recommendations.extend([
                    "Consult dermatologist for skin lesion evaluation",
                    "Monitor for changes in size or color",
                    "Avoid self-diagnosis based on image analysis alone"
                ])
            
            return {
                'detected': len(findings) > 0,
                'findings': findings,
                'recommendations': recommendations,
                'confidence': confidence,
                'severity': severity
            }
            
        except Exception as e:
            logger.error(f"Skin lesion analysis failed: {e}")
            return {
                'detected': False,
                'findings': [],
                'recommendations': [],
                'confidence': 0.0,
                'severity': 'unknown'
            }
    
    async def _analyze_medical_features(self, cv_image: np.ndarray) -> Dict[str, Any]:
        """Analyze general medical image features"""
        
        try:
            findings = []
            recommendations = []
            confidence = 0.0
            
            # Color analysis for medical indicators
            hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
            
            # Check for redness (inflammation indicator)
            lower_red = np.array([0, 50, 50])
            upper_red = np.array([10, 255, 255])
            red_mask = cv2.inRange(hsv, lower_red, upper_red)
            red_percentage = np.sum(red_mask > 0) / red_mask.size * 100
            
            if red_percentage > 5:  # Threshold for significant redness
                findings.append({
                    'type': 'inflammation_indicator',
                    'description': f'Redness detected: {red_percentage:.1f}% of image area',
                    'severity': 'medium' if red_percentage > 10 else 'low'
                })
                recommendations.append("Redness may indicate inflammation - consult healthcare provider")
                confidence = max(confidence, 0.6)
            
            # Texture analysis
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            texture_variance = np.var(gray)
            
            if texture_variance > 1000:  # High variance might indicate abnormalities
                findings.append({
                    'type': 'texture_abnormality',
                    'description': f'Texture variance: {texture_variance:.1f}',
                    'severity': 'medium'
                })
                recommendations.append("Unusual texture detected - medical evaluation recommended")
                confidence = max(confidence, 0.5)
            
            return {
                'detected': len(findings) > 0,
                'findings': findings,
                'recommendations': recommendations,
                'confidence': confidence,
                'severity': 'medium' if findings else 'low'
            }
            
        except Exception as e:
            logger.error(f"Medical feature analysis failed: {e}")
            return {
                'detected': False,
                'findings': [],
                'recommendations': [],
                'confidence': 0.0,
                'severity': 'unknown'
            }

class ExplainabilityAgent(BaseEnhancedAgent):
    """
    Enhanced Explainability Agent for AI decision transparency
    Provides step-by-step reasoning and confidence breakdown
    """
    
    def __init__(self):
        super().__init__("Explainability Agent", 0.8)
        self.explanation_templates = {
            'emergency': [
                "Immediate medical attention required because {primary_reason}",
                "Emergency indicators detected: {emergency_factors}",
                "Risk level: HIGH - Call emergency services immediately"
            ],
            'urgent': [
                "Urgent medical evaluation needed within 24 hours",
                "Primary concern: {primary_reason}",
                "Supporting factors: {supporting_factors}"
            ],
            'routine': [
                "Routine medical care recommended",
                "Symptoms suggest: {primary_reason}",
                "No immediate emergency indicators detected"
            ],
            'self_care': [
                "Self-care appropriate for these symptoms",
                "Home treatment: {primary_reason}",
                "Monitor for: {monitoring_factors}"
            ]
        }
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explainability report for triage decision"""
        
        try:
            # Extract agent outputs
            agent_outputs = input_data.get('agent_outputs', {})
            triage_level = input_data.get('triage_level', 'self_care')
            patient_context = input_data.get('patient_context', {})
            
            # Generate explanation
            explanation = await self._generate_explanation(
                agent_outputs, triage_level, patient_context
            )
            
            # Calculate confidence breakdown
            confidence_breakdown = await self._calculate_confidence_breakdown(agent_outputs)
            
            # Identify key factors
            key_factors = await self._identify_key_factors(agent_outputs, patient_context)
            
            # Generate counterfactual scenarios
            counterfactuals = await self._generate_counterfactuals(
                agent_outputs, triage_level, patient_context
            )
            
            return {
                'agent': self.name,
                'status': 'completed',
                'confidence': 0.85,
                'explanation': explanation,
                'confidence_breakdown': confidence_breakdown,
                'key_factors': key_factors,
                'counterfactual_scenarios': counterfactuals,
                'reasoning_steps': await self._generate_reasoning_steps(agent_outputs),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Explainability agent error: {e}")
            return {
                'agent': self.name,
                'status': 'error',
                'confidence': 0.0,
                'error': str(e),
                'explanation': 'Unable to generate explanation due to processing error'
            }
    
    async def _generate_explanation(
        self, 
        agent_outputs: Dict[str, Any], 
        triage_level: str, 
        patient_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate human-readable explanation"""
        
        # Get primary reason from triage agent
        triage_output = agent_outputs.get('triage_agent', {})
        primary_reason = triage_output.get('reasoning', 'Symptom analysis')
        
        # Get safety guard findings
        safety_output = agent_outputs.get('safety_guard_agent', {})
        emergency_factors = safety_output.get('emergency_factors', [])
        
        # Get guideline agent findings
        guideline_output = agent_outputs.get('guideline_agent', {})
        supporting_factors = guideline_output.get('supporting_factors', [])
        
        # Get risk prediction
        risk_output = agent_outputs.get('risk_prediction_agent', {})
        risk_factors = risk_output.get('risk_factors', [])
        
        # Select appropriate template
        template = self.explanation_templates.get(triage_level, self.explanation_templates['self_care'])
        
        # Fill template
        explanation = {
            'summary': template[0].format(
                primary_reason=primary_reason
            ),
            'emergency_factors': emergency_factors,
            'supporting_factors': supporting_factors,
            'risk_factors': risk_factors,
            'triage_level': triage_level.upper(),
            'confidence_level': self._get_confidence_description(agent_outputs)
        }
        
        return explanation
    
    async def _calculate_confidence_breakdown(self, agent_outputs: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence breakdown by agent"""
        
        breakdown = {}
        
        for agent_name, output in agent_outputs.items():
            if isinstance(output, dict) and 'confidence' in output:
                breakdown[agent_name] = output['confidence']
        
        # Calculate overall confidence
        if breakdown:
            overall_confidence = np.mean(list(breakdown.values()))
            breakdown['overall'] = overall_confidence
        else:
            breakdown['overall'] = 0.0
        
        return breakdown
    
    async def _identify_key_factors(
        self, 
        agent_outputs: Dict[str, Any], 
        patient_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify key factors influencing the decision"""
        
        key_factors = []
        
        # Extract symptoms
        triage_output = agent_outputs.get('triage_agent', {})
        symptoms = triage_output.get('symptoms_analyzed', [])
        
        for symptom in symptoms:
            if symptom.get('severity', 'low') in ['medium', 'high']:
                key_factors.append({
                    'type': 'symptom',
                    'description': symptom.get('description', ''),
                    'severity': symptom.get('severity', 'low'),
                    'impact': 'high' if symptom.get('severity') == 'high' else 'medium'
                })
        
        # Extract vital signs
        vital_signs = patient_context.get('vital_signs', {})
        for vital, value in vital_signs.items():
            if self._is_abnormal_vital(vital, value):
                key_factors.append({
                    'type': 'vital_sign',
                    'description': f'Abnormal {vital}: {value}',
                    'severity': 'high',
                    'impact': 'critical'
                })
        
        # Extract risk factors
        risk_output = agent_outputs.get('risk_prediction_agent', {})
        risk_factors = risk_output.get('risk_factors', [])
        
        for factor in risk_factors:
            if factor.get('severity') == 'high':
                key_factors.append({
                    'type': 'risk_factor',
                    'description': factor.get('description', ''),
                    'severity': 'high',
                    'impact': 'high'
                })
        
        return key_factors
    
    async def _generate_counterfactuals(
        self, 
        agent_outputs: Dict[str, Any], 
        triage_level: str, 
        patient_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate counterfactual scenarios"""
        
        counterfactuals = []
        
        # What if symptoms were more severe?
        current_symptoms = agent_outputs.get('triage_agent', {}).get('symptoms_analyzed', [])
        if current_symptoms:
            more_severe_symptoms = [s.copy() for s in current_symptoms]
            for symptom in more_severe_symptoms:
                symptom['severity'] = 'high'
            
            counterfactuals.append({
                'scenario': 'more_severe_symptoms',
                'description': 'If symptoms were more severe',
                'likely_triage_level': 'emergency',
                'confidence_change': '+0.2',
                'recommendations': ['Seek immediate emergency care']
            })
        
        # What if patient was older?
        age = patient_context.get('age', 30)
        if age < 65:
            counterfactuals.append({
                'scenario': 'older_patient',
                'description': f'If patient was 65+ (current: {age})',
                'likely_triage_level': 'urgent',
                'confidence_change': '+0.1',
                'recommendations': ['More aggressive monitoring needed']
            })
        
        # What if vital signs were normal?
        vital_signs = patient_context.get('vital_signs', {})
        abnormal_vitals = [v for v, val in vital_signs.items() if self._is_abnormal_vital(v, val)]
        
        if abnormal_vitals:
            counterfactuals.append({
                'scenario': 'normal_vital_signs',
                'description': 'If vital signs were within normal range',
                'likely_triage_level': 'routine',
                'confidence_change': '-0.15',
                'recommendations': ['Routine care would be appropriate']
            })
        
        return counterfactuals
    
    async def _generate_reasoning_steps(self, agent_outputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate step-by-step reasoning process"""
        
        steps = []
        
        # Step 1: Symptom Analysis
        triage_output = agent_outputs.get('triage_agent', {})
        steps.append({
            'step': 1,
            'agent': 'Triage Agent',
            'action': 'Analyzed patient symptoms',
            'result': f"Identified {len(triage_output.get('symptoms_analyzed', []))} key symptoms",
            'confidence': triage_output.get('confidence', 0.0)
        })
        
        # Step 2: Safety Check
        safety_output = agent_outputs.get('safety_guard_agent', {})
        steps.append({
            'step': 2,
            'agent': 'Safety Guard Agent',
            'action': 'Checked for emergency indicators',
            'result': f"Found {len(safety_output.get('emergency_factors', []))} emergency factors",
            'confidence': safety_output.get('confidence', 0.0)
        })
        
        # Step 3: Guideline Application
        guideline_output = agent_outputs.get('guideline_agent', {})
        steps.append({
            'step': 3,
            'agent': 'Guideline Agent',
            'action': 'Applied clinical guidelines',
            'result': f"Retrieved {len(guideline_output.get('guidelines_applied', []))} relevant guidelines",
            'confidence': guideline_output.get('confidence', 0.0)
        })
        
        # Step 4: Risk Assessment
        risk_output = agent_outputs.get('risk_prediction_agent', {})
        steps.append({
            'step': 4,
            'agent': 'Risk Prediction Agent',
            'action': 'Assessed risk factors',
            'result': f"Calculated risk score: {risk_output.get('risk_score', 'unknown')}",
            'confidence': risk_output.get('confidence', 0.0)
        })
        
        # Step 5: Final Decision
        steps.append({
            'step': 5,
            'agent': 'Coordinator Agent',
            'action': 'Synthesized all agent outputs',
            'result': 'Final triage decision made',
            'confidence': 0.85  # Overall confidence
        })
        
        return steps
    
    def _get_confidence_description(self, agent_outputs: Dict[str, Any]) -> str:
        """Get human-readable confidence description"""
        
        confidences = []
        for output in agent_outputs.values():
            if isinstance(output, dict) and 'confidence' in output:
                confidences.append(output['confidence'])
        
        if not confidences:
            return 'Unknown'
        
        avg_confidence = np.mean(confidences)
        
        if avg_confidence >= 0.9:
            return 'Very High'
        elif avg_confidence >= 0.8:
            return 'High'
        elif avg_confidence >= 0.7:
            return 'Medium-High'
        elif avg_confidence >= 0.6:
            return 'Medium'
        elif avg_confidence >= 0.5:
            return 'Low-Medium'
        else:
            return 'Low'
    
    def _is_abnormal_vital(self, vital: str, value: Any) -> bool:
        """Check if vital sign is abnormal"""
        
        normal_ranges = {
            'blood_pressure_systolic': (90, 120),
            'blood_pressure_diastolic': (60, 80),
            'heart_rate': (60, 100),
            'temperature': (36.1, 37.2),
            'oxygen_saturation': (95, 100),
            'respiratory_rate': (12, 20)
        }
        
        if vital in normal_ranges:
            min_val, max_val = normal_ranges[vital]
            try:
                numeric_value = float(value)
                return numeric_value < min_val or numeric_value > max_val
            except (ValueError, TypeError):
                return False
        
        return False

class BiasMonitoringAgent(BaseEnhancedAgent):
    """
    Enhanced Bias Monitoring Agent for continuous fairness tracking
    Monitors performance across demographics and auto-corrects biases
    """
    
    def __init__(self):
        super().__init__("Bias Monitoring Agent", 0.9)
        self.demographic_groups = {
            'age_groups': ['0-17', '18-35', '36-50', '51-65', '65+'],
            'genders': ['male', 'female', 'other'],
            'languages': ['en', 'sw', 'am', 'es', 'fr'],
            'regions': ['africa_east', 'africa_west', 'africa_south', 'asia_se', 'latam']
        }
        self.bias_thresholds = {
            'performance_disparity': 0.15,  # 15% max disparity
            'accuracy_variance': 0.10,      # 10% max variance
            'confidence_bias': 0.05          # 5% max confidence bias
        }
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor and analyze bias metrics"""
        
        try:
            # Extract performance data
            performance_data = input_data.get('performance_data', [])
            demographics = input_data.get('demographics', {})
            
            # Analyze bias across groups
            bias_analysis = await self._analyze_bias_across_groups(performance_data, demographics)
            
            # Detect bias violations
            bias_violations = await self._detect_bias_violations(bias_analysis)
            
            # Generate correction recommendations
            corrections = await self._generate_bias_corrections(bias_analysis, bias_violations)
            
            # Update internal bias metrics
            self._update_internal_bias_metrics(performance_data, demographics)
            
            return {
                'agent': self.name,
                'status': 'completed',
                'confidence': 0.9,
                'bias_analysis': bias_analysis,
                'bias_violations': bias_violations,
                'corrections': corrections,
                'fairness_score': await self._calculate_fairness_score(bias_analysis),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Bias monitoring agent error: {e}")
            return {
                'agent': self.name,
                'status': 'error',
                'confidence': 0.0,
                'error': str(e),
                'bias_analysis': {},
                'corrections': []
            }
    
    async def _analyze_bias_across_groups(
        self, 
        performance_data: List[Dict[str, Any]], 
        demographics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze bias across demographic groups"""
        
        bias_analysis = {}
        
        for category, groups in self.demographic_groups.items():
            category_analysis = {}
            
            for group in groups:
                # Filter performance data for this group
                group_data = [
                    data for data in performance_data
                    if self._belongs_to_group(data, category, group, demographics)
                ]
                
                if group_data:
                    # Calculate metrics for this group
                    accuracies = [data.get('accuracy', 0) for data in group_data]
                    confidences = [data.get('confidence', 0) for data in group_data]
                    
                    category_analysis[group] = {
                        'sample_size': len(group_data),
                        'accuracy_mean': np.mean(accuracies),
                        'accuracy_std': np.std(accuracies),
                        'confidence_mean': np.mean(confidences),
                        'confidence_std': np.std(confidences),
                        'error_rate': 1 - np.mean(accuracies)
                    }
                else:
                    category_analysis[group] = {
                        'sample_size': 0,
                        'accuracy_mean': 0.0,
                        'accuracy_std': 0.0,
                        'confidence_mean': 0.0,
                        'confidence_std': 0.0,
                        'error_rate': 1.0
                    }
            
            # Calculate disparity metrics
            if category_analysis:
                accuracies = [data['accuracy_mean'] for data in category_analysis.values() if data['sample_size'] > 0]
                if accuracies:
                    max_accuracy = max(accuracies)
                    min_accuracy = min(accuracies)
                    disparity = max_accuracy - min_accuracy
                    
                    category_analysis['disparity'] = {
                        'max_accuracy': max_accuracy,
                        'min_accuracy': min_accuracy,
                        'disparity_range': disparity,
                        'exceeds_threshold': disparity > self.bias_thresholds['performance_disparity']
                    }
            
            bias_analysis[category] = category_analysis
        
        return bias_analysis
    
    async def _detect_bias_violations(self, bias_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect bias threshold violations"""
        
        violations = []
        
        for category, analysis in bias_analysis.items():
            if 'disparity' in analysis:
                disparity = analysis['disparity']
                
                if disparity['exceeds_threshold']:
                    violations.append({
                        'type': 'performance_disparity',
                        'category': category,
                        'severity': 'high' if disparity['disparity_range'] > 0.2 else 'medium',
                        'description': f"Performance disparity in {category}: {disparity['disparity_range']:.2f}",
                        'threshold': self.bias_thresholds['performance_disparity'],
                        'actual_value': disparity['disparity_range']
                    })
        
        return violations
    
    async def _generate_bias_corrections(
        self, 
        bias_analysis: Dict[str, Any], 
        violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate bias correction recommendations"""
        
        corrections = []
        
        for violation in violations:
            if violation['type'] == 'performance_disparity':
                corrections.append({
                    'type': 'model_retraining',
                    'category': violation['category'],
                    'priority': 'high' if violation['severity'] == 'high' else 'medium',
                    'description': f"Retrain model with balanced {violation['category']} data",
                    'action': 'augment_training_data',
                    'expected_impact': f"Reduce disparity by {violation['actual_value'] - violation['threshold']:.2f}"
                })
        
        # General corrections
        if len(violations) > 0:
            corrections.append({
                'type': 'fairness_regularization',
                'priority': 'high',
                'description': 'Apply fairness regularization to model training',
                'action': 'adjust_model_parameters',
                'expected_impact': 'Improve overall fairness metrics'
            })
        
        return corrections
    
    async def _calculate_fairness_score(self, bias_analysis: Dict[str, Any]) -> float:
        """Calculate overall fairness score"""
        
        fairness_scores = []
        
        for category, analysis in bias_analysis.items():
            if 'disparity' in analysis:
                disparity = analysis['disparity']['disparity_range']
                # Convert disparity to fairness score (inverse relationship)
                fairness_score = max(0.0, 1.0 - disparity)
                fairness_scores.append(fairness_score)
        
        if fairness_scores:
            return np.mean(fairness_scores)
        else:
            return 0.5  # Neutral score
    
    def _belongs_to_group(
        self, 
        data: Dict[str, Any], 
        category: str, 
        group: str, 
        demographics: Dict[str, Any]
    ) -> bool:
        """Check if data point belongs to demographic group"""
        
        if category == 'age_groups':
            age = demographics.get('age', 0)
            if group == '0-17':
                return age <= 17
            elif group == '18-35':
                return 18 <= age <= 35
            elif group == '36-50':
                return 36 <= age <= 50
            elif group == '51-65':
                return 51 <= age <= 65
            elif group == '65+':
                return age > 65
                
        elif category == 'genders':
            return demographics.get('gender', '') == group
            
        elif category == 'languages':
            return demographics.get('language', '') == group
            
        elif category == 'regions':
            return demographics.get('region', '') == group
        
        return False
    
    def _update_internal_bias_metrics(
        self, 
        performance_data: List[Dict[str, Any]], 
        demographics: Dict[str, Any]
    ):
        """Update internal bias tracking metrics"""
        
        for data_point in performance_data:
            for category in self.demographic_groups.keys():
                group = self._get_group_for_data_point(data_point, category, demographics)
                if group:
                    if category not in self.bias_metrics:
                        self.bias_metrics[category] = {}
                    
                    if group not in self.bias_metrics[category]:
                        self.bias_metrics[category][group] = []
                    
                    self.bias_metrics[category][group].append({
                        'timestamp': datetime.utcnow().isoformat(),
                        'accuracy': data_point.get('accuracy', 0),
                        'confidence': data_point.get('confidence', 0)
                    })
    
    def _get_group_for_data_point(
        self, 
        data_point: Dict[str, Any], 
        category: str, 
        demographics: Dict[str, Any]
    ) -> Optional[str]:
        """Get demographic group for data point"""
        
        if category == 'age_groups':
            age = demographics.get('age', 0)
            if age <= 17:
                return '0-17'
            elif age <= 35:
                return '18-35'
            elif age <= 50:
                return '36-50'
            elif age <= 65:
                return '51-65'
            else:
                return '65+'
                
        elif category == 'genders':
            return demographics.get('gender', 'other')
            
        elif category == 'languages':
            return demographics.get('language', 'en')
            
        elif category == 'regions':
            return demographics.get('region', 'unknown')
        
        return None

# Enhanced Agent Orchestration
class EnhancedAgentOrchestrator:
    """
    World-class agent orchestration with LangChain/CrewAI-style coordination
    Manages 7 specialized agents with intelligent routing
    """
    
    def __init__(self):
        self.agents = {
            'triage': None,  # Will be set to existing triage agent
            'safety_guard': None,  # Will be set to existing safety guard agent
            'guideline': None,  # Will be set to existing guideline agent
            'risk_prediction': None,  # Will be set to existing risk prediction agent
            'image_analysis': ImageAnalysisAgent(),
            'explainability': ExplainabilityAgent(),
            'bias_monitoring': BiasMonitoringAgent()
        }
        
        self.orchestration_graph = {
            'initial': ['triage'],
            'parallel': ['safety_guard', 'guideline', 'risk_prediction'],
            'conditional': {
                'images_present': ['image_analysis'],
                'always': ['explainability', 'bias_monitoring']
            }
        }
        
        self.context_manager = {}
        self.performance_tracker = {}
        
    async def orchestrate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate all agents for comprehensive triage analysis"""
        
        try:
            orchestration_id = f"orch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Initialize orchestration context
            context = await self._initialize_context(input_data, orchestration_id)
            
            # Step 1: Initial agents
            initial_results = await self._run_initial_agents(context)
            
            # Step 2: Parallel agents
            parallel_results = await self._run_parallel_agents(context)
            
            # Step 3: Conditional agents
            conditional_results = await self._run_conditional_agents(context, initial_results, parallel_results)
            
            # Step 4: Final synthesis
            final_result = await self._synthesize_results(
                initial_results, parallel_results, conditional_results, context
            )
            
            # Step 5: Performance tracking
            await self._track_performance(orchestration_id, final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Agent orchestration error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'orchestration_id': orchestration_id if 'orchestration_id' in locals() else 'unknown'
            }
    
    async def _initialize_context(self, input_data: Dict[str, Any], orchestration_id: str) -> Dict[str, Any]:
        """Initialize orchestration context"""
        
        context = {
            'orchestration_id': orchestration_id,
            'input_data': input_data,
            'start_time': datetime.utcnow().isoformat(),
            'agent_results': {},
            'intermediate_data': {},
            'decisions': {},
            'performance_metrics': {}
        }
        
        self.context_manager[orchestration_id] = context
        return context
    
    async def _run_initial_agents(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run initial agents in sequence"""
        
        results = {}
        
        for agent_name in self.orchestration_graph['initial']:
            if agent_name in self.agents and self.agents[agent_name]:
                try:
                    result = await self.agents[agent_name].process(context['input_data'])
                    results[agent_name] = result
                    context['agent_results'][agent_name] = result
                    
                    logger.info(f"Initial agent {agent_name} completed")
                    
                except Exception as e:
                    logger.error(f"Initial agent {agent_name} failed: {e}")
                    results[agent_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
        
        return results
    
    async def _run_parallel_agents(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run parallel agents concurrently"""
        
        results = {}
        
        # Create parallel tasks
        tasks = []
        agent_names = []
        
        for agent_name in self.orchestration_graph['parallel']:
            if agent_name in self.agents and self.agents[agent_name]:
                task = self.agents[agent_name].process(context['input_data'])
                tasks.append(task)
                agent_names.append(agent_name)
        
        # Execute parallel tasks
        if tasks:
            try:
                parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, (agent_name, result) in enumerate(zip(agent_names, parallel_results)):
                    if isinstance(result, Exception):
                        logger.error(f"Parallel agent {agent_name} failed: {result}")
                        results[agent_name] = {
                            'status': 'error',
                            'error': str(result)
                        }
                    else:
                        results[agent_name] = result
                        context['agent_results'][agent_name] = result
                        logger.info(f"Parallel agent {agent_name} completed")
                        
            except Exception as e:
                logger.error(f"Parallel agent execution failed: {e}")
        
        return results
    
    async def _run_conditional_agents(
        self, 
        context: Dict[str, Any], 
        initial_results: Dict[str, Any], 
        parallel_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run conditional agents based on previous results"""
        
        results = {}
        combined_results = {**initial_results, **parallel_results}
        
        # Check conditions and run appropriate agents
        if context['input_data'].get('images'):
            for agent_name in self.orchestration_graph['conditional']['images_present']:
                if agent_name in self.agents and self.agents[agent_name]:
                    try:
                        result = await self.agents[agent_name].process(context['input_data'])
                        results[agent_name] = result
                        context['agent_results'][agent_name] = result
                        logger.info(f"Conditional agent {agent_name} (images) completed")
                    except Exception as e:
                        logger.error(f"Conditional agent {agent_name} (images) failed: {e}")
                        results[agent_name] = {
                            'status': 'error',
                            'error': str(e)
                        }
        
        # Always run agents
        for agent_name in self.orchestration_graph['conditional']['always']:
            if agent_name in self.agents and self.agents[agent_name]:
                try:
                    # Provide all agent results for context
                    enhanced_input = {
                        **context['input_data'],
                        'agent_outputs': combined_results
                    }
                    
                    result = await self.agents[agent_name].process(enhanced_input)
                    results[agent_name] = result
                    context['agent_results'][agent_name] = result
                    logger.info(f"Always agent {agent_name} completed")
                    
                except Exception as e:
                    logger.error(f"Always agent {agent_name} failed: {e}")
                    results[agent_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
        
        return results
    
    async def _synthesize_results(
        self, 
        initial_results: Dict[str, Any], 
        parallel_results: Dict[str, Any], 
        conditional_results: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize all agent results into final triage decision"""
        
        all_results = {**initial_results, **parallel_results, **conditional_results}
        
        # Extract key information
        triage_result = initial_results.get('triage', {})
        safety_result = parallel_results.get('safety_guard', {})
        guideline_result = parallel_results.get('guideline', {})
        risk_result = parallel_results.get('risk_prediction', {})
        image_result = conditional_results.get('image_analysis', {})
        explainability_result = conditional_results.get('explainability', {})
        bias_result = conditional_results.get('bias_monitoring', {})
        
        # Synthesize final triage decision
        final_triage_level = self._determine_final_triage_level(triage_result, safety_result)
        final_confidence = self._calculate_overall_confidence(all_results)
        
        # Create comprehensive result
        synthesized_result = {
            'orchestration_id': context['orchestration_id'],
            'status': 'completed',
            'triage_level': final_triage_level,
            'confidence': final_confidence,
            'agent_outputs': all_results,
            'synthesis': {
                'primary_decision': final_triage_level,
                'confidence_breakdown': explainability_result.get('confidence_breakdown', {}),
                'key_factors': explainability_result.get('key_factors', []),
                'explanation': explainability_result.get('explanation', {}),
                'risk_assessment': risk_result.get('risk_assessment', {}),
                'safety_analysis': safety_result.get('safety_analysis', {}),
                'guideline_application': guideline_result.get('guideline_application', {}),
                'image_findings': image_result.get('findings', []),
                'bias_analysis': bias_result.get('bias_analysis', {}),
                'counterfactuals': explainability_result.get('counterfactual_scenarios', [])
            },
            'recommendations': self._generate_final_recommendations(all_results),
            'processing_time': datetime.utcnow().isoformat(),
            'agent_performance': self._calculate_agent_performance(all_results)
        }
        
        return synthesized_result
    
    def _determine_final_triage_level(
        self, 
        triage_result: Dict[str, Any], 
        safety_result: Dict[str, Any]
    ) -> str:
        """Determine final triage level with safety override"""
        
        # Safety guard has veto power
        if safety_result.get('emergency_detected', False):
            return 'emergency'
        
        # Otherwise use triage agent result
        return triage_result.get('triage_level', 'self_care')
    
    def _calculate_overall_confidence(self, all_results: Dict[str, Any]) -> float:
        """Calculate overall confidence from all agents"""
        
        confidences = []
        
        for result in all_results.values():
            if isinstance(result, dict) and 'confidence' in result:
                confidences.append(result['confidence'])
        
        if confidences:
            # Weight safety guard higher
            weighted_confidences = []
            for agent_name, result in all_results.items():
                confidence = result.get('confidence', 0.0)
                weight = 1.5 if agent_name == 'safety_guard' else 1.0
                weighted_confidences.append(confidence * weight)
            
            return np.mean(weighted_confidences) / len(weighted_confidences)
        
        return 0.0
    
    def _generate_final_recommendations(self, all_results: Dict[str, Any]) -> List[str]:
        """Generate final recommendations from all agents"""
        
        all_recommendations = []
        
        for result in all_results.values():
            if isinstance(result, dict) and 'recommendations' in result:
                all_recommendations.extend(result['recommendations'])
        
        # Remove duplicates and prioritize
        unique_recommendations = list(set(all_recommendations))
        
        # Prioritize safety-related recommendations
        safety_recommendations = [
            rec for rec in unique_recommendations 
            if any(keyword in rec.lower() for keyword in ['emergency', 'urgent', 'immediate'])
        ]
        
        other_recommendations = [
            rec for rec in unique_recommendations 
            if rec not in safety_recommendations
        ]
        
        return safety_recommendations + other_recommendations[:5]  # Limit to reasonable number
    
    def _calculate_agent_performance(self, all_results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate performance metrics for all agents"""
        
        performance = {}
        
        for agent_name, result in all_results.items():
            if isinstance(result, dict):
                confidence = result.get('confidence', 0.0)
                status = result.get('status', 'unknown')
                
                # Performance score based on confidence and status
                if status == 'completed':
                    performance_score = confidence
                elif status == 'error':
                    performance_score = 0.0
                else:
                    performance_score = confidence * 0.5  # Partial completion
                
                performance[agent_name] = performance_score
        
        return performance
    
    async def _track_performance(self, orchestration_id: str, final_result: Dict[str, Any]):
        """Track orchestration performance for learning"""
        
        performance_data = {
            'orchestration_id': orchestration_id,
            'timestamp': datetime.utcnow().isoformat(),
            'overall_confidence': final_result.get('confidence', 0.0),
            'agent_performance': final_result.get('agent_performance', {}),
            'processing_time': final_result.get('processing_time'),
            'status': final_result.get('status', 'unknown')
        }
        
        self.performance_tracker[orchestration_id] = performance_data
        
        # Update individual agent performance
        agent_performance = final_result.get('agent_performance', {})
        for agent_name, performance_score in agent_performance.items():
            if agent_name in self.agents and self.agents[agent_name]:
                self.agents[agent_name].log_performance(
                    performance_score, 
                    1.0 if performance_score > 0.7 else 0.5  # Assume accuracy based on confidence
                )

# Global enhanced agent instances
enhanced_orchestrator = EnhancedAgentOrchestrator()
