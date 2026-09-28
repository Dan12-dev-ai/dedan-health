import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import json
import logging

from models_v2 import (
    RiskSentinelInput, RiskSentinelOutput, RiskScore,
    ChronicCareData, HomeMeasurement, ChronicCareCheckIn
)

# Configure logging
logger = logging.getLogger(__name__)

class RiskSentinel:
    """
    DEDAN Risk Sentinel - Predictive early warning system for chronic patients.
    Monitors symptom evolution, medication adherence, and home measurements.
    """
    
    def __init__(self):
        self.anomaly_detector = None
        self.scaler = None
        self.risk_thresholds = {
            'diabetes': {'glucose_high': 250, 'glucose_critical': 400},
            'hypertension': {'bp_high': 160/100, 'bp_critical': 180/110},
            'asthma': {'peak_flow_low': 200, 'peak_flow_critical': 150},
            'heart_disease': {'hr_high': 100, 'hr_critical': 120}
        }
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained anomaly detection models."""
        try:
            # Try to load existing models
            self.anomaly_detector = joblib.load('models/risk_anomaly_detector.pkl')
            self.scaler = joblib.load('models/risk_scaler.pkl')
            logger.info("Risk Sentinel models loaded successfully")
        except FileNotFoundError:
            # Initialize new models if not found
            self.anomaly_detector = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42
            )
            self.scaler = StandardScaler()
            logger.info("Initialized new Risk Sentinel models")
    
    async def analyze_risk(self, risk_input: RiskSentinelInput) -> RiskSentinelOutput:
        """
        Main risk analysis method - orchestrates comprehensive risk assessment.
        """
        
        try:
            logger.info(f"Starting Risk Sentinel analysis for patient {risk_input.patient_id}")
            
            # Step 1: Analyze symptom evolution
            symptom_trends = self._analyze_symptom_evolution(risk_input)
            
            # Step 2: Analyze medication adherence
            adherence_analysis = self._analyze_medication_adherence(risk_input)
            
            # Step 3: Analyze measurement trends
            measurement_trends = self._analyze_measurement_trends(risk_input)
            
            # Step 4: Detect anomalies
            anomaly_analysis = self._detect_anomalies(risk_input)
            
            # Step 5: Calculate comprehensive risk score
            risk_assessment = self._calculate_comprehensive_risk(
                symptom_trends, adherence_analysis, measurement_trends, anomaly_analysis
            )
            
            # Step 6: Generate alerts and recommendations
            alerts = self._generate_risk_alerts(risk_assessment, risk_input)
            recommendations = self._generate_risk_recommendations(risk_assessment, risk_input)
            
            # Step 7: Determine escalation level
            escalation_level = self._determine_escalation_level(risk_assessment, alerts)
            
            # Create output
            output = RiskSentinelOutput(
                patient_id=risk_input.patient_id,
                risk_status=risk_assessment['status'],
                risk_score=risk_assessment['score'],
                risk_trend=risk_assessment['trend'],
                alerts=alerts,
                recommendations=recommendations,
                escalation_level=escalation_level,
                last_updated=datetime.utcnow()
            )
            
            logger.info(f"Risk Sentinel analysis completed for patient {risk_input.patient_id}")
            return output
            
        except Exception as e:
            logger.error(f"Risk Sentinel analysis error: {str(e)}")
            raise
    
    def _analyze_symptom_evolution(self, risk_input: RiskSentinelInput) -> Dict[str, Any]:
        """Analyze symptom evolution over time."""
        
        check_ins = risk_input.recent_check_ins
        if not check_ins:
            return {"trend": "stable", "severity": "low", "progression": "none"}
        
        # Extract symptom data
        symptom_timeline = []
        for check_in in check_ins:
            symptom_timeline.append({
                'date': datetime.fromisoformat(check_in.check_in_date.replace('Z', '+00:00')),
                'symptoms': check_in.symptoms,
                'severity': len(check_in.symptoms)  # Proxy for severity
            })
        
        # Sort by date
        symptom_timeline.sort(key=lambda x: x['date'])
        
        # Calculate trends
        if len(symptom_timeline) < 2:
            return {"trend": "insufficient_data", "severity": "low", "progression": "none"}
        
        # Recent vs older comparison
        recent_period = symptom_timeline[-3:] if len(symptom_timeline) >= 3 else symptom_timeline[-1:]
        older_period = symptom_timeline[:-3] if len(symptom_timeline) >= 6 else symptom_timeline[:-1]
        
        recent_avg_severity = np.mean([s['severity'] for s in recent_period])
        older_avg_severity = np.mean([s['severity'] for s in older_period]) if older_period else recent_avg_severity
        
        # Determine trend
        trend = "stable"
        if recent_avg_severity > older_avg_severity * 1.2:
            trend = "worsening"
        elif recent_avg_severity < older_avg_severity * 0.8:
            trend = "improving"
        
        # Check for new severe symptoms
        recent_symptoms = set()
        for check_in in recent_period:
            recent_symptoms.update(check_in.symptoms)
        
        older_symptoms = set()
        for check_in in older_period:
            older_symptoms.update(check_in.symptoms)
        
        new_symptoms = recent_symptoms - older_symptoms
        progression = "new_symptoms" if new_symptoms else "stable"
        
        return {
            "trend": trend,
            "severity": "high" if recent_avg_severity > 5 else "medium" if recent_avg_severity > 2 else "low",
            "progression": progression,
            "new_symptoms": list(new_symptoms),
            "data_points": len(symptom_timeline)
        }
    
    def _analyze_medication_adherence(self, risk_input: RiskSentinelInput) -> Dict[str, Any]:
        """Analyze medication adherence patterns."""
        
        check_ins = risk_input.recent_check_ins
        if not check_ins:
            return {"adherence_rate": 1.0, "trend": "stable", "concerns": []}
        
        # Calculate adherence
        total_check_ins = len(check_ins)
        taken_check_ins = sum(1 for check_in in check_ins if check_in.medication_taken)
        adherence_rate = taken_check_ins / total_check_ins if total_check_ins > 0 else 1.0
        
        # Time-based adherence analysis
        adherence_by_time = {}
        for check_in in check_ins:
            date = datetime.fromisoformat(check_in.check_in_date.replace('Z', '+00:00'))
            hour = date.hour
            
            if hour not in adherence_by_time:
                adherence_by_time[hour] = {'taken': 0, 'total': 0}
            
            adherence_by_time[hour]['total'] += 1
            if check_in.medication_taken:
                adherence_by_time[hour]['taken'] += 1
        
        # Calculate rates by time
        for hour, data in adherence_by_time.items():
            data['rate'] = data['taken'] / data['total'] if data['total'] > 0 else 0
        
        # Identify adherence concerns
        concerns = []
        if adherence_rate < 0.5:
            concerns.append("critical_non_adherence")
        elif adherence_rate < 0.8:
            concerns.append("poor_adherence")
        
        # Check for time-based patterns
        low_adherence_hours = [hour for hour, data in adherence_by_time.items() if data.get('rate', 0) < 0.5]
        if low_adherence_hours:
            concerns.append(f"time_based_non_adherence: {low_adherence_hours}")
        
        # Determine trend
        recent_adherence = adherence_by_time.get(8, {}).get('rate', 0)  # Morning dose
        overall_trend = "stable"
        if recent_adherence < 0.5:
            overall_trend = "declining"
        elif recent_adherence > 0.9:
            overall_trend = "improving"
        
        return {
            "adherence_rate": adherence_rate,
            "trend": overall_trend,
            "concerns": concerns,
            "time_patterns": adherence_by_time,
            "total_check_ins": total_check_ins
        }
    
    def _analyze_measurement_trends(self, risk_input: RiskSentinelInput) -> Dict[str, Any]:
        """Analyze home measurement trends."""
        
        measurements = risk_input.recent_measurements
        if not measurements:
            return {"trend": "no_data", "concerns": []}
        
        # Group measurements by type
        measurement_groups = {}
        for measurement in measurements:
            m_type = measurement.measurement_type
            if m_type not in measurement_groups:
                measurement_groups[m_type] = []
            measurement_groups[m_type].append({
                'value': measurement.value,
                'timestamp': measurement.timestamp,
                'unit': measurement.unit
            })
        
        # Analyze each measurement type
        trends = {}
        concerns = []
        
        for m_type, group in measurement_groups.items():
            if len(group) < 2:
                trends[m_type] = {"trend": "insufficient_data", "current": None}
                continue
            
            # Sort by timestamp
            group.sort(key=lambda x: x['timestamp'])
            
            # Calculate trend
            values = [m['value'] for m in group]
            recent_avg = np.mean(values[-3:]) if len(values) >= 3 else values[-1]
            older_avg = np.mean(values[:-3]) if len(values) >= 6 else np.mean(values[:-1])
            
            trend = "stable"
            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"
            
            current_value = values[-1]
            
            # Check against thresholds
            type_concerns = []
            if m_type in self.risk_thresholds:
                thresholds = self.risk_thresholds[m_type]
                
                if 'glucose' in m_type.lower():
                    if current_value > thresholds.get('glucose_critical', 400):
                        type_concerns.append("critical_glucose")
                    elif current_value > thresholds.get('glucose_high', 250):
                        type_concerns.append("high_glucose")
                
                elif 'blood_pressure' in m_type.lower():
                    # Handle BP measurements (systolic/diastolic)
                    if isinstance(current_value, dict):
                        systolic = current_value.get('systolic', 0)
                        diastolic = current_value.get('diastolic', 0)
                        
                        if systolic > thresholds.get('bp_critical', [180])[0]:
                            type_concerns.append("critical_systolic_bp")
                        if diastolic > thresholds.get('bp_critical', [110])[1]:
                            type_concerns.append("critical_diastolic_bp")
                
                elif 'heart_rate' in m_type.lower():
                    if current_value > thresholds.get('hr_critical', 120):
                        type_concerns.append("critical_heart_rate")
                    elif current_value > thresholds.get('hr_high', 100):
                        type_concerns.append("high_heart_rate")
            
            trends[m_type] = {
                "trend": trend,
                "current": current_value,
                "average": np.mean(values),
                "concerns": type_concerns,
                "data_points": len(values)
            }
            
            concerns.extend(type_concerns)
        
        return {
            "trend": trends,
            "concerns": concerns,
            "measurement_types": list(measurement_groups.keys())
        }
    
    def _detect_anomalies(self, risk_input: RiskSentinelInput) -> Dict[str, Any]:
        """Detect anomalies in patient data using ML."""
        
        try:
            # Prepare features for anomaly detection
            features = self._prepare_anomaly_features(risk_input)
            if not features or len(features) < 5:
                return {"anomalies": [], "anomaly_score": 0.0}
            
            # Scale features
            features_scaled = self.scaler.fit_transform([features])
            
            # Detect anomalies
            anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
            is_anomaly = self.anomaly_detector.predict(features_scaled)[0] == -1
            
            # If we have enough data, update the model
            if len(features) >= 10:
                self._update_anomaly_model(features)
            
            return {
                "anomalies": ["data_pattern_anomaly"] if is_anomaly else [],
                "anomaly_score": float(abs(anomaly_score)),
                "features_used": len(features)
            }
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return {"anomalies": [], "anomaly_score": 0.0}
    
    def _prepare_anomaly_features(self, risk_input: RiskSentinelInput) -> List[float]:
        """Prepare features for anomaly detection."""
        
        features = []
        
        # Symptom features
        if risk_input.recent_check_ins:
            symptom_counts = [len(check_in.symptoms) for check_in in risk_input.recent_check_ins]
            features.extend([
                np.mean(symptom_counts),
                np.std(symptom_counts),
                max(symptom_counts) if symptom_counts else 0
            ])
        
        # Adherence features
        if risk_input.recent_check_ins:
            adherence_rates = [1.0 if check_in.medication_taken else 0.0 for check_in in risk_input.recent_check_ins]
            features.extend([
                np.mean(adherence_rates),
                np.std(adherence_rates),
                min(adherence_rates) if adherence_rates else 0.0
            ])
        
        # Measurement features
        if risk_input.recent_measurements:
            # Group by measurement type
            measurement_values = {}
            for measurement in risk_input.recent_measurements:
                m_type = measurement.measurement_type
                if m_type not in measurement_values:
                    measurement_values[m_type] = []
                measurement_values[m_type].append(measurement.value)
            
            # Add statistical features for each measurement type
            for m_type, values in measurement_values.items():
                features.extend([
                    np.mean(values),
                    np.std(values),
                    max(values) - min(values)  # Range
                ])
        
        return features
    
    def _update_anomaly_model(self, new_features: List[float]):
        """Update anomaly detection model with new data."""
        try:
            # This would implement incremental learning
            # For now, just log that we have new data
            logger.info(f"Updating anomaly model with {len(new_features)} features")
        except Exception as e:
            logger.error(f"Failed to update anomaly model: {e}")
    
    def _calculate_comprehensive_risk(
        self,
        symptom_trends: Dict[str, Any],
        adherence_analysis: Dict[str, Any],
        measurement_trends: Dict[str, Any],
        anomaly_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk assessment."""
        
        risk_score = 0
        risk_factors = []
        
        # Symptom-based risk
        if symptom_trends.get('trend') == 'worsening':
            risk_score += 3
            risk_factors.append("worsening_symptoms")
        elif symptom_trends.get('severity') == 'high':
            risk_score += 2
            risk_factors.append("severe_symptoms")
        
        # Adherence-based risk
        adherence_rate = adherence_analysis.get('adherence_rate', 1.0)
        if adherence_rate < 0.5:
            risk_score += 3
            risk_factors.append("critical_non_adherence")
        elif adherence_rate < 0.8:
            risk_score += 1
            risk_factors.append("poor_adherence")
        
        # Measurement-based risk
        measurement_concerns = measurement_trends.get('concerns', [])
        risk_score += len(measurement_concerns)
        risk_factors.extend(measurement_concerns)
        
        # Anomaly-based risk
        if anomaly_analysis.get('anomalies'):
            risk_score += 2
            risk_factors.append("anomalous_patterns")
        
        # Determine overall risk level
        if risk_score >= 6:
            risk_level = RiskScore.HIGH
            status = "escalate"
        elif risk_score >= 3:
            risk_level = RiskScore.MEDIUM
            status = "monitor"
        else:
            risk_level = RiskScore.LOW
            status = "stable"
        
        # Determine overall trend
        trends = [symptom_trends.get('trend', 'stable')]
        if adherence_analysis.get('trend') != 'stable':
            trends.append(adherence_analysis['trend'])
        
        overall_trend = "worsening" if 'worsening' in trends else "stable"
        
        return {
            "score": risk_level,
            "status": status,
            "trend": overall_trend,
            "risk_factors": risk_factors,
            "numerical_score": risk_score
        }
    
    def _generate_risk_alerts(self, risk_assessment: Dict[str, Any], risk_input: RiskSentinelInput) -> List[str]:
        """Generate risk alerts based on assessment."""
        
        alerts = []
        
        if risk_assessment['status'] == 'escalate':
            alerts.append("HIGH RISK: Immediate medical attention required")
        
        # Specific alerts based on risk factors
        for factor in risk_assessment['risk_factors']:
            if factor == "critical_glucose":
                alerts.append("CRITICAL: Blood glucose level dangerously high")
            elif factor == "critical_systolic_bp":
                alerts.append("CRITICAL: Systolic blood pressure at dangerous level")
            elif factor == "critical_diastolic_bp":
                alerts.append("CRITICAL: Diastolic blood pressure at dangerous level")
            elif factor == "critical_heart_rate":
                alerts.append("CRITICAL: Heart rate abnormally high")
            elif factor == "worsening_symptoms":
                alerts.append("WARNING: Symptoms are worsening over time")
            elif factor == "critical_non_adherence":
                alerts.append("URGENT: Critical medication non-adherence detected")
            elif factor == "anomalous_patterns":
                alerts.append("ALERT: Unusual health patterns detected")
        
        return alerts
    
    def _generate_risk_recommendations(self, risk_assessment: Dict[str, Any], risk_input: RiskSentinelInput) -> List[str]:
        """Generate risk-based recommendations."""
        
        recommendations = []
        risk_level = risk_assessment['score']
        
        # Base recommendations by risk level
        if risk_level == RiskScore.HIGH:
            recommendations.extend([
                "Contact healthcare provider immediately",
                "Go to emergency department if symptoms severe",
                "Take all emergency medications as prescribed",
                "Have someone stay with you until help arrives"
            ])
        elif risk_level == RiskScore.MEDIUM:
            recommendations.extend([
                "Schedule urgent medical appointment",
                "Increase monitoring frequency",
                "Review medication effectiveness",
                "Prepare for potential escalation"
            ])
        else:  # LOW risk
            recommendations.extend([
                "Continue current care plan",
                "Maintain medication adherence",
                "Schedule routine follow-up",
                "Monitor for any changes"
            ])
        
        # Factor-specific recommendations
        for factor in risk_assessment['risk_factors']:
            if "glucose" in factor:
                recommendations.extend([
                    "Check blood glucose immediately",
                    "Review diabetes management plan",
                    "Avoid high-sugar foods"
                ])
            elif "blood_pressure" in factor:
                recommendations.extend([
                    "Check blood pressure immediately",
                    "Take antihypertensive medication",
                    "Reduce sodium intake",
                    "Rest and avoid stress"
                ])
            elif "adherence" in factor:
                recommendations.extend([
                    "Set up medication reminders",
                    "Use pill organizers",
                    "Ask family for support",
                    "Identify adherence barriers"
                ])
        
        return list(set(recommendations))[:8]  # Limit to 8 recommendations
    
    def _determine_escalation_level(self, risk_assessment: Dict[str, Any], alerts: List[str]) -> Optional[str]:
        """Determine appropriate escalation level."""
        
        if risk_assessment['score'] == RiskScore.HIGH:
            return "emergency"
        elif risk_assessment['score'] == RiskScore.MEDIUM:
            return "urgent"
        elif len(alerts) >= 3:
            return "monitor_closely"
        else:
            return None
    
    def save_models(self):
        """Save trained models for future use."""
        try:
            joblib.dump(self.anomaly_detector, 'models/risk_anomaly_detector.pkl')
            joblib.dump(self.scaler, 'models/risk_scaler.pkl')
            logger.info("Risk Sentinel models saved successfully")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")

# Global instance
risk_sentinel = RiskSentinel()
