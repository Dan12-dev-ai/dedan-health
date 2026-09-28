import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import httpx
import logging

from models_v2 import (
    EMRPatientRecord, EMRTriageEvent, TriageLevel, RiskScore
)

# Configure logging
logger = logging.getLogger(__name__)

class EMRConnector:
    """
    DEDAN EMR/Clinic-Scheduling Connector - Integrates with external EMR systems.
    Provides standardized JSON schema for patient data and triage events.
    """
    
    def __init__(self):
        self.emr_systems = {
            'openemr': {
                'base_url': os.getenv('OPENEMR_URL', 'https://demo.open-emr.org/openemr'),
                'api_key': os.getenv('OPENEMR_API_KEY'),
                'patient_endpoint': '/api/patient',
                'encounter_endpoint': '/api/encounter',
                'auth_type': 'api_key'
            },
            'epic': {
                'base_url': os.getenv('EPIC_URL', 'https://epic.example.com'),
                'api_key': os.getenv('EPIC_API_KEY'),
                'patient_endpoint': '/api/v1/patient',
                'encounter_endpoint': '/api/v1/encounter',
                'auth_type': 'oauth2'
            },
            'cerner': {
                'base_url': os.getenv('CERNER_URL', 'https://fhir.cerner.com'),
                'api_key': os.getenv('CERNER_API_KEY'),
                'patient_endpoint': '/api/v1/Patient',
                'encounter_endpoint': '/api/v1/Encounter',
                'auth_type': 'oauth2'
            },
            'google_calendar': {
                'base_url': 'https://www.googleapis.com/calendar/v3',
                'api_key': os.getenv('GOOGLE_CALENDAR_API_KEY'),
                'calendar_id': os.getenv('GOOGLE_CALENDAR_ID', 'primary'),
                'auth_type': 'oauth2'
            },
            'calendly': {
                'base_url': os.getenv('CALENDLY_URL', 'https://api.calendly.com'),
                'api_key': os.getenv('CALENDLY_API_KEY'),
                'event_types': ['triage_appointment', 'follow_up'],
                'auth_type': 'api_key'
            }
        }
        
        self.patient_mapping = {}  # Maps DEDAN patient IDs to EMR patient IDs
        self.appointment_mapping = {}  # Maps triage events to appointments
        
        logger.info("EMR Connector initialized")
    
    async def read_patient_data(self, emr_system: str, patient_id: str) -> Optional[EMRPatientRecord]:
        """
        Read patient data from external EMR system.
        Returns standardized patient record.
        """
        
        try:
            if emr_system not in self.emr_systems:
                logger.error(f"Unsupported EMR system: {emr_system}")
                return None
            
            system_config = self.emr_systems[emr_system]
            
            # Check if we have a mapped EMR patient ID
            emr_patient_id = self.patient_mapping.get(patient_id)
            if not emr_patient_id:
                # Try to find patient by demographics
                emr_patient_id = await self._find_patient_by_demographics(emr_system, patient_id)
                if emr_patient_id:
                    self.patient_mapping[patient_id] = emr_patient_id
            
            if not emr_patient_id:
                logger.error(f"Patient {patient_id} not found in {emr_system}")
                return None
            
            # Fetch patient data from EMR
            patient_data = await self._fetch_patient_from_emr(emr_system, emr_patient_id)
            if not patient_data:
                return None
            
            # Convert to standardized format
            standardized_record = EMRPatientRecord(
                patient_id=patient_id,
                external_system=emr_system,
                external_id=emr_patient_id,
                demographic_data=patient_data.get('demographics', {}),
                medical_history=patient_data.get('medical_history', []),
                medications=patient_data.get('medications', []),
                allergies=patient_data.get('allergies', []),
                last_updated=datetime.utcnow()
            )
            
            logger.info(f"Read patient data for {patient_id} from {emr_system}")
            return standardized_record
            
        except Exception as e:
            logger.error(f"Failed to read patient data: {e}")
            return None
    
    async def write_triage_event(self, emr_system: str, triage_event: EMRTriageEvent) -> bool:
        """
        Write DEDAN triage event back to EMR system.
        """
        
        try:
            if emr_system not in self.emr_systems:
                logger.error(f"Unsupported EMR system: {emr_system}")
                return False
            
            system_config = self.emr_systems[emr_system]
            
            # Prepare triage event for EMR
            emr_triage_data = self._prepare_triage_for_emr(triage_event, emr_system)
            
            # Write to EMR system
            success = await self._write_triage_to_emr(emr_system, emr_triage_data)
            
            if success:
                # Update sync status
                triage_event.sync_status = "synced"
                logger.info(f"Triage event synced to {emr_system}: {triage_event.session_id}")
            else:
                triage_event.sync_status = "failed"
                logger.error(f"Failed to sync triage event to {emr_system}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to write triage event: {e}")
            return False
    
    async def schedule_appointment(
        self,
        emr_system: str,
        patient_id: str,
        triage_level: TriageLevel,
        preferred_time: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Schedule appointment based on triage level and clinic capacity.
        """
        
        try:
            # Determine appointment urgency and duration
            appointment_config = self._get_appointment_config(triage_level)
            
            # Get available slots
            available_slots = await self._get_available_appointment_slots(
                emr_system, preferred_time, appointment_config
            )
            
            if not available_slots:
                logger.warning(f"No available slots in {emr_system}")
                return None
            
            # Select best slot
            selected_slot = self._select_best_slot(available_slots, preferred_time)
            
            # Create appointment
            appointment_data = {
                'patient_id': patient_id,
                'triage_level': triage_level,
                'slot': selected_slot,
                'duration': appointment_config['duration'],
                'urgency': appointment_config['urgency'],
                'notes': notes,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Schedule in EMR system
            if emr_system in ['google_calendar', 'calendly']:
                appointment_id = await self._schedule_in_calendar_system(emr_system, appointment_data)
            else:
                appointment_id = await self._schedule_in_emr_system(emr_system, appointment_data)
            
            if appointment_id:
                # Update appointment mapping
                self.appointment_mapping[appointment_data['slot']['start_time']] = appointment_id
                
                logger.info(f"Appointment scheduled in {emr_system}: {appointment_id}")
                return {
                    'appointment_id': appointment_id,
                    'scheduled_time': selected_slot['start_time'],
                    'duration': appointment_config['duration'],
                    'location': selected_slot.get('location', 'Main Clinic'),
                    'confirmation_required': appointment_config['confirmation_required']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to schedule appointment: {e}")
            return None
    
    async def sync_patient_data(self, emr_system: str, patient_id: str) -> Dict[str, Any]:
        """
        Synchronize patient data between DEDAN and EMR systems.
        """
        
        try:
            # Read from EMR
            emr_record = await self.read_patient_data(emr_system, patient_id)
            if not emr_record:
                return {'status': 'failed', 'error': 'Patient not found in EMR'}
            
            # Get DEDAN patient data (this would come from DEDAN database)
            dedan_data = await self._get_dedan_patient_data(patient_id)
            
            # Compare and merge data
            sync_result = self._compare_and_merge_data(emr_record, dedan_data)
            
            # Update systems as needed
            updates = []
            
            if sync_result['emr_needs_update']:
                success = await self._update_emr_patient(emr_system, patient_id, sync_result['merged_data'])
                updates.append({'system': 'emr', 'success': success})
            
            if sync_result['dedan_needs_update']:
                success = await self._update_dedan_patient(patient_id, sync_result['merged_data'])
                updates.append({'system': 'dedan', 'success': success})
            
            return {
                'status': 'completed',
                'updates': updates,
                'merged_fields': sync_result['merged_fields'],
                'sync_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to sync patient data: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _find_patient_by_demographics(self, emr_system: str, patient_id: str) -> Optional[str]:
        """Find patient in EMR by demographics search."""
        
        try:
            # Get DEDAN patient data
            dedan_data = await self._get_dedan_patient_data(patient_id)
            if not dedan_data:
                return None
            
            # Search EMR by demographics
            search_params = {
                'name': dedan_data.get('name'),
                'date_of_birth': dedan_data.get('date_of_birth'),
                'phone': dedan_data.get('phone'),
                'email': dedan_data.get('email')
            }
            
            # Remove None values
            search_params = {k: v for k, v in search_params.items() if v is not None}
            
            if not search_params:
                return None
            
            # Search in EMR system
            emr_patient_id = await self._search_emr_patients(emr_system, search_params)
            
            if emr_patient_id:
                # Store mapping
                self.patient_mapping[patient_id] = emr_patient_id
                logger.info(f"Found EMR patient mapping: {patient_id} -> {emr_patient_id}")
            
            return emr_patient_id
            
        except Exception as e:
            logger.error(f"Failed to find patient by demographics: {e}")
            return None
    
    async def _fetch_patient_from_emr(self, emr_system: str, emr_patient_id: str) -> Optional[Dict[str, Any]]:
        """Fetch patient data from EMR system."""
        
        try:
            system_config = self.emr_systems[emr_system]
            
            if emr_system == 'openemr':
                return await self._fetch_openemr_patient(system_config, emr_patient_id)
            elif emr_system == 'epic':
                return await self._fetch_epic_patient(system_config, emr_patient_id)
            elif emr_system == 'cerner':
                return await self._fetch_cerner_patient(system_config, emr_patient_id)
            else:
                logger.error(f"EMR system {emr_system} not implemented")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch patient from {emr_system}: {e}")
            return None
    
    async def _fetch_openemr_patient(self, config: Dict[str, Any], patient_id: str) -> Optional[Dict[str, Any]]:
        """Fetch patient from OpenEMR system."""
        
        try:
            headers = {'Authorization': f"Bearer {config['api_key']}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config['base_url']}{config['patient_endpoint']}/{patient_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"OpenEMR API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"OpenEMR fetch error: {e}")
            return None
    
    async def _fetch_epic_patient(self, config: Dict[str, Any], patient_id: str) -> Optional[Dict[str, Any]]:
        """Fetch patient from Epic system."""
        
        try:
            # Epic uses FHIR R4 resources
            headers = {'Authorization': f"Bearer {config['api_key']}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config['base_url']}{config['patient_endpoint']}/{patient_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    fhir_data = response.json()
                    return self._convert_fhir_to_standard(fhir_data)
                else:
                    logger.error(f"Epic API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Epic fetch error: {e}")
            return None
    
    async def _fetch_cerner_patient(self, config: Dict[str, Any], patient_id: str) -> Optional[Dict[str, Any]]:
        """Fetch patient from Cerner system."""
        
        try:
            # Cerner uses FHIR resources
            headers = {'Authorization': f"Bearer {config['api_key']}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config['base_url']}{config['patient_endpoint']}/{patient_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    fhir_data = response.json()
                    return self._convert_fhir_to_standard(fhir_data)
                else:
                    logger.error(f"Cerner API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Cerner fetch error: {e}")
            return None
    
    def _convert_fhir_to_standard(self, fhir_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert FHIR patient data to standard format."""
        
        try:
            # Extract basic demographics from FHIR Patient resource
            name = fhir_data.get('name', [{}])[0]
            birth_date = fhir_data.get('birthDate')
            
            demographics = {
                'name': f"{name.get('given', '')} {name.get('family', '')}".strip(),
                'date_of_birth': birth_date,
                'gender': fhir_data.get('gender'),
                'phone': next((telecom.get('value') for telecom in fhir_data.get('telecom', []) if telecom.get('system') == 'phone'), None),
                'email': next((telecom.get('value') for telecom in fhir_data.get('telecom', []) if telecom.get('system') == 'email'), None),
                'address': self._format_fhir_address(fhir_data.get('address', []))
            }
            
            # Extract medical history
            medical_history = []
            for condition in fhir_data.get('condition', []):
                medical_history.append({
                    'condition': condition.get('code', {}).get('text', ''),
                    'onset_date': condition.get('onsetDateTime'),
                    'severity': condition.get('severity', [{}])[0].get('coding', [{}])[0].get('display', '')
                })
            
            # Extract medications
            medications = []
            for med in fhir_data.get('medicationStatement', []):
                medications.append({
                    'medication': med.get('medicationCode', {}).get('text', ''),
                    'dosage': med.get('dosage', [{}])[0].get('text', ''),
                    'start_date': med.get('effectiveDateTime')
                })
            
            # Extract allergies
            allergies = []
            for allergy in fhir_data.get('allergyIntolerance', []):
                allergies.append(allergy.get('substance', {}).get('coding', [{}])[0].get('display', ''))
            
            return {
                'demographics': demographics,
                'medical_history': medical_history,
                'medications': medications,
                'allergies': allergies
            }
            
        except Exception as e:
            logger.error(f"FHIR conversion error: {e}")
            return {'demographics': {}, 'medical_history': [], 'medications': [], 'allergies': []}
    
    def _format_fhir_address(self, addresses: List[Dict[str, Any]]) -> str:
        """Format FHIR address to string."""
        
        if not addresses:
            return ""
        
        address = addresses[0]
        parts = [
            address.get('line', [])[0],
            address.get('city', ''),
            address.get('state', ''),
            address.get('postalCode', '')
        ]
        
        return ', '.join(filter(None, parts))
    
    def _prepare_triage_for_emr(self, triage_event: EMRTriageEvent, emr_system: str) -> Dict[str, Any]:
        """Prepare triage event for EMR system."""
        
        base_data = {
            'patient_id': triage_event.patient_id,
            'triage_date': triage_event.triage_date.isoformat(),
            'triage_level': triage_event.triage_level,
            'risk_score': triage_event.risk_score,
            'symptoms': triage_event.symptoms,
            'recommendations': triage_event.recommendations,
            'requires_follow_up': triage_event.requires_follow_up,
            'follow_up_date': triage_event.follow_up_date.isoformat() if triage_event.follow_up_date else None,
            'source_system': 'DEDAN_HealthEngine_v2',
            'event_type': 'DEDAN_Triage_Event'
        }
        
        # System-specific formatting
        if emr_system in ['epic', 'cerner']:
            # Convert to FHIR Encounter format
            return self._convert_triage_to_fhir(base_data)
        elif emr_system == 'openemr':
            # OpenEMR specific format
            return self._convert_triage_to_openemr(base_data)
        else:
            # Generic format
            return base_data
    
    def _convert_triage_to_fhir(self, triage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert triage data to FHIR Encounter format."""
        
        return {
            'resourceType': 'Encounter',
            'status': 'finished',
            'class': {
                'system': 'http://terminology.hl7.org/CodeSystem/v3/ActCode',
                'code': 'AMB',
                'display': 'Ambulatory'
            },
            'subject': {
                'reference': f"Patient/{triage_data['patient_id']}"
            },
            'period': {
                'start': triage_data['triage_date']
            },
            'reasonCode': [{
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': self._map_triage_to_snomed(triage_data['triage_level']),
                    'display': f"DEDAN Triage: {triage_data['triage_level']}"
                }],
                'text': triage_data['symptoms']
            }],
            'extension': [{
                'url': 'http://dedan.health/fhir/StructureDefinition/triage-details',
                'extension': [
                    {
                        'url': 'riskScore',
                        'valueString': triage_data['risk_score']
                    },
                    {
                        'url': 'recommendations',
                        'valueString': json.dumps(triage_data['recommendations'])
                    }
                ]
            }]
        }
    
    def _convert_triage_to_openemr(self, triage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert triage data to OpenEMR format."""
        
        return {
            'form_id': 'dedan_triage',
            'patient_id': triage_data['patient_id'],
            'encounter_date': triage_data['triage_date'],
            'category': 'triage',
            'triage_level': triage_data['triage_level'],
            'risk_score': triage_data['risk_score'],
            'chief_complaint': triage_data['symptoms'],
            'assessment': 'DEDAN AI Triage Assessment',
            'plan': json.dumps(triage_data['recommendations']),
            'follow_up_required': triage_data['requires_follow_up'],
            'follow_up_date': triage_data['follow_up_date'],
            'source': 'DEDAN_HealthEngine_v2'
        }
    
    def _map_triage_to_snomed(self, triage_level: str) -> str:
        """Map DEDAN triage levels to SNOMED codes."""
        
        snomed_mapping = {
            'emergency': '3948009',  # Emergency encounter
            'urgent': '270427003',    # Urgent encounter
            'routine': '308335008',    # Routine encounter
            'self_care': '394777002'  # Self-care encounter
        }
        
        return snomed_mapping.get(triage_level, '3948009')
    
    def _get_appointment_config(self, triage_level: TriageLevel) -> Dict[str, Any]:
        """Get appointment configuration based on triage level."""
        
        configs = {
            'emergency': {
                'urgency': 'emergency',
                'duration': 60,  # 60 minutes
                'window_hours': 2,  # Within 2 hours
                'confirmation_required': True
            },
            'urgent': {
                'urgency': 'urgent',
                'duration': 30,  # 30 minutes
                'window_hours': 24,  # Within 24 hours
                'confirmation_required': True
            },
            'routine': {
                'urgency': 'routine',
                'duration': 20,  # 20 minutes
                'window_hours': 168,  # Within 1 week
                'confirmation_required': False
            },
            'self_care': {
                'urgency': 'routine',
                'duration': 15,  # 15 minutes
                'window_hours': 336,  # Within 2 weeks
                'confirmation_required': False
            }
        }
        
        return configs.get(triage_level, configs['routine'])
    
    async def _get_available_appointment_slots(
        self,
        emr_system: str,
        preferred_time: Optional[datetime],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get available appointment slots from scheduling system."""
        
        try:
            if emr_system == 'google_calendar':
                return await self._get_google_calendar_slots(preferred_time, config)
            elif emr_system == 'calendly':
                return await self._get_calendly_slots(preferred_time, config)
            else:
                # For EMR systems, return sample slots
                return self._generate_sample_slots(preferred_time, config)
                
        except Exception as e:
            logger.error(f"Failed to get appointment slots: {e}")
            return []
    
    async def _get_google_calendar_slots(self, preferred_time: Optional[datetime], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available slots from Google Calendar."""
        
        # This would integrate with Google Calendar API
        # For now, return sample slots
        return self._generate_sample_slots(preferred_time, config)
    
    async def _get_calendly_slots(self, preferred_time: Optional[datetime], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available slots from Calendly."""
        
        # This would integrate with Calendly API
        # For now, return sample slots
        return self._generate_sample_slots(preferred_time, config)
    
    def _generate_sample_slots(self, preferred_time: Optional[datetime], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate sample appointment slots for testing."""
        
        slots = []
        base_time = preferred_time or datetime.utcnow()
        
        # Generate slots for next 7 days
        for day_offset in range(7):
            date = base_time + timedelta(days=day_offset)
            
            # Generate 3 slots per day (morning, afternoon, evening)
            for hour in [9, 14, 16]:
                slot_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # Only include future slots
                if slot_time > datetime.utcnow():
                    slots.append({
                        'start_time': slot_time.isoformat(),
                        'end_time': (slot_time + timedelta(minutes=config['duration'])).isoformat(),
                        'duration': config['duration'],
                        'location': 'Main Clinic',
                        'available': True
                    })
        
        return slots
    
    def _select_best_slot(self, slots: List[Dict[str, Any]], preferred_time: Optional[datetime]) -> Dict[str, Any]:
        """Select best appointment slot based on preferences."""
        
        if not slots:
            return {}
        
        if preferred_time:
            # Find closest slot to preferred time
            preferred_timestamp = preferred_time.timestamp()
            
            best_slot = min(slots, key=lambda slot: abs(
                datetime.fromisoformat(slot['start_time']).timestamp() - preferred_timestamp
            ))
        else:
            # Take first available slot
            best_slot = slots[0]
        
        return best_slot
    
    async def _get_dedan_patient_data(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient data from DEDAN system."""
        
        # This would query DEDAN database
        # For now, return sample data
        return {
            'name': 'John Doe',
            'date_of_birth': '1980-01-01',
            'phone': '+1234567890',
            'email': 'john.doe@example.com'
        }
    
    async def _update_dedan_patient(self, patient_id: str, updated_data: Dict[str, Any]) -> bool:
        """Update patient data in DEDAN system."""
        
        # This would update DEDAN database
        logger.info(f"Updated DEDAN patient data for {patient_id}")
        return True
    
    def _compare_and_merge_data(self, emr_record: EMRPatientRecord, dedan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare and merge patient data from EMR and DEDAN."""
        
        merged_data = {}
        merged_fields = []
        emr_needs_update = False
        dedan_needs_update = False
        
        # Compare demographics
        emr_demo = emr_record.demographic_data
        dedan_demo = dedan_data
        
        for field in ['name', 'date_of_birth', 'phone', 'email']:
            emr_value = emr_demo.get(field)
            dedan_value = dedan_demo.get(field)
            
            if emr_value and dedan_value:
                if emr_value != dedan_value:
                    # Use most recent data
                    merged_data[field] = emr_value if emr_record.last_updated > datetime.utcnow() - timedelta(days=1) else dedan_value
                    merged_fields.append(field)
                    emr_needs_update = True
                    dedan_needs_update = True
                else:
                    merged_data[field] = emr_value  # They match
            elif emr_value:
                merged_data[field] = emr_value
            elif dedan_value:
                merged_data[field] = dedan_value
                dedan_needs_update = True
        
        return {
            'merged_data': merged_data,
            'merged_fields': merged_fields,
            'emr_needs_update': emr_needs_update,
            'dedan_needs_update': dedan_needs_update
        }
    
    async def _write_triage_to_emr(self, emr_system: str, triage_data: Dict[str, Any]) -> bool:
        """Write triage event to EMR system."""
        
        try:
            system_config = self.emr_systems[emr_system]
            
            if emr_system == 'openemr':
                return await self._write_triage_to_openemr(system_config, triage_data)
            elif emr_system in ['epic', 'cerner']:
                return await self._write_triage_to_fhir(system_config, triage_data)
            else:
                logger.error(f"EMR system {emr_system} write not implemented")
                return False
                
        except Exception as e:
            logger.error(f"Failed to write triage to {emr_system}: {e}")
            return False
    
    async def _write_triage_to_openemr(self, config: Dict[str, Any], triage_data: Dict[str, Any]) -> bool:
        """Write triage event to OpenEMR."""
        
        try:
            headers = {'Authorization': f"Bearer {config['api_key']}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config['base_url']}{config['encounter_endpoint']}",
                    json=triage_data,
                    headers=headers
                )
                
                return response.status_code == 201
                
        except Exception as e:
            logger.error(f"OpenEMR write error: {e}")
            return False
    
    async def _write_triage_to_fhir(self, config: Dict[str, Any], triage_data: Dict[str, Any]) -> bool:
        """Write triage event to FHIR-based EMR (Epic/Cerner)."""
        
        try:
            headers = {'Authorization': f"Bearer {config['api_key']}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config['base_url']}{config['encounter_endpoint']}",
                    json=triage_data,
                    headers=headers
                )
                
                return response.status_code == 201
                
        except Exception as e:
            logger.error(f"FHIR write error: {e}")
            return False
    
    async def _search_emr_patients(self, emr_system: str, search_params: Dict[str, str]) -> Optional[str]:
        """Search for patients in EMR system."""
        
        # This would implement patient search in EMR system
        # For now, return None
        logger.info(f"Searching {emr_system} with params: {search_params}")
        return None
    
    async def _schedule_in_calendar_system(self, calendar_system: str, appointment_data: Dict[str, Any]) -> Optional[str]:
        """Schedule appointment in calendar system."""
        
        try:
            if calendar_system == 'google_calendar':
                return await self._schedule_google_calendar(appointment_data)
            elif calendar_system == 'calendly':
                return await self._schedule_calendly(appointment_data)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to schedule in {calendar_system}: {e}")
            return None
    
    async def _schedule_in_emr_system(self, emr_system: str, appointment_data: Dict[str, Any]) -> Optional[str]:
        """Schedule appointment in EMR system."""
        
        # This would implement appointment scheduling in EMR
        # For now, return sample ID
        appointment_id = f"appointment_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Scheduled appointment in {emr_system}: {appointment_id}")
        return appointment_id
    
    async def _schedule_google_calendar(self, appointment_data: Dict[str, Any]) -> Optional[str]:
        """Schedule appointment in Google Calendar."""
        
        # This would integrate with Google Calendar API
        # For now, return sample ID
        event_id = f"google_event_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Scheduled Google Calendar event: {event_id}")
        return event_id
    
    async def _schedule_calendly(self, appointment_data: Dict[str, Any]) -> Optional[str]:
        """Schedule appointment in Calendly."""
        
        # This would integrate with Calendly API
        # For now, return sample ID
        event_id = f"calendly_event_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Scheduled Calendly event: {event_id}")
        return event_id

# Global instance
emr_connector = EMRConnector()
