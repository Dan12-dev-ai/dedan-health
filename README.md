# DEDAN Health Platform

**Digital Empathy-Driven AI Navigator** for primary-care triage and virtual clinic services in underserved regions.

## Platform Overview

DEDAN Health is a world-class AI-powered healthcare platform designed for low-resource regions (Africa, SE Asia, Latin America) that provides:

- **AI-Powered Triage**: DEDAN HealthEngine with clinical safety guards
- **Multi-Platform Support**: Web PWA, Mobile Apps, WhatsApp/SMS integration
- **Low-Bandwidth Optimized**: Works on 2G/3G networks
- **Multilingual**: English + local languages (Amharic, Swahili, etc.)
- **Clinically Safe**: WHO and local health ministry guidelines integration

## Architecture

```
DEDAN-Health/
├── backend/                 # DEDAN HealthEngine (FastAPI)
├── web-portal/             # DEDAN Health Portal (React PWA)
├── mobile-app/             # DEDAN Health App (React Native)
├── messaging-backend/      # WhatsApp/SMS integration
├── clinic-dashboard/       # Clinic Console
└── data/                   # Clinical guidelines and datasets
```

## Core Components

### 🧠 DEDAN HealthEngine
- LLM-based triage with RAG over clinical guidelines
- Safety guards for emergency detection
- Structured JSON triage decisions
- REST API endpoints

### 🖥️ DEDAN Health Portal
- Progressive Web App with offline support
- Interactive triage chat interface
- Color-coded triage levels
- Local language support

### 📱 DEDAN Mobile App
- Cross-platform (React Native)
- Voice input support
- Clinic finder
- Follow-up coaching

### 💬 DEDAN Messaging
- WhatsApp Business API integration
- SMS-compatible responses
- Emergency flagging

### 🏥 Clinic Console
- Triage report management
- Data analytics dashboard
- Export capabilities

## Getting Started

1. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

2. **Web Portal**:
   ```bash
   cd web-portal
   npm install
   npm run dev
   ```

3. **Mobile App**:
   ```bash
   cd mobile-app
   npm install
   npx react-native run-android
   ```

## Safety & Compliance

- **Medical Disclaimer**: "Not a replacement for doctors"
- **Data Privacy**: Anonymized triage data storage
- **Clinical Guidelines**: WHO, Ethiopia MoH, and local health authorities
- **Emergency Protocol**: Immediate flagging of high-risk symptoms

## DEDAN Brand

- **Colors**: Medical-friendly blue and white scheme
- **Logo**: "DEDAN Health"
- **Mission**: AI-powered primary care for underserved communities

## License

© 2025 DEDAN Health - Digital Empathy-Driven AI Navigator
