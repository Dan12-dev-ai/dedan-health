import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()

class TriageFeedback(Base):
    __tablename__ = "triage_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=False, index=True)
    original_triage_level = Column(String, nullable=False)
    doctor_triage_level = Column(String, nullable=False)
    doctor_diagnosis = Column(Text, nullable=True)
    treatment_given = Column(Text, nullable=True)
    patient_age_group = Column(String, nullable=False)
    patient_sex = Column(String, nullable=False)
    patient_language = Column(String, nullable=False)
    symptoms_keywords = Column(Text, nullable=False)  # JSON array
    symptoms_description = Column(Text, nullable=False)
    dedan_confidence_score = Column(Float, nullable=False)
    risk_flags_detected = Column(Text, nullable=True)  # JSON array
    suggested_next_step = Column(Text, nullable=False)
    patient_summary = Column(Text, nullable=False)
    doctor_notes = Column(Text, nullable=True)
    feedback_timestamp = Column(DateTime, default=datetime.utcnow)
    clinic_id = Column(String, nullable=True)
    doctor_id = Column(String, nullable=True)
    outcome = Column(String, nullable=True)  # 'improved', 'same', 'worsened'
    follow_up_required = Column(Boolean, default=False)
    follow_up_days = Column(Integer, nullable=True)
    emergency_accurate = Column(Boolean, nullable=True)  # Was emergency detection correct?
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'session_id': self.session_id,
            'original_triage_level': self.original_triage_level,
            'doctor_triage_level': self.doctor_triage_level,
            'doctor_diagnosis': self.doctor_diagnosis,
            'treatment_given': self.treatment_given,
            'patient_age_group': self.patient_age_group,
            'patient_sex': self.patient_sex,
            'patient_language': self.patient_language,
            'symptoms_keywords': json.loads(self.symptoms_keywords) if self.symptoms_keywords else [],
            'symptoms_description': self.symptoms_description,
            'dedan_confidence_score': self.dedan_confidence_score,
            'risk_flags_detected': json.loads(self.risk_flags_detected) if self.risk_flags_detected else [],
            'suggested_next_step': self.suggested_next_step,
            'patient_summary': self.patient_summary,
            'doctor_notes': self.doctor_notes,
            'feedback_timestamp': self.feedback_timestamp.isoformat(),
            'clinic_id': self.clinic_id,
            'doctor_id': self.doctor_id,
            'outcome': self.outcome,
            'follow_up_required': self.follow_up_required,
            'follow_up_days': self.follow_up_days,
            'emergency_accurate': self.emergency_accurate
        }

class DEDANDataFlywheel:
    """
    DEDAN Data-Flywheel: Continuous improvement system for medical triage
    """
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///./dedan_flywheel.db")
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Initialize model
        self.model = None
        self.model_version = "1.0"
        self.last_training_date = None
        
        logger.info("DEDAN Data-Flywheel initialized")
    
    async def collect_feedback(self, triage_data: Dict[str, Any], doctor_feedback: Dict[str, Any]) -> bool:
        """Collect triage feedback from healthcare providers"""
        try:
            session = self.SessionLocal()
            
            feedback = TriageFeedback(
                session_id=triage_data.get('session_id'),
                original_triage_level=triage_data.get('triage_level'),
                doctor_triage_level=doctor_feedback.get('triage_level'),
                doctor_diagnosis=doctor_feedback.get('diagnosis'),
                treatment_given=doctor_feedback.get('treatment'),
                patient_age_group=triage_data.get('patient_age_group'),
                patient_sex=triage_data.get('patient_sex'),
                patient_language=triage_data.get('patient_language'),
                symptoms_keywords=json.dumps(triage_data.get('symptoms_keywords', [])),
                symptoms_description=triage_data.get('symptoms_description'),
                dedan_confidence_score=triage_data.get('confidence_score', 0.0),
                risk_flags_detected=json.dumps(triage_data.get('risk_flags', [])),
                suggested_next_step=triage_data.get('suggested_next_step'),
                patient_summary=triage_data.get('patient_summary'),
                doctor_notes=doctor_feedback.get('notes'),
                clinic_id=doctor_feedback.get('clinic_id'),
                doctor_id=doctor_feedback.get('doctor_id'),
                outcome=doctor_feedback.get('outcome'),
                follow_up_required=doctor_feedback.get('follow_up_required', False),
                follow_up_days=doctor_feedback.get('follow_up_days'),
                emergency_accurate=doctor_feedback.get('emergency_accurate')
            )
            
            session.add(feedback)
            session.commit()
            
            logger.info(f"Collected feedback for session {triage_data.get('session_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to collect feedback: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    async def get_performance_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Calculate performance metrics from feedback data"""
        try:
            session = self.SessionLocal()
            
            # Get recent feedback
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            feedback_records = session.query(TriageFeedback).filter(
                TriageFeedback.feedback_timestamp >= cutoff_date
            ).all()
            
            if not feedback_records:
                return {
                    'total_cases': 0,
                    'accuracy': 0.0,
                    'emergency_detection_accuracy': 0.0,
                    'confidence_distribution': {},
                    'language_distribution': {},
                    'age_group_distribution': {},
                    'top_misclassifications': []
                }
            
            # Calculate metrics
            total_cases = len(feedback_records)
            correct_predictions = sum(1 for f in feedback_records 
                                  if f.original_triage_level == f.doctor_triage_level)
            accuracy = correct_predictions / total_cases if total_cases > 0 else 0.0
            
            # Emergency detection accuracy
            emergency_cases = [f for f in feedback_records if f.original_triage_level == 'emergency']
            emergency_correct = sum(1 for f in emergency_cases if f.emergency_accurate)
            emergency_accuracy = emergency_correct / len(emergency_cases) if emergency_cases else 0.0
            
            # Confidence distribution
            confidence_ranges = {'0-50': 0, '51-70': 0, '71-90': 0, '91-100': 0}
            for f in feedback_records:
                conf = f.dedan_confidence_score * 100
                if conf <= 50:
                    confidence_ranges['0-50'] += 1
                elif conf <= 70:
                    confidence_ranges['51-70'] += 1
                elif conf <= 90:
                    confidence_ranges['71-90'] += 1
                else:
                    confidence_ranges['91-100'] += 1
            
            # Language distribution
            language_dist = {}
            for f in feedback_records:
                lang = f.patient_language or 'unknown'
                language_dist[lang] = language_dist.get(lang, 0) + 1
            
            # Age group distribution
            age_dist = {}
            for f in feedback_records:
                age_group = f.patient_age_group or 'unknown'
                age_dist[age_group] = age_dist.get(age_group, 0) + 1
            
            # Top misclassifications
            misclassifications = []
            for f in feedback_records:
                if f.original_triage_level != f.doctor_triage_level:
                    misclassifications.append({
                        'original': f.original_triage_level,
                        'doctor': f.doctor_triage_level,
                        'symptoms': f.symptoms_description[:100] + '...' if len(f.symptoms_description) > 100 else f.symptoms_description
                    })
            
            # Sort by frequency
            misclass_counts = {}
            for mis in misclassifications:
                key = f"{mis['original']} -> {mis['doctor']}"
                misclass_counts[key] = misclass_counts.get(key, 0) + 1
            
            top_misclassifications = sorted(misclass_counts.items(), 
                                        key=lambda x: x[1], 
                                        reverse=True)[:5]
            
            session.close()
            
            return {
                'total_cases': total_cases,
                'accuracy': accuracy,
                'emergency_detection_accuracy': emergency_accuracy,
                'confidence_distribution': confidence_ranges,
                'language_distribution': language_dist,
                'age_group_distribution': age_dist,
                'top_misclassifications': [
                    {'pattern': pattern, 'count': count} 
                    for pattern, count in top_misclassifications
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            return {}
    
    def prepare_training_data(self) -> Optional[pd.DataFrame]:
        """Prepare data for model training"""
        try:
            session = self.SessionLocal()
            
            # Get all feedback records
            feedback_records = session.query(TriageFeedback).all()
            session.close()
            
            if len(feedback_records) < 100:  # Minimum data for training
                logger.warning(f"Insufficient data for training: {len(feedback_records)} records (need 100+)")
                return None
            
            # Convert to DataFrame
            data = []
            for f in feedback_records:
                # Feature engineering
                symptoms_keywords = json.loads(f.symptoms_keywords) if f.symptoms_keywords else []
                risk_flags = json.loads(f.risk_flags_detected) if f.risk_flags_detected else []
                
                features = {
                    'patient_age_group': f.patient_age_group,
                    'patient_sex': f.patient_sex,
                    'patient_language': f.patient_language,
                    'symptoms_count': len(symptoms_keywords),
                    'risk_flags_count': len(risk_flags),
                    'has_chest_pain': 1 if 'chest' in f.symptoms_description.lower() else 0,
                    'has_breathing_difficulty': 1 if 'breath' in f.symptoms_description.lower() else 0,
                    'has_fever': 1 if 'fever' in f.symptoms_description.lower() else 0,
                    'has_headache': 1 if 'headache' in f.symptoms_description.lower() else 0,
                    'has_abdominal_pain': 1 if 'abdominal' in f.symptoms_description.lower() else 0,
                    'symptoms_length': len(f.symptoms_description),
                    'original_confidence': f.dedan_confidence_score,
                    'original_triage_level': f.original_triage_level
                }
                
                # Target variable
                target = f.doctor_triage_level  # Use doctor's assessment as ground truth
                
                data.append({**features, 'target': target})
            
            df = pd.DataFrame(data)
            logger.info(f"Prepared training dataset with {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to prepare training data: {e}")
            return None
    
    def train_model(self, df: pd.DataFrame) -> bool:
        """Train the triage improvement model"""
        try:
            if len(df) < 100:
                logger.warning("Insufficient data for training")
                return False
            
            # Prepare features and target
            feature_columns = [col for col in df.columns if col != 'target']
            
            # Encode categorical variables
            df_encoded = pd.get_dummies(df[feature_columns], 
                                       columns=['patient_age_group', 'patient_sex', 'patient_language'])
            
            # Add numerical features
            numerical_features = ['symptoms_count', 'risk_flags_count', 'has_chest_pain', 
                              'has_breathing_difficulty', 'has_fever', 'has_headache', 
                              'has_abdominal_pain', 'symptoms_length', 'original_confidence']
            
            X = pd.concat([df_encoded, df[numerical_features]], axis=1)
            y = df['target']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Generate classification report
            report = classification_report(y_test, y_pred, output_dict=True)
            
            self.last_training_date = datetime.utcnow()
            
            logger.info(f"Model trained with accuracy: {accuracy:.3f}")
            logger.info(f"Classification report: {report}")
            
            # Save model metadata
            self.save_model_metadata(accuracy, report)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to train model: {e}")
            return False
    
    def save_model_metadata(self, accuracy: float, report: Dict[str, Any]) -> None:
        """Save model training metadata"""
        try:
            metadata = {
                'model_version': self.model_version,
                'training_date': self.last_training_date.isoformat(),
                'accuracy': accuracy,
                'classification_report': report,
                'training_samples': len(self.model.n_features_) if self.model else 0
            }
            
            # Save to file
            with open('model_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info("Model metadata saved")
            
        except Exception as e:
            logger.error(f"Failed to save model metadata: {e}")
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """Generate improvement suggestions based on performance metrics"""
        try:
            metrics = asyncio.run(self.get_performance_metrics())
            
            suggestions = []
            
            # Accuracy-based suggestions
            if metrics.get('accuracy', 0) < 0.8:
                suggestions.append({
                    'type': 'accuracy',
                    'priority': 'high',
                    'title': 'Low Accuracy Detected',
                    'description': f"Current accuracy is {metrics.get('accuracy', 0):.1%}. Consider collecting more training data.",
                    'action': 'Increase feedback collection from healthcare providers'
                })
            
            # Emergency detection suggestions
            if metrics.get('emergency_detection_accuracy', 0) < 0.9:
                suggestions.append({
                    'type': 'emergency_detection',
                    'priority': 'critical',
                    'title': 'Emergency Detection Needs Improvement',
                    'description': f"Emergency detection accuracy is {metrics.get('emergency_detection_accuracy', 0):.1%}. This is critical for patient safety.",
                    'action': 'Review and enhance emergency keyword detection rules'
                })
            
            # Language-specific suggestions
            lang_dist = metrics.get('language_distribution', {})
            if len(lang_dist) > 1:
                min_lang_samples = min(lang_dist.values())
                if min_lang_samples < 50:
                    suggestions.append({
                        'type': 'language_coverage',
                        'priority': 'medium',
                        'title': 'Insufficient Language Coverage',
                        'description': f"Some languages have insufficient training data ({min_lang_samples} samples).",
                        'action': 'Increase diverse language data collection'
                    })
            
            # Misclassification patterns
            top_misclassifications = metrics.get('top_misclassifications', [])
            if top_misclassifications:
                top_pattern = top_misclassifications[0]
                suggestions.append({
                    'type': 'misclassification_pattern',
                    'priority': 'medium',
                    'title': 'Common Misclassification Pattern',
                    'description': f"Most common error: {top_pattern['pattern']} ({top_pattern['count']} occurrences)",
                    'action': 'Add specific rules or training examples for this pattern'
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            return []
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """Generate weekly performance report"""
        try:
            metrics = asyncio.run(self.get_performance_metrics(days=7))
            suggestions = self.get_improvement_suggestions()
            
            report = {
                'report_date': datetime.utcnow().isoformat(),
                'period': '7 days',
                'metrics': metrics,
                'improvement_suggestions': suggestions,
                'model_status': {
                    'version': self.model_version,
                    'last_training': self.last_training_date.isoformat() if self.last_training_date else None,
                    'trained': self.model is not None
                }
            }
            
            # Save report
            with open(f"weekly_report_{datetime.utcnow().strftime('%Y%m%d')}.json", 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info("Weekly report generated")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate weekly report: {e}")
            return {}
    
    async def auto_retrain(self) -> bool:
        """Automatically retrain model if conditions are met"""
        try:
            # Check if we have enough new data
            session = self.SessionLocal()
            
            # Get data since last training
            if self.last_training_date:
                new_feedback_count = session.query(TriageFeedback).filter(
                    TriageFeedback.feedback_timestamp > self.last_training_date
                ).count()
            else:
                new_feedback_count = session.query(TriageFeedback).count()
            
            session.close()
            
            # Retrain if we have 500+ new records or it's been 30 days
            days_since_training = (datetime.utcnow() - self.last_training_date).days if self.last_training_date else 999
            
            if new_feedback_count >= 500 or days_since_training >= 30:
                logger.info(f"Starting auto-retrain with {new_feedback_count} new records")
                
                df = self.prepare_training_data()
                if df is not None:
                    return self.train_model(df)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to auto-retrain: {e}")
            return False

# Global instance
data_flywheel = DEDANDataFlywheel()

# API endpoints for data flywheel
async def collect_feedback_endpoint(triage_data: Dict[str, Any], doctor_feedback: Dict[str, Any]) -> Dict[str, Any]:
    """API endpoint to collect feedback"""
    success = await data_flywheel.collect_feedback(triage_data, doctor_feedback)
    return {
        "success": success,
        "message": "Feedback collected successfully" if success else "Failed to collect feedback"
    }

async def get_metrics_endpoint(days: int = 30) -> Dict[str, Any]:
    """API endpoint to get performance metrics"""
    return await data_flywheel.get_performance_metrics(days)

async def get_suggestions_endpoint() -> List[Dict[str, Any]]:
    """API endpoint to get improvement suggestions"""
    return data_flywheel.get_improvement_suggestions()

async def generate_report_endpoint() -> Dict[str, Any]:
    """API endpoint to generate weekly report"""
    return data_flywheel.generate_weekly_report()

async def trigger_retrain_endpoint() -> Dict[str, Any]:
    """API endpoint to trigger model retraining"""
    success = await data_flywheel.auto_retrain()
    return {
        "success": success,
        "message": "Retraining started" if success else "Retraining conditions not met"
    }

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    # Generate weekly report
    report = data_flywheel.generate_weekly_report()
    print(json.dumps(report, indent=2))
    
    # Get current metrics
    metrics = asyncio.run(data_flywheel.get_performance_metrics())
    print(json.dumps(metrics, indent=2))
