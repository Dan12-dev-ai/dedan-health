import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import logging

from models_v2 import (
    ChronicCondition, ChronicCareData, ChronicCareCheckIn, 
    ChronicCarePlan, HomeMeasurement, RiskScore
)

# Configure logging
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()

class PatientHistory(Base):
    __tablename__ = "patient_history"
    
    id = Column(String, primary_key=True)  # patient_id
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Demographics
    age = Column(Integer)
    sex = Column(String)
    location = Column(String)
    language = Column(String)
    
    # Chronic conditions
    chronic_conditions = Column(JSON, default=list)
    
    # Care plans
    care_plans = Column(JSON, default=dict)
    
    # Risk history
    risk_history = Column(JSON, default=list)
    
    # Check-in history
    check_in_history = Column(JSON, default=list)
    
    # Measurement history
    measurement_history = Column(JSON, default=list)

class ChronicCareManager:
    """
    DEDAN Chronic Care Manager - Manages patient history, tracking, and care plans.
    """
    
    def __init__(self, database_url: str = "sqlite:///./chronic_care.db"):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        logger.info("Chronic Care Manager initialized")
    
    async def create_patient_profile(self, patient_id: str, patient_data: Dict[str, Any]) -> bool:
        """Create or update patient chronic care profile."""
        
        try:
            session = self.SessionLocal()
            
            # Check if patient exists
            existing_patient = session.query(PatientHistory).filter_by(id=patient_id).first()
            
            if existing_patient:
                # Update existing patient
                existing_patient.age = patient_data.get('age')
                existing_patient.sex = patient_data.get('sex')
                existing_patient.location = patient_data.get('location')
                existing_patient.language = patient_data.get('language')
                existing_patient.chronic_conditions = patient_data.get('chronic_conditions', [])
                existing_patient.updated_at = datetime.utcnow()
            else:
                # Create new patient
                new_patient = PatientHistory(
                    id=patient_id,
                    age=patient_data.get('age'),
                    sex=patient_data.get('sex'),
                    location=patient_data.get('location'),
                    language=patient_data.get('language'),
                    chronic_conditions=patient_data.get('chronic_conditions', [])
                )
                session.add(new_patient)
            
            session.commit()
            logger.info(f"Patient profile created/updated for {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create patient profile: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def record_check_in(self, check_in_data: Dict[str, Any]) -> bool:
        """Record chronic care check-in."""
        
        try:
            session = self.SessionLocal()
            
            patient_id = check_in_data['patient_id']
            
            # Get patient
            patient = session.query(PatientHistory).filter_by(id=patient_id).first()
            if not patient:
                logger.error(f"Patient {patient_id} not found")
                return False
            
            # Create check-in record
            check_in_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "condition": check_in_data.get('condition'),
                "symptoms": check_in_data.get('symptoms', []),
                "medication_taken": check_in_data.get('medication_taken'),
                "side_effects": check_in_data.get('side_effects', []),
                "measurements": [m.dict() for m in check_in_data.get('measurements', [])],
                "notes": check_in_data.get('notes'),
                "risk_score": check_in_data.get('risk_score')
            }
            
            # Add to patient history
            if not patient.check_in_history:
                patient.check_in_history = []
            
            patient.check_in_history.append(check_in_record)
            patient.updated_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Check-in recorded for patient {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record check-in: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def create_care_plan(self, patient_id: str, care_plan_data: Dict[str, Any]) -> bool:
        """Create personalized chronic care plan."""
        
        try:
            session = self.SessionLocal()
            
            # Get patient
            patient = session.query(PatientHistory).filter_by(id=patient_id).first()
            if not patient:
                logger.error(f"Patient {patient_id} not found")
                return False
            
            # Create care plan
            care_plan = {
                "condition": care_plan_data.get('condition'),
                "created_date": datetime.utcnow().isoformat(),
                "goals": care_plan_data.get('goals', []),
                "medications": care_plan_data.get('medications', []),
                "monitoring_schedule": care_plan_data.get('monitoring_schedule', {}),
                "red_flags": care_plan_data.get('red_flags', []),
                "follow_up_frequency": care_plan_data.get('follow_up_frequency'),
                "education_topics": care_plan_data.get('education_topics', [])
            }
            
            # Add to patient care plans
            if not patient.care_plans:
                patient.care_plans = {}
            
            condition = care_plan_data.get('condition')
            patient.care_plans[condition] = care_plan
            patient.updated_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Care plan created for patient {patient_id} - {condition}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create care plan: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def record_home_measurement(self, patient_id: str, measurement: HomeMeasurement) -> bool:
        """Record home measurement."""
        
        try:
            session = self.SessionLocal()
            
            # Get patient
            patient = session.query(PatientHistory).filter_by(id=patient_id).first()
            if not patient:
                logger.error(f"Patient {patient_id} not found")
                return False
            
            # Create measurement record
            measurement_record = measurement.dict()
            measurement_record['recorded_at'] = datetime.utcnow().isoformat()
            
            # Add to patient measurement history
            if not patient.measurement_history:
                patient.measurement_history = []
            
            patient.measurement_history.append(measurement_record)
            patient.updated_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Home measurement recorded for patient {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record home measurement: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def get_patient_history(self, patient_id: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get patient history for specified time period."""
        
        try:
            session = self.SessionLocal()
            
            patient = session.query(PatientHistory).filter_by(id=patient_id).first()
            if not patient:
                return None
            
            # Filter recent data
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            recent_check_ins = [
                check_in for check_in in patient.check_in_history or []
                if datetime.fromisoformat(check_in['timestamp']) >= cutoff_date
            ]
            
            recent_measurements = [
                measurement for measurement in patient.measurement_history or []
                if datetime.fromisoformat(measurement['timestamp']) >= cutoff_date
            ]
            
            # Calculate trends
            trends = await self._calculate_trends(recent_check_ins, recent_measurements)
            
            history = {
                "patient_id": patient_id,
                "demographics": {
                    "age": patient.age,
                    "sex": patient.sex,
                    "location": patient.location,
                    "language": patient.language
                },
                "chronic_conditions": patient.chronic_conditions,
                "care_plans": patient.care_plans,
                "recent_check_ins": recent_check_ins,
                "recent_measurements": recent_measurements,
                "trends": trends,
                "last_updated": patient.updated_at.isoformat()
            }
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get patient history: {e}")
            return None
        finally:
            session.close()
    
    async def _calculate_trends(self, check_ins: List[Dict], measurements: List[Dict]) -> Dict[str, Any]:
        """Calculate trends from check-ins and measurements."""
        
        trends = {
            "symptom_trends": {},
            "measurement_trends": {},
            "adherence_trends": {},
            "risk_trends": {}
        }
        
        # Symptom trends
        symptom_counts = {}
        for check_in in check_ins:
            for symptom in check_in.get('symptoms', []):
                symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
        
        trends["symptom_trends"] = {
            "most_common": sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "total_check_ins": len(check_ins)
        }
        
        # Measurement trends
        measurement_trends = {}
        for measurement in measurements:
            measurement_type = measurement['measurement_type']
            if measurement_type not in measurement_trends:
                measurement_trends[measurement_type] = []
            measurement_trends[measurement_type].append(measurement['value'])
        
        # Calculate averages and trends for each measurement type
        for m_type, values in measurement_trends.items():
            if len(values) >= 2:
                recent_avg = sum(values[-3:]) / min(3, len(values[-3:]))
                older_avg = sum(values[:-3]) / max(1, len(values[:-3]))
                
                trend = "stable"
                if recent_avg > older_avg * 1.1:
                    trend = "increasing"
                elif recent_avg < older_avg * 0.9:
                    trend = "decreasing"
                
                measurement_trends[m_type] = {
                    "current": values[-1],
                    "average": sum(values) / len(values),
                    "trend": trend,
                    "count": len(values)
                }
        
        trends["measurement_trends"] = measurement_trends
        
        # Adherence trends
        adherence_scores = []
        for check_in in check_ins:
            if check_in.get('medication_taken') is not None:
                adherence_scores.append(1.0 if check_in['medication_taken'] else 0.0)
        
        if adherence_scores:
            trends["adherence_trends"] = {
                "current_adherence": adherence_scores[-1] if adherence_scores else 0.0,
                "average_adherence": sum(adherence_scores) / len(adherence_scores),
                "trend": "improving" if len(adherence_scores) >= 2 and adherence_scores[-1] > adherence_scores[-2] else "stable"
            }
        
        return trends
    
    async def get_risk_assessment(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get current risk assessment for patient."""
        
        try:
            session = self.SessionLocal()
            
            patient = session.query(PatientHistory).filter_by(id=patient_id).first()
            if not patient:
                return None
            
            # Get recent data
            recent_history = await self.get_patient_history(patient_id, days=30)
            if not recent_history:
                return None
            
            # Calculate risk factors
            risk_factors = []
            
            # Chronic condition risks
            for condition in patient.chronic_conditions:
                risk_factors.append(f"chronic_{condition}")
            
            # Measurement-based risks
            for m_type, trend_data in recent_history['trends']['measurement_trends'].items():
                if m_type == 'blood_pressure' and trend_data.get('current', {}).get('systolic', 0) > 140:
                    risk_factors.append("uncontrolled_hypertension")
                elif m_type == 'blood_glucose' and trend_data.get('current', 0) > 200:
                    risk_factors.append("uncontrolled_diabetes")
                elif m_type == 'weight' and trend_data.get('trend') == 'increasing':
                    risk_factors.append("weight_gain")
            
            # Adherence risk
            adherence = recent_history['trends']['adherence_trends'].get('current_adherence', 1.0)
            if adherence < 0.8:
                risk_factors.append("poor_medication_adherence")
            
            # Calculate overall risk score
            risk_score = self._calculate_risk_score(risk_factors, adherence)
            
            return {
                "patient_id": patient_id,
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "assessment_date": datetime.utcnow().isoformat(),
                "recommendations": self._generate_risk_recommendations(risk_score, risk_factors)
            }
            
        except Exception as e:
            logger.error(f"Failed to get risk assessment: {e}")
            return None
        finally:
            session.close()
    
    def _calculate_risk_score(self, risk_factors: List[str], adherence: float) -> RiskScore:
        """Calculate overall risk score."""
        
        risk_score = 0
        
        # High-risk factors
        high_risk_factors = [
            "uncontrolled_diabetes", "uncontrolled_hypertension", 
            "emergency_symptoms", "multiple_comorbidities"
        ]
        
        # Medium-risk factors
        medium_risk_factors = [
            "poor_medication_adherence", "weight_gain", 
            "worsening_symptoms", "missed_check_ins"
        ]
        
        for factor in risk_factors:
            if factor in high_risk_factors:
                risk_score += 3
            elif factor in medium_risk_factors:
                risk_score += 2
            else:
                risk_score += 1
        
        # Adjust for adherence
        if adherence < 0.5:
            risk_score += 2
        elif adherence < 0.8:
            risk_score += 1
        
        # Convert to risk level
        if risk_score >= 8:
            return RiskScore.HIGH
        elif risk_score >= 4:
            return RiskScore.MEDIUM
        else:
            return RiskScore.LOW
    
    def _generate_risk_recommendations(self, risk_score: RiskScore, risk_factors: List[str]) -> List[str]:
        """Generate risk-based recommendations."""
        
        recommendations = []
        
        if risk_score == RiskScore.HIGH:
            recommendations.extend([
                "Contact healthcare provider immediately",
                "Review medication adherence",
                "Monitor vital signs twice daily",
                "Prepare for urgent care if needed"
            ])
        elif risk_score == RiskScore.MEDIUM:
            recommendations.extend([
                "Schedule appointment within 1 week",
                "Increase monitoring frequency",
                "Review medication effectiveness",
                "Consider lifestyle modifications"
            ])
        else:  # LOW risk
            recommendations.extend([
                "Continue current care plan",
                "Maintain medication adherence",
                "Schedule routine follow-up",
                "Monitor for any changes"
            ])
        
        # Factor-specific recommendations
        if "uncontrolled_diabetes" in risk_factors:
            recommendations.extend([
                "Check blood glucose more frequently",
                "Review diabetes management plan",
                "Consider dietary adjustments"
            ])
        
        if "uncontrolled_hypertension" in risk_factors:
            recommendations.extend([
                "Monitor blood pressure daily",
                "Reduce sodium intake",
                "Review antihypertensive medications"
            ])
        
        if "poor_medication_adherence" in risk_factors:
            recommendations.extend([
                "Set up medication reminders",
                "Use pill organizers",
                "Involve family support"
            ])
        
        return list(set(recommendations))[:8]  # Limit to 8 recommendations
    
    async def generate_care_plan_suggestions(self, patient_id: str, condition: str) -> List[str]:
        """Generate AI-powered care plan suggestions."""
        
        try:
            # Get patient history
            history = await self.get_patient_history(patient_id, days=90)
            if not history:
                return []
            
            suggestions = []
            
            # Condition-specific suggestions
            if condition == "diabetes":
                suggestions.extend([
                    "Check HbA1c every 3 months",
                    "Monitor blood glucose before meals",
                    "Follow carbohydrate-controlled diet",
                    "Exercise 30 minutes daily",
                    "Check feet daily for sores"
                ])
            elif condition == "hypertension":
                suggestions.extend([
                    "Monitor blood pressure daily",
                    "Limit sodium to <2g per day",
                    "Take medications as prescribed",
                    "Maintain healthy weight",
                    "Reduce alcohol intake"
                ])
            elif condition == "asthma":
                suggestions.extend([
                    "Use inhaler as prescribed",
                    "Avoid known triggers",
                    "Monitor peak flow daily",
                    "Have rescue medication available",
                    "Create asthma action plan"
                ])
            
            # Personalized suggestions based on history
            adherence = history['trends']['adherence_trends'].get('average_adherence', 1.0)
            if adherence < 0.8:
                suggestions.append("Focus on improving medication adherence")
            
            # Measurement trends
            for m_type, trend_data in history['trends']['measurement_trends'].items():
                if trend_data.get('trend') == 'increasing':
                    if m_type == 'blood_pressure':
                        suggestions.append("Intensify blood pressure management")
                    elif m_type == 'blood_glucose':
                        suggestions.append("Review diabetes management plan")
                    elif m_type == 'weight':
                        suggestions.append("Consider weight management program")
            
            return list(set(suggestions))[:10]
            
        except Exception as e:
            logger.error(f"Failed to generate care plan suggestions: {e}")
            return []
    
    async def get_adherence_insights(self, patient_id: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed medication adherence insights."""
        
        try:
            history = await self.get_patient_history(patient_id, days)
            if not history:
                return {}
            
            check_ins = history['recent_check_ins']
            if not check_ins:
                return {}
            
            # Calculate adherence metrics
            total_check_ins = len(check_ins)
            taken_check_ins = sum(1 for check_in in check_ins if check_in.get('medication_taken', False))
            adherence_rate = taken_check_ins / total_check_ins if total_check_ins > 0 else 0
            
            # Time-based adherence
            adherence_by_time = {}
            for check_in in check_ins:
                date = datetime.fromisoformat(check_in['timestamp'])
                day_of_week = date.strftime('%A')
                
                if day_of_week not in adherence_by_time:
                    adherence_by_time[day_of_week] = {'taken': 0, 'total': 0}
                
                adherence_by_time[day_of_week]['total'] += 1
                if check_in.get('medication_taken', False):
                    adherence_by_time[day_of_week]['taken'] += 1
            
            # Calculate rates by day
            for day, data in adherence_by_time.items():
                data['rate'] = data['taken'] / data['total'] if data['total'] > 0 else 0
            
            # Side effects analysis
            side_effects = []
            for check_in in check_ins:
                side_effects.extend(check_in.get('side_effects', []))
            
            side_effect_counts = {}
            for effect in side_effects:
                side_effect_counts[effect] = side_effect_counts.get(effect, 0) + 1
            
            return {
                "overall_adherence": adherence_rate,
                "total_check_ins": total_check_ins,
                "adherence_by_day": adherence_by_time,
                "common_side_effects": sorted(side_effect_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                "insights": self._generate_adherence_insights(adherence_rate, adherence_by_time, side_effect_counts)
            }
            
        except Exception as e:
            logger.error(f"Failed to get adherence insights: {e}")
            return {}
    
    def _generate_adherence_insights(self, overall_rate: float, by_day: Dict, side_effects: Dict) -> List[str]:
        """Generate insights from adherence data."""
        
        insights = []
        
        if overall_rate < 0.5:
            insights.append("Medication adherence is critically low - immediate intervention needed")
        elif overall_rate < 0.8:
            insights.append("Medication adherence is below target - consider reminder system")
        else:
            insights.append("Medication adherence is good - maintain current routine")
        
        # Day-specific insights
        low_days = [day for day, data in by_day.items() if data.get('rate', 0) < 0.5]
        if low_days:
            insights.append(f"Lowest adherence on: {', '.join(low_days)}")
        
        # Side effects insights
        if side_effects:
            most_common = max(side_effects.items(), key=lambda x: x[1])
            insights.append(f"Most common side effect: {most_common[0]} ({most_common[1]} occurrences)")
        
        return insights

# Global instance
chronic_care_manager = ChronicCareManager()
