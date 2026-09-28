#!/usr/bin/env python
"""
Test script for clinical-guidance endpoint without full agent dependencies.
"""
import sys
import os
sys.path.insert(0, '.')

# Mock the problematic imports before importing main_v2
import types

# Create mock modules
for mod_name in ['agents.coordinator_agent', 'agents.triage_agent', 'agents.safety_guard_agent', 
                 'agents.guideline_agent', 'agents.risk_prediction_agent', 'agents.base_agent',
                 'data_flywheel']:
    mod = types.ModuleType(mod_name)
    mod.CoordinatorAgent = type('CoordinatorAgent', (), {})
    mod.DedandDataFlywheel = type('DedandDataFlywheel', (), {})
    sys.modules[mod_name] = mod

# Now test import
try:
    import main_v2
    print("main_v2 imported successfully")
    
    # Test FastAPI app creation
    from fastapi.testclient import TestClient
    client = TestClient(main_v2.app)
    print("FastAPI app created successfully")
    
    # Test health endpoint
    response = client.get("/api/health")
    print(f"Health check: {response.status_code} - {response.json()}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()