import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import logging

from models_v2 import (
    TriageLevel, RiskScore, Language, BiasMetrics, SafetyMetrics
)

# Configure logging
logger = logging.getLogger(__name__)

class SafetyBiasLayer:
    """
    DEDAN Safety & Bias Layer - Monitors and mitigates safety issues and algorithmic bias.
    Tracks false negatives, over-referrals, and demographic performance disparities.
    """
    
    def __init__(self):
        self.safety_logs = []
        self.bias_metrics = {}
        self.performance_thresholds = {
            'false_negative_rate_max': 0.05,  # 5% max false negative rate
            'over_referral_rate_max': 0.15,  # 15% max over-referral rate
            'accuracy_min': 0.80,  # 80% minimum accuracy
            'bias_disparity_max': 0.10  # 10% max disparity between groups
        }
        self.demographic_groups = {
            'age_groups': ['0-17', '18-35', '36-50', '51-65', '65+'],
            'genders': ['male', 'female', 'other'],
            'languages': [lang.value for lang in Language],
            'regions': ['africa_east', 'africa_west', 'africa_south', 'asia_se', 'latam']
        }
        
        logger.info("Safety & Bias Layer initialized")
    
    async def log_false_negative(
        self,
        session_id: str,
        original_triage: TriageLevel,
        actual_outcome: TriageLevel,
        patient_demographics: Dict[str, Any],
        symptoms: str,
        feedback_data: Dict[str, Any]
    ) -> bool:
        """Log false negative emergency cases."""
        
        try:
            # Check if this is actually a false negative
            is_false_negative = (
                original_triage in ['self_care', 'routine'] and
                actual_outcome in ['emergency', 'urgent']
            )
            
            if not is_false_negative:
                return False
            
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'session_id': session_id,
                'type': 'false_negative',
                'original_triage': original_triage,
                'actual_outcome': actual_outcome,
                'severity': 'critical' if actual_outcome == 'emergency' else 'high',
                'patient_demographics': patient_demographics,
                'symptoms': symptoms,
                'feedback_data': feedback_data,
                'impact_score': self._calculate_impact_score(original_triage, actual_outcome)
            }
            
            self.safety_logs.append(log_entry)
            
            # Trigger immediate safety alert
            await self._trigger_safety_alert(log_entry)
            
            logger.warning(f"False negative logged: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log false negative: {e}")
            return False
    
    async def log_over_referral(
        self,
        session_id: str,
        original_triage: TriageLevel,
        actual_outcome: TriageLevel,
        patient_demographics: Dict[str, Any],
        referral_reason: str,
        feedback_data: Dict[str, Any]
    ) -> bool:
        """Log over-referral cases."""
        
        try:
            # Check if this is actually an over-referral
            is_over_referral = (
                original_triage in ['emergency', 'urgent'] and
                actual_outcome in ['routine', 'self_care']
            )
            
            if not is_over_referral:
                return False
            
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'session_id': session_id,
                'type': 'over_referral',
                'original_triage': original_triage,
                'actual_outcome': actual_outcome,
                'severity': 'medium',
                'patient_demographics': patient_demographics,
                'referral_reason': referral_reason,
                'feedback_data': feedback_data,
                'impact_score': self._calculate_impact_score(original_triage, actual_outcome)
            }
            
            self.safety_logs.append(log_entry)
            
            logger.warning(f"Over-referral logged: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log over-referral: {e}")
            return False
    
    async def log_bias_incident(
        self,
        session_id: str,
        predicted_triage: TriageLevel,
        actual_outcome: TriageLevel,
        patient_demographics: Dict[str, Any],
        bias_type: str,
        description: str
    ) -> bool:
        """Log bias-related incidents."""
        
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'session_id': session_id,
                'type': 'bias_incident',
                'predicted_triage': predicted_triage,
                'actual_outcome': actual_outcome,
                'bias_type': bias_type,
                'severity': 'medium',
                'patient_demographics': patient_demographics,
                'description': description,
                'impact_score': self._calculate_impact_score(predicted_triage, actual_outcome)
            }
            
            self.safety_logs.append(log_entry)
            
            logger.warning(f"Bias incident logged: {session_id} - {bias_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log bias incident: {e}")
            return False
    
    async def calculate_bias_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Calculate bias metrics across demographic groups."""
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_logs = [
                log for log in self.safety_logs
                if datetime.fromisoformat(log['timestamp']) >= cutoff_date
            ]
            
            if not recent_logs:
                return {"error": "Insufficient data for bias analysis"}
            
            # Group logs by demographic categories
            demographic_performance = {}
            
            for log in recent_logs:
                demographics = log.get('patient_demographics', {})
                
                # Age group analysis
                age = demographics.get('age', 0)
                age_group = self._get_age_group(age)
                
                # Language analysis
                language = demographics.get('language', 'en')
                
                # Gender analysis
                gender = demographics.get('sex', 'other')
                
                # Region analysis
                location = demographics.get('location', '')
                region = self._get_region(location)
                
                # Calculate performance for each group
                for category, value in [
                    ('age_group', age_group),
                    ('language', language),
                    ('gender', gender),
                    ('region', region)
                ]:
                    if category not in demographic_performance:
                        demographic_performance[category] = {}
                    
                    if value not in demographic_performance[category]:
                        demographic_performance[category][value] = {
                            'total_cases': 0,
                            'correct_predictions': 0,
                            'false_negatives': 0,
                            'over_referrals': 0
                        }
                    
                    # Update metrics
                    perf = demographic_performance[category][value]
                    perf['total_cases'] += 1
                    
                    predicted = log.get('predicted_triage') or log.get('original_triage')
                    actual = log.get('actual_outcome')
                    
                    if predicted == actual:
                        perf['correct_predictions'] += 1
                    
                    # Check for false negatives
                    if (predicted in ['self_care', 'routine'] and 
                        actual in ['emergency', 'urgent']):
                        perf['false_negatives'] += 1
                    
                    # Check for over-referrals
                    if (predicted in ['emergency', 'urgent'] and 
                        actual in ['self_care', 'routine']):
                        perf['over_referrals'] += 1
            
            # Calculate bias metrics
            bias_analysis = {}
            
            for category, groups in demographic_performance.items():
                bias_analysis[category] = {}
                
                # Calculate metrics for each group
                group_metrics = {}
                for group, perf in groups.items():
                    if perf['total_cases'] == 0:
                        continue
                    
                    accuracy = perf['correct_predictions'] / perf['total_cases']
                    false_negative_rate = perf['false_negatives'] / perf['total_cases']
                    over_referral_rate = perf['over_referrals'] / perf['total_cases']
                    
                    group_metrics[group] = {
                        'accuracy': accuracy,
                        'false_negative_rate': false_negative_rate,
                        'over_referral_rate': over_referral_rate,
                        'sample_size': perf['total_cases']
                    }
                
                # Calculate disparities
                if len(group_metrics) > 1:
                    accuracies = [metrics['accuracy'] for metrics in group_metrics.values()]
                    max_accuracy = max(accuracies)
                    min_accuracy = min(accuracies)
                    
                    disparity = max_accuracy - min_accuracy
                    
                    bias_analysis[category] = {
                        'group_metrics': group_metrics,
                        'max_disparity': disparity,
                        'threshold_exceeded': disparity > self.performance_thresholds['bias_disparity_max']
                    }
            
            return bias_analysis
            
        except Exception as e:
            logger.error(f"Failed to calculate bias metrics: {e}")
            return {"error": "Bias calculation failed"}
    
    async def calculate_safety_metrics(self, days: int = 30) -> SafetyMetrics:
        """Calculate overall safety metrics."""
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_logs = [
                log for log in self.safety_logs
                if datetime.fromisoformat(log['timestamp']) >= cutoff_date
            ]
            
            if not recent_logs:
                return SafetyMetrics(
                    total_cases=0,
                    false_negatives=0,
                    over_referrals=0,
                    missed_risk_cases=0,
                    emergency_detection_accuracy=0.0,
                    overall_accuracy=0.0
                )
            
            # Count different types of incidents
            total_cases = len(recent_logs)
            false_negatives = len([log for log in recent_logs if log.get('type') == 'false_negative'])
            over_referrals = len([log for log in recent_logs if log.get('type') == 'over_referral'])
            missed_risk_cases = len([log for log in recent_logs if log.get('type') == 'missed_risk'])
            
            # Calculate accuracy metrics
            correct_predictions = 0
            emergency_correct = 0
            total_emergency = 0
            
            for log in recent_logs:
                predicted = log.get('predicted_triage') or log.get('original_triage')
                actual = log.get('actual_outcome')
                
                if predicted == actual:
                    correct_predictions += 1
                
                if actual == 'emergency':
                    total_emergency += 1
                    if predicted == 'emergency':
                        emergency_correct += 1
            
            overall_accuracy = correct_predictions / total_cases if total_cases > 0 else 0.0
            emergency_detection_accuracy = emergency_correct / total_emergency if total_emergency > 0 else 0.0
            
            safety_metrics = SafetyMetrics(
                total_cases=total_cases,
                false_negatives=false_negatives,
                over_referrals=over_referrals,
                missed_risk_cases=missed_risk_cases,
                emergency_detection_accuracy=emergency_detection_accuracy,
                overall_accuracy=overall_accuracy
            )
            
            # Check if thresholds are exceeded
            await self._check_safety_thresholds(safety_metrics)
            
            return safety_metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate safety metrics: {e}")
            return SafetyMetrics(
                total_cases=0,
                false_negatives=0,
                over_referrals=0,
                missed_risk_cases=0,
                emergency_detection_accuracy=0.0,
                overall_accuracy=0.0
            )
    
    async def generate_bias_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive bias and safety report."""
        
        try:
            bias_metrics = await self.calculate_bias_metrics(days)
            safety_metrics = await self.calculate_safety_metrics(days)
            
            # Generate recommendations
            recommendations = await self._generate_bias_recommendations(bias_metrics, safety_metrics)
            
            report = {
                'report_date': datetime.utcnow().isoformat(),
                'period_days': days,
                'safety_metrics': safety_metrics.dict(),
                'bias_metrics': bias_metrics,
                'thresholds': self.performance_thresholds,
                'recommendations': recommendations,
                'summary': self._generate_executive_summary(bias_metrics, safety_metrics)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate bias report: {e}")
            return {"error": "Report generation failed"}
    
    async def _trigger_safety_alert(self, log_entry: Dict[str, Any]):
        """Trigger immediate safety alerts for critical issues."""
        
        try:
            severity = log_entry.get('severity', 'medium')
            
            if severity == 'critical':
                # Trigger immediate alert
                alert_data = {
                    'type': 'safety_alert',
                    'severity': 'critical',
                    'session_id': log_entry['session_id'],
                    'message': f"CRITICAL SAFETY ISSUE: {log_entry.get('type', 'unknown')}",
                    'timestamp': datetime.utcnow().isoformat(),
                    'requires_immediate_action': True
                }
                
                # This would integrate with alerting systems
                logger.critical(f"SAFETY ALERT: {alert_data}")
                
                # Trigger model retraining if needed
                if log_entry.get('type') == 'false_negative':
                    await self._trigger_model_retraining('emergency_detection')
            
        except Exception as e:
            logger.error(f"Failed to trigger safety alert: {e}")
    
    async def _check_safety_thresholds(self, safety_metrics: SafetyMetrics):
        """Check if safety thresholds are exceeded."""
        
        try:
            alerts = []
            
            # Check false negative rate
            if safety_metrics.total_cases > 0:
                false_negative_rate = safety_metrics.false_negatives / safety_metrics.total_cases
                if false_negative_rate > self.performance_thresholds['false_negative_rate_max']:
                    alerts.append({
                        'type': 'threshold_exceeded',
                        'metric': 'false_negative_rate',
                        'current': false_negative_rate,
                        'threshold': self.performance_thresholds['false_negative_rate_max'],
                        'severity': 'high'
                    })
            
            # Check over-referral rate
            over_referral_rate = safety_metrics.over_referrals / safety_metrics.total_cases
            if over_referral_rate > self.performance_thresholds['over_referral_rate_max']:
                alerts.append({
                    'type': 'threshold_exceeded',
                    'metric': 'over_referral_rate',
                    'current': over_referral_rate,
                    'threshold': self.performance_thresholds['over_referral_rate_max'],
                    'severity': 'medium'
                })
            
            # Check accuracy
            if safety_metrics.overall_accuracy < self.performance_thresholds['accuracy_min']:
                alerts.append({
                    'type': 'threshold_exceeded',
                    'metric': 'overall_accuracy',
                    'current': safety_metrics.overall_accuracy,
                    'threshold': self.performance_thresholds['accuracy_min'],
                    'severity': 'high'
                })
            
            # Log alerts
            for alert in alerts:
                logger.warning(f"SAFETY THRESHOLD EXCEEDED: {alert}")
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check safety thresholds: {e}")
            return []
    
    async def _generate_bias_recommendations(
        self,
        bias_metrics: Dict[str, Any],
        safety_metrics: SafetyMetrics
    ) -> List[str]:
        """Generate recommendations based on bias and safety analysis."""
        
        recommendations = []
        
        # Safety-based recommendations
        if safety_metrics.false_negatives > 0:
            recommendations.append("Review emergency detection rules and training data")
            recommendations.append("Implement stricter safety guard parameters")
        
        if safety_metrics.over_referrals > 0:
            recommendations.append("Review triage escalation criteria")
            recommendations.append("Add conservative triage rules for high-risk symptoms")
        
        if safety_metrics.emergency_detection_accuracy < 0.90:
            recommendations.append("Retrain emergency detection models with recent false negative cases")
        
        # Bias-based recommendations
        for category, analysis in bias_metrics.items():
            if 'error' in analysis:
                continue
                
            if analysis.get('threshold_exceeded', False):
                recommendations.append(f"Address {category} bias - disparity exceeds {self.performance_thresholds['bias_disparity_max']:.0%}")
                
                # Specific recommendations by category
                if category == 'language':
                    recommendations.append("Increase training data diversity for underrepresented languages")
                elif category == 'age_group':
                    recommendations.append("Review age-based performance and adjust models")
                elif category == 'gender':
                    recommendations.append("Audit for gender bias in training data")
                elif category == 'region':
                    recommendations.append("Add region-specific clinical guidelines")
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("Continue monitoring bias and safety metrics")
            recommendations.append("Maintain diverse training data collection")
        
        return recommendations
    
    def _generate_executive_summary(
        self,
        bias_metrics: Dict[str, Any],
        safety_metrics: SafetyMetrics
    ) -> Dict[str, Any]:
        """Generate executive summary of bias and safety performance."""
        
        summary = {
            'overall_status': 'good' if safety_metrics.overall_accuracy >= 0.90 else 'needs_attention',
            'key_metrics': {
                'total_cases': safety_metrics.total_cases,
                'overall_accuracy': f"{safety_metrics.overall_accuracy:.1%}",
                'emergency_detection_accuracy': f"{safety_metrics.emergency_detection_accuracy:.1%}",
                'false_negatives': safety_metrics.false_negatives,
                'over_referrals': safety_metrics.over_referrals
            },
            'critical_issues': [],
            'improvement_areas': []
        }
        
        # Identify critical issues
        if safety_metrics.false_negatives > 5:
            summary['critical_issues'].append("High false negative rate - patient safety risk")
        
        if safety_metrics.emergency_detection_accuracy < 0.85:
            summary['critical_issues'].append("Poor emergency detection accuracy")
        
        # Identify bias issues
        for category, analysis in bias_metrics.items():
            if 'error' in analysis:
                continue
                
            if analysis.get('threshold_exceeded', False):
                summary['critical_issues'].append(f"Significant {category} bias detected")
                summary['improvement_areas'].append(category)
        
        # Overall assessment
        if len(summary['critical_issues']) == 0:
            summary['assessment'] = "System performing within acceptable safety and bias thresholds"
        else:
            summary['assessment'] = "System requires immediate attention to safety and bias issues"
        
        return summary
    
    def _calculate_impact_score(self, predicted: TriageLevel, actual: TriageLevel) -> float:
        """Calculate impact score for safety incidents."""
        
        # Define impact levels
        impact_matrix = {
            ('self_care', 'emergency'): 10.0,  # Worst case
            ('self_care', 'urgent'): 7.0,
            ('routine', 'emergency'): 9.0,
            ('routine', 'urgent'): 6.0,
            ('emergency', 'self_care'): 5.0,  # Over-referral
            ('urgent', 'self_care'): 3.0,
            ('emergency', 'routine'): 4.0,
            ('urgent', 'routine'): 2.0,
            ('self_care', 'routine'): 1.0,  # Correct
            ('routine', 'self_care'): 1.0,  # Correct
            ('emergency', 'emergency'): 0.0,  # Correct
            ('urgent', 'urgent'): 0.0,  # Correct
            ('routine', 'routine'): 0.0,  # Correct
        }
        
        return impact_matrix.get((predicted, actual), 1.0)
    
    def _get_age_group(self, age: int) -> str:
        """Get age group category."""
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
    
    def _get_region(self, location: str) -> str:
        """Get region category from location."""
        location_lower = location.lower()
        
        if any(country in location_lower for country in ['kenya', 'tanzania', 'uganda']):
            return 'africa_east'
        elif any(country in location_lower for country in ['nigeria', 'ghana', 'senegal']):
            return 'africa_west'
        elif any(country in location_lower for country in ['south africa', 'botswana', 'zimbabwe']):
            return 'africa_south'
        elif any(country in location_lower for country in ['india', 'thailand', 'vietnam']):
            return 'asia_se'
        elif any(country in location_lower for country in ['brazil', 'mexico', 'colombia']):
            return 'latam'
        else:
            return 'other'
    
    async def _trigger_model_retraining(self, component: str):
        """Trigger model retraining for safety improvements."""
        try:
            # This would integrate with the main training system
            logger.info(f"Triggering retraining for {component} due to safety concerns")
            
            # In a real system, this would:
            # 1. Collect recent false negative cases
            # 2. Augment training data
            # 3. Retrain affected models
            # 4. Validate and deploy new models
            
        except Exception as e:
            logger.error(f"Failed to trigger model retraining: {e}")
    
    def get_bias_dashboard_data(self) -> Dict[str, Any]:
        """Get data for bias dashboard visualization."""
        
        try:
            # Calculate current metrics
            bias_metrics = asyncio.run(self.calculate_bias_metrics(30))
            safety_metrics = asyncio.run(self.calculate_safety_metrics(30))
            
            dashboard_data = {
                'last_updated': datetime.utcnow().isoformat(),
                'safety_metrics': safety_metrics.dict(),
                'bias_analysis': bias_metrics,
                'trends': self._calculate_trends(),
                'alerts': self._get_active_alerts(),
                'performance_vs_thresholds': {
                    'false_negative_rate': {
                        'current': safety_metrics.false_negatives / safety_metrics.total_cases if safety_metrics.total_cases > 0 else 0,
                        'threshold': self.performance_thresholds['false_negative_rate_max'],
                        'status': 'exceeded' if (safety_metrics.false_negatives / safety_metrics.total_cases if safety_metrics.total_cases > 0 else 0) > self.performance_thresholds['false_negative_rate_max'] else 'ok'
                    },
                    'overall_accuracy': {
                        'current': safety_metrics.overall_accuracy,
                        'threshold': self.performance_thresholds['accuracy_min'],
                        'status': 'below_threshold' if safety_metrics.overall_accuracy < self.performance_thresholds['accuracy_min'] else 'ok'
                    }
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get bias dashboard data: {e}")
            return {"error": "Dashboard data unavailable"}
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate trend data for dashboard."""
        
        # This would calculate trends over time
        # For now, return placeholder data
        return {
            'false_negative_trend': 'stable',
            'accuracy_trend': 'improving',
            'bias_trend': 'stable'
        }
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active safety and bias alerts."""
        
        alerts = []
        
        # Check recent safety logs for alerts
        recent_logs = [
            log for log in self.safety_logs
            if datetime.fromisoformat(log['timestamp']) >= datetime.utcnow() - timedelta(days=7)
        ]
        
        critical_logs = [log for log in recent_logs if log.get('severity') == 'critical']
        high_logs = [log for log in recent_logs if log.get('severity') == 'high']
        
        if critical_logs:
            alerts.append({
                'type': 'critical',
                'count': len(critical_logs),
                'message': f"{len(critical_logs)} critical safety issues in past 7 days"
            })
        
        if high_logs:
            alerts.append({
                'type': 'high',
                'count': len(high_logs),
                'message': f"{len(high_logs)} high-priority safety issues in past 7 days"
            })
        
        return alerts

# Global instance
safety_bias_layer = SafetyBiasLayer()
