import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import hashlib
import logging

from models_v2 import (
    HubClinicRegistration, HubTriageRule, TriageLevel,
    AgentType, Language
)

# Configure logging
logger = logging.getLogger(__name__)

class DEDANHub:
    """
    DEDAN Hub - Central federation layer for multiple clinics and regions.
    Manages collective knowledge sharing and Africa-Consensus Triage Rules.
    """
    
    def __init__(self):
        self.registered_clinics = {}
        self.triage_rules = {}
        self.collective_knowledge = {
            'disease_patterns': {},
            'treatment_outcomes': {},
            'regional_variations': {},
            'seasonal_trends': {}
        }
        self.consensus_rules = {
            'version': '1.0',
            'created_date': datetime.utcnow().isoformat(),
            'rules': {},
            'validation_status': {},
            'usage_stats': {}
        }
        
        # Initialize with sample data
        self._initialize_sample_data()
        
        logger.info("DEDAN Hub initialized")
    
    async def register_clinic(self, clinic_registration: HubClinicRegistration) -> Dict[str, Any]:
        """
        Register a clinic with the DEDAN Hub.
        Enables participation in collective knowledge sharing.
        """
        
        try:
            # Validate clinic registration
            validation_result = await self._validate_clinic_registration(clinic_registration)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'clinic_id': None
                }
            
            # Generate clinic ID
            clinic_id = self._generate_clinic_id(clinic_registration)
            
            # Store clinic registration
            self.registered_clinics[clinic_id] = {
                'registration': clinic_registration,
                'registered_at': datetime.utcnow().isoformat(),
                'status': 'active',
                'last_sync': None,
                'contribution_count': 0,
                'api_usage': {
                    'triage_requests': 0,
                    'feedback_submissions': 0,
                    'rule_updates': 0
                }
            }
            
            # Initialize clinic-specific knowledge base
            self.collective_knowledge['regional_variations'][clinic_id] = {
                'region': clinic_registration.region,
                'country': clinic_registration.country,
                'local_diseases': [],
                'local_treatments': [],
                'cultural_considerations': []
            }
            
            logger.info(f"Clinic registered: {clinic_id} - {clinic_registration.clinic_name}")
            
            return {
                'success': True,
                'clinic_id': clinic_id,
                'api_key': self._generate_api_key(clinic_id),
                'hub_rules_version': self.consensus_rules['version'],
                'welcome_message': f"Welcome to DEDAN Hub! Clinic {clinic_registration.clinic_name} is now part of the collective knowledge network."
            }
            
        except Exception as e:
            logger.error(f"Failed to register clinic: {e}")
            return {
                'success': False,
                'error': f"Registration failed: {str(e)}",
                'clinic_id': None
            }
    
    async def submit_triage_rule(
        self,
        clinic_id: str,
        rule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit triage rule for consideration in Africa-Consensus repository.
        """
        
        try:
            # Validate clinic is registered
            if clinic_id not in self.registered_clinics:
                return {
                    'success': False,
                    'error': 'Clinic not registered with DEDAN Hub'
                }
            
            # Validate rule data
            validation_result = await self._validate_triage_rule(rule_data)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error']
                }
            
            # Create rule object
            rule = HubTriageRule(
                rule_id=self._generate_rule_id(clinic_id),
                version=self.consensus_rules['version'],
                condition=rule_data.get('condition'),
                symptoms=rule_data.get('symptoms', []),
                triage_level=rule_data.get('triage_level'),
                evidence_level=rule_data.get('evidence_level', 'C'),
                source=clinic_id,
                created_date=datetime.utcnow()
            )
            
            # Store rule
            rule_key = f"{rule.condition}_{rule.triage_level}"
            self.triage_rules[rule_key] = rule
            
            # Add to consensus validation
            if rule_key not in self.consensus_rules['validation_status']:
                self.consensus_rules['validation_status'][rule_key] = {
                    'submitted_by': clinic_id,
                    'submission_date': rule.created_date.isoformat(),
                    'validating_clinics': [],
                    'approvals': 0,
                    'rejections': 0,
                    'status': 'pending_validation'
                }
            
            # Update clinic contribution count
            self.registered_clinics[clinic_id]['contribution_count'] += 1
            
            logger.info(f"Triage rule submitted: {rule.rule_id} from {clinic_id}")
            
            return {
                'success': True,
                'rule_id': rule.rule_id,
                'status': 'submitted_for_validation',
                'message': 'Rule submitted for consensus validation'
            }
            
        except Exception as e:
            logger.error(f"Failed to submit triage rule: {e}")
            return {
                'success': False,
                'error': f"Rule submission failed: {str(e)}"
            }
    
    async def validate_triage_rule(
        self,
        clinic_id: str,
        rule_id: str
    ) -> Dict[str, Any]:
        """
        Validate a triage rule submitted by another clinic.
        """
        
        try:
            # Validate clinic is registered
            if clinic_id not in self.registered_clinics:
                return {
                    'success': False,
                    'error': 'Clinic not registered'
                }
            
            # Find rule
            rule = None
            for key, rule_obj in self.triage_rules.items():
                if rule_obj.rule_id == rule_id:
                    rule = rule_obj
                    break
            
            if not rule:
                return {
                    'success': False,
                    'error': 'Rule not found'
                }
            
            # Add validation
            rule_key = f"{rule.condition}_{rule.triage_level}"
            if rule_key in self.consensus_rules['validation_status']:
                validation_status = self.consensus_rules['validation_status'][rule_key]
                
                if clinic_id not in validation_status['validating_clinics']:
                    validation_status['validating_clinics'].append(clinic_id)
                
                validation_status['approvals'] += 1
                
                # Check if we have enough validations for consensus
                if len(validation_status['validating_clinics']) >= 5:
                    approval_rate = validation_status['approvals'] / len(validation_status['validating_clinics'])
                    
                    if approval_rate >= 0.8:  # 80% approval rate
                        validation_status['status'] = 'approved'
                        validation_status['consensus_date'] = datetime.utcnow().isoformat()
                        
                        # Add to consensus rules
                        self.consensus_rules['rules'][rule_key] = rule.dict()
                        
                        logger.info(f"Rule approved by consensus: {rule_id}")
                    elif validation_status['approvals'] >= 3:
                        validation_status['status'] = 'rejected'
                        validation_status['rejections'] += len(validation_status['validating_clinics']) - validation_status['approvals']
                        
                        logger.info(f"Rule rejected by consensus: {rule_id}")
            
            return {
                'success': True,
                'status': validation_status.get('status', 'pending_validation'),
                'message': 'Validation recorded'
            }
            
        except Exception as e:
            logger.error(f"Failed to validate triage rule: {e}")
            return {
                'success': False,
                'error': f"Validation failed: {str(e)}"
            }
    
    async def share_collective_knowledge(
        self,
        clinic_id: str,
        knowledge_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Share anonymized knowledge with the collective network.
        """
        
        try:
            # Validate clinic is registered
            if clinic_id not in self.registered_clinics:
                return {
                    'success': False,
                    'error': 'Clinic not registered'
                }
            
            # Anonymize data
            anonymized_data = await self._anonymize_knowledge(knowledge_data)
            
            # Categorize knowledge
            knowledge_type = knowledge_data.get('type', 'disease_pattern')
            
            if knowledge_type == 'disease_pattern':
                self._update_disease_patterns(clinic_id, anonymized_data)
            elif knowledge_type == 'treatment_outcome':
                self._update_treatment_outcomes(clinic_id, anonymized_data)
            elif knowledge_type == 'seasonal_trend':
                self._update_seasonal_trends(clinic_id, anonymized_data)
            else:
                self._update_regional_variations(clinic_id, anonymized_data)
            
            # Update clinic contribution count
            self.registered_clinics[clinic_id]['contribution_count'] += 1
            
            logger.info(f"Collective knowledge shared by {clinic_id}: {knowledge_type}")
            
            return {
                'success': True,
                'message': 'Knowledge shared with collective network',
                'contribution_count': self.registered_clinics[clinic_id]['contribution_count']
            }
            
        except Exception as e:
            logger.error(f"Failed to share collective knowledge: {e}")
            return {
                'success': False,
                'error': f"Knowledge sharing failed: {str(e)}"
            }
    
    async def get_hub_triage_rules(
        self,
        clinic_id: str,
        version: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get DEDAN Hub triage rules for clinic use.
        """
        
        try:
            # Validate clinic is registered
            if clinic_id not in self.registered_clinics:
                return {
                    'success': False,
                    'error': 'Clinic not registered'
                }
            
            # Get clinic configuration
            clinic = self.registered_clinics[clinic_id]
            
            # Determine which rules to return
            rules_to_return = {}
            
            if clinic['registration'].local_rules_enabled:
                # Return clinic's local rules + consensus rules
                rules_to_return = {**self.consensus_rules['rules']}
                
                # Add clinic-specific rules
                for key, rule in self.triage_rules.items():
                    if rule.source == clinic_id:
                        rules_to_return[key] = rule.dict()
            else:
                # Return only consensus rules
                rules_to_return = self.consensus_rules['rules']
            
            # Apply filters
            if filters:
                rules_to_return = self._apply_rule_filters(rules_to_return, filters)
            
            # Update usage stats
            self.registered_clinics[clinic_id]['api_usage']['rule_updates'] += 1
            
            logger.info(f"Triage rules provided to {clinic_id}")
            
            return {
                'success': True,
                'version': version or self.consensus_rules['version'],
                'rules': rules_to_return,
                'total_rules': len(rules_to_return),
                'last_updated': self.consensus_rules['created_date']
            }
            
        except Exception as e:
            logger.error(f"Failed to get hub triage rules: {e}")
            return {
                'success': False,
                'error': f"Failed to get rules: {str(e)}"
            }
    
    async def get_collective_insights(
        self,
        clinic_id: str,
        insight_type: str = 'all'
    ) -> Dict[str, Any]:
        """
        Get collective insights from the DEDAN Hub network.
        """
        
        try:
            # Validate clinic is registered
            if clinic_id not in self.registered_clinics:
                return {
                    'success': False,
                    'error': 'Clinic not registered'
                }
            
            insights = {}
            
            if insight_type == 'all' or insight_type == 'disease_patterns':
                insights['disease_patterns'] = self._analyze_disease_patterns()
            
            if insight_type == 'all' or insight_type == 'treatment_outcomes':
                insights['treatment_outcomes'] = self._analyze_treatment_outcomes()
            
            if insight_type == 'all' or insight_type == 'seasonal_trends':
                insights['seasonal_trends'] = self._analyze_seasonal_trends()
            
            if insight_type == 'all' or insight_type == 'regional_variations':
                insights['regional_variations'] = self._analyze_regional_variations()
            
            # Update usage stats
            self.registered_clinics[clinic_id]['api_usage']['triage_requests'] += 1
            
            logger.info(f"Collective insights provided to {clinic_id}")
            
            return {
                'success': True,
                'insights': insights,
                'network_size': len(self.registered_clinics),
                'data_freshness': self._calculate_data_freshness()
            }
            
        except Exception as e:
            logger.error(f"Failed to get collective insights: {e}")
            return {
                'success': False,
                'error': f"Failed to get insights: {str(e)}"
            }
    
    async def _validate_clinic_registration(self, registration: HubClinicRegistration) -> Dict[str, Any]:
        """Validate clinic registration data."""
        
        # Required fields
        required_fields = ['clinic_name', 'region', 'country', 'contact_email', 'api_endpoint']
        for field in required_fields:
            if not getattr(registration, field):
                return {
                    'valid': False,
                    'error': f'Missing required field: {field}'
                }
        
        # Email validation
        if '@' not in registration.contact_email:
            return {
                'valid': False,
                'error': 'Invalid email address'
            }
        
        # API endpoint validation
        if not registration.api_endpoint.startswith(('http://', 'https://')):
            return {
                'valid': False,
                'error': 'Invalid API endpoint URL'
            }
        
        return {'valid': True}
    
    async def _validate_triage_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate triage rule data."""
        
        # Required fields
        required_fields = ['condition', 'symptoms', 'triage_level']
        for field in required_fields:
            if field not in rule_data:
                return {
                    'valid': False,
                    'error': f'Missing required field: {field}'
                }
        
        # Validate triage level
        valid_levels = [level.value for level in TriageLevel]
        if rule_data.get('triage_level') not in valid_levels:
            return {
                'valid': False,
                'error': 'Invalid triage level'
            }
        
        # Validate symptoms
        symptoms = rule_data.get('symptoms', [])
        if not isinstance(symptoms, list) or len(symptoms) == 0:
            return {
                'valid': False,
                'error': 'Symptoms must be a non-empty list'
            }
        
        return {'valid': True}
    
    def _generate_clinic_id(self, registration: HubClinicRegistration) -> str:
        """Generate unique clinic ID."""
        
        # Create hash from clinic details
        clinic_string = f"{registration.clinic_name}_{registration.region}_{registration.country}"
        clinic_hash = hashlib.md5(clinic_string.encode()).hexdigest()[:8]
        
        return f"clinic_{clinic_hash}_{datetime.utcnow().strftime('%Y%m%d')}"
    
    def _generate_rule_id(self, clinic_id: str) -> str:
        """Generate unique rule ID."""
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        return f"rule_{clinic_id}_{timestamp}"
    
    def _generate_api_key(self, clinic_id: str) -> str:
        """Generate API key for clinic."""
        
        # Create secure API key
        key_string = f"{clinic_id}_{datetime.utcnow().isoformat()}"
        api_key = hashlib.sha256(key_string.encode()).hexdigest()
        
        return f"dh_{api_key[:32]}"
    
    async def _anonymize_knowledge(self, knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize knowledge data for collective sharing."""
        
        anonymized = knowledge_data.copy()
        
        # Remove or anonymize sensitive fields
        sensitive_fields = ['patient_id', 'patient_name', 'contact_info', 'exact_location']
        for field in sensitive_fields:
            if field in anonymized:
                if field == 'patient_id':
                    anonymized[field] = f"patient_{hashlib.md5(str(anonymized[field]).hexdigest())[:8]}"
                elif field == 'exact_location':
                    anonymized[field] = f"location_{hashlib.md5(str(anonymized[field]).hexdigest())[:8]}"
                else:
                    anonymized[field] = "[REDACTED]"
        
        # Add anonymization metadata
        anonymized['anonymized'] = True
        anonymized['anonymization_date'] = datetime.utcnow().isoformat()
        
        return anonymized
    
    def _update_disease_patterns(self, clinic_id: str, data: Dict[str, Any]):
        """Update disease patterns knowledge."""
        
        condition = data.get('condition')
        if condition:
            if condition not in self.collective_knowledge['disease_patterns']:
                self.collective_knowledge['disease_patterns'][condition] = {
                    'symptoms': [],
                    'regional_variations': [],
                    'seasonal_patterns': [],
                    'contributing_clinics': []
                }
            
            self.collective_knowledge['disease_patterns'][condition]['symptoms'].extend(
                data.get('symptoms', [])
            )
            
            if clinic_id not in self.collective_knowledge['disease_patterns'][condition]['contributing_clinics']:
                self.collective_knowledge['disease_patterns'][condition]['contributing_clinics'].append(clinic_id)
    
    def _update_treatment_outcomes(self, clinic_id: str, data: Dict[str, Any]):
        """Update treatment outcomes knowledge."""
        
        condition = data.get('condition')
        treatment = data.get('treatment')
        outcome = data.get('outcome')
        
        if condition and treatment and outcome:
            key = f"{condition}_{treatment}"
            if key not in self.collective_knowledge['treatment_outcomes']:
                self.collective_knowledge['treatment_outcomes'][key] = {
                    'outcomes': [],
                    'success_rate': 0,
                    'contributing_clinics': []
                }
            
            self.collective_knowledge['treatment_outcomes'][key]['outcomes'].append({
                'outcome': outcome,
                'clinic_id': clinic_id,
                'date': datetime.utcnow().isoformat()
            })
            
            # Calculate success rate
            outcomes = self.collective_knowledge['treatment_outcomes'][key]['outcomes']
            successful = len([o for o in outcomes if o['outcome'] in ['recovered', 'improved']])
            self.collective_knowledge['treatment_outcomes'][key]['success_rate'] = successful / len(outcomes)
            
            if clinic_id not in self.collective_knowledge['treatment_outcomes'][key]['contributing_clinics']:
                self.collective_knowledge['treatment_outcomes'][key]['contributing_clinics'].append(clinic_id)
    
    def _update_seasonal_trends(self, clinic_id: str, data: Dict[str, Any]):
        """Update seasonal trends knowledge."""
        
        season = data.get('season')
        condition = data.get('condition')
        trend = data.get('trend')
        
        if season and condition:
            if season not in self.collective_knowledge['seasonal_trends']:
                self.collective_knowledge['seasonal_trends'][season] = {
                    'conditions': {},
                    'contributing_clinics': []
                }
            
            if condition not in self.collective_knowledge['seasonal_trends'][season]['conditions']:
                self.collective_knowledge['seasonal_trends'][season]['conditions'][condition] = {
                    'trends': [],
                    'contributing_clinics': []
                }
            
            self.collective_knowledge['seasonal_trends'][season]['conditions'][condition]['trends'].append({
                'trend': trend,
                'clinic_id': clinic_id,
                'date': datetime.utcnow().isoformat()
            })
            
            if clinic_id not in self.collective_knowledge['seasonal_trends'][season]['contributing_clinics']:
                self.collective_knowledge['seasonal_trends'][season]['contributing_clinics'].append(clinic_id)
    
    def _update_regional_variations(self, clinic_id: str, data: Dict[str, Any]):
        """Update regional variations knowledge."""
        
        if clinic_id in self.collective_knowledge['regional_variations']:
            region_data = self.collective_knowledge['regional_variations'][clinic_id]
            
            # Update regional data
            region_data['local_diseases'].extend(data.get('local_diseases', []))
            region_data['local_treatments'].extend(data.get('local_treatments', []))
            region_data['cultural_considerations'].extend(data.get('cultural_considerations', []))
            region_data['last_updated'] = datetime.utcnow().isoformat()
    
    def _apply_rule_filters(self, rules: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply filters to triage rules."""
        
        filtered_rules = {}
        
        for key, rule in rules.items():
            include_rule = True
            
            # Filter by condition
            if 'conditions' in filters:
                if rule.get('condition') not in filters['conditions']:
                    include_rule = False
            
            # Filter by triage level
            if 'triage_levels' in filters:
                if rule.get('triage_level') not in filters['triage_levels']:
                    include_rule = False
            
            # Filter by evidence level
            if 'evidence_levels' in filters:
                if rule.get('evidence_level') not in filters['evidence_levels']:
                    include_rule = False
            
            if include_rule:
                filtered_rules[key] = rule
        
        return filtered_rules
    
    def _analyze_disease_patterns(self) -> Dict[str, Any]:
        """Analyze collective disease patterns."""
        
        analysis = {}
        
        for condition, data in self.collective_knowledge['disease_patterns'].items():
            analysis[condition] = {
                'common_symptoms': self._get_most_common(data['symptoms']),
                'regional_spread': len(data['contributing_clinics']),
                'symptom_diversity': len(set(data['symptoms']))
            }
        
        return analysis
    
    def _analyze_treatment_outcomes(self) -> Dict[str, Any]:
        """Analyze collective treatment outcomes."""
        
        analysis = {}
        
        for key, data in self.collective_knowledge['treatment_outcomes'].items():
            analysis[key] = {
                'success_rate': data['success_rate'],
                'total_cases': len(data['outcomes']),
                'contributing_clinics': len(data['contributing_clinics']),
                'common_outcomes': self._get_most_common(data['outcomes'], 'outcome')
            }
        
        return analysis
    
    def _analyze_seasonal_trends(self) -> Dict[str, Any]:
        """Analyze seasonal trends."""
        
        analysis = {}
        
        for season, data in self.collective_knowledge['seasonal_trends'].items():
            analysis[season] = {
                'active_conditions': len(data['conditions']),
                'contributing_clinics': len(data['contributing_clinics']),
                'trending_conditions': []
            }
            
            # Find trending conditions
            for condition, condition_data in data['conditions'].items():
                if len(condition_data['trends']) >= 3:
                    recent_trends = condition_data['trends'][-3:]
                    trend_direction = 'increasing' if len([t for t in recent_trends if t.get('trend') == 'increasing']) >= 2 else 'stable'
                    
                    analysis[season]['trending_conditions'].append({
                        'condition': condition,
                        'trend': trend_direction
                    })
        
        return analysis
    
    def _analyze_regional_variations(self) -> Dict[str, Any]:
        """Analyze regional variations."""
        
        analysis = {}
        
        for clinic_id, data in self.collective_knowledge['regional_variations'].items():
            clinic = self.registered_clinics.get(clinic_id, {})
            region = clinic.get('registration', {}).get('region', 'Unknown')
            
            analysis[clinic_id] = {
                'region': region,
                'unique_diseases': len(set(data['local_diseases'])),
                'unique_treatments': len(set(data['local_treatments'])),
                'cultural_considerations_count': len(data['cultural_considerations']),
                'last_updated': data.get('last_updated')
            }
        
        return analysis
    
    def _get_most_common(self, items: List[Dict], key: str) -> List[Any]:
        """Get most common items from a list."""
        
        if not items:
            return []
        
        counts = {}
        for item in items:
            value = item.get(key)
            if value:
                counts[value] = counts.get(value, 0) + 1
        
        # Sort by count and return top 5
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items[:5]]
    
    def _calculate_data_freshness(self) -> Dict[str, Any]:
        """Calculate data freshness metrics."""
        
        now = datetime.utcnow()
        freshness = {
            'overall_score': 0,
            'rule_freshness': {},
            'knowledge_freshness': {}
        }
        
        # Calculate rule freshness
        for key, rule in self.consensus_rules['rules'].items():
            if rule.get('created_date'):
                rule_age = now - datetime.fromisoformat(rule['created_date'])
                days_old = rule_age.days
                
                if days_old <= 7:
                    score = 1.0
                elif days_old <= 30:
                    score = 0.8
                elif days_old <= 90:
                    score = 0.6
                else:
                    score = 0.4
                
                freshness['rule_freshness'][key] = score
        
        # Calculate knowledge freshness
        for category, data in self.collective_knowledge.items():
            if category == 'disease_patterns':
                freshness['knowledge_freshness'][category] = self._calculate_pattern_freshness(data)
            elif category == 'treatment_outcomes':
                freshness['knowledge_freshness'][category] = self._calculate_outcome_freshness(data)
            else:
                freshness['knowledge_freshness'][category] = 0.5  # Default score
        
        # Calculate overall freshness
        all_scores = list(freshness['rule_freshness'].values()) + list(freshness['knowledge_freshness'].values())
        if all_scores:
            freshness['overall_score'] = sum(all_scores) / len(all_scores)
        
        return freshness
    
    def _calculate_pattern_freshness(self, patterns: Dict[str, Any]) -> float:
        """Calculate freshness score for disease patterns."""
        
        if not patterns:
            return 0.0
        
        total_contributions = sum(len(data.get('contributing_clinics', [])) for data in patterns.values())
        if total_contributions == 0:
            return 0.0
        
        # More recent contributions get higher scores
        now = datetime.utcnow()
        weighted_score = 0
        
        for condition, data in patterns.items():
            for clinic_id in data.get('contributing_clinics', []):
                # Get clinic registration date
                clinic = self.registered_clinics.get(clinic_id, {})
                if clinic and clinic.get('registered_at'):
                    reg_date = datetime.fromisoformat(clinic['registered_at'])
                    days_old = (now - reg_date).days
                    
                    # Recent contributions get higher weight
                    if days_old <= 30:
                        weighted_score += 1.0
                    elif days_old <= 90:
                        weighted_score += 0.7
                    else:
                        weighted_score += 0.4
        
        return weighted_score / total_contributions if total_contributions > 0 else 0.0
    
    def _calculate_outcome_freshness(self, outcomes: Dict[str, Any]) -> float:
        """Calculate freshness score for treatment outcomes."""
        
        if not outcomes:
            return 0.0
        
        total_outcomes = sum(len(data.get('outcomes', [])) for data in outcomes.values())
        if total_outcomes == 0:
            return 0.0
        
        # More recent outcomes get higher scores
        now = datetime.utcnow()
        weighted_score = 0
        
        for key, data in outcomes.items():
            for outcome in data.get('outcomes', []):
                if outcome.get('date'):
                    outcome_date = datetime.fromisoformat(outcome['date'])
                    days_old = (now - outcome_date).days
                    
                    # Recent outcomes get higher weight
                    if days_old <= 30:
                        weighted_score += 1.0
                    elif days_old <= 90:
                        weighted_score += 0.7
                    else:
                        weighted_score += 0.4
        
        return weighted_score / total_outcomes if total_outcomes > 0 else 0.0
    
    def _initialize_sample_data(self):
        """Initialize with sample data for testing."""
        
        # Sample consensus rules
        self.consensus_rules['rules'] = {
            'malaria_emergency': {
                'rule_id': 'consensus_malaria_emergency',
                'version': '1.0',
                'condition': 'malaria',
                'symptoms': ['fever', 'chills', 'headache', 'muscle_pain'],
                'triage_level': 'emergency',
                'evidence_level': 'A',
                'source': 'consensus',
                'created_date': '2024-01-01T00:00:00Z'
            },
            'diabetes_routine': {
                'rule_id': 'consensus_diabetes_routine',
                'version': '1.0',
                'condition': 'diabetes_maintenance',
                'symptoms': ['high_glucose', 'increased_thirst', 'frequent_urination'],
                'triage_level': 'routine',
                'evidence_level': 'B',
                'source': 'consensus',
                'created_date': '2024-01-01T00:00:00Z'
            }
        }
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get overall DEDAN Hub network status."""
        
        return {
            'total_clinics': len(self.registered_clinics),
            'active_clinics': len([c for c in self.registered_clinics.values() if c.get('status') == 'active']),
            'total_rules': len(self.triage_rules),
            'consensus_rules': len(self.consensus_rules['rules']),
            'knowledge_categories': list(self.collective_knowledge.keys()),
            'hub_version': self.consensus_rules['version'],
            'last_updated': datetime.utcnow().isoformat()
        }

# Global instance
dedan_hub = DEDANHub()
