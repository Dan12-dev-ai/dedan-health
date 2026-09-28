# DEDAN Health - Separate Web & Mobile App Architecture

## 🎯 Core Architecture Rule

**"Yes. Web app and mobile app are SEPARATE, independent UI projects.
They share the SAME backend API, but their codebases live in /web and /mobile and can be developed, tested, and deployed independently."**

---

## 📁 Folder Structure Blueprint

```
DEDAN-Health/
├── backend/                    # Shared FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI application entry
│   │   ├── models/             # Database models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── triage.py
│   │   │   ├── subscription.py
│   │   │   └── billing.py
│   │   ├── services/           # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── triage_service.py
│   │   │   ├── safety_guard.py
│   │   │   ├── billing_service.py
│   │   │   ├── ai_engine.py
│   │   │   └── image_analysis.py
│   │   ├── api/                # API routers
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── triage.py
│   │   │   │   ├── users.py
│   │   │   │   ├── billing.py
│   │   │   │   ├── subscriptions.py
│   │   │   │   └── health.py
│   │   │   └── dependencies.py
│   │   ├── core/               # Core functionality
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   ├── database.py
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   └── utils/              # Utility functions
│   │       ├── __init__.py
│   │       ├── helpers.py
│   │       └── validators.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── README.md
│
├── web/                        # SEPARATE React PWA project
│   ├── public/
│   │   ├── index.html
│   │   ├── manifest.json
│   │   └── service-worker.js
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── TriageChat.tsx
│   │   │   ├── PatientProfile.tsx
│   │   │   ├── PricingPage.tsx
│   │   │   └── Dashboard.tsx
│   │   ├── pages/              # Page components
│   │   │   ├── HomePage.tsx
│   │   │   ├── TriagePage.tsx
│   │   │   └── BillingPage.tsx
│   │   ├── services/           # API service layer
│   │   │   ├── api.ts          # HTTP client for backend
│   │   │   ├── auth.ts
│   │   │   └── types.ts
│   │   ├── hooks/              # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   └── useTriage.ts
│   │   ├── utils/              # Utility functions
│   │   │   ├── helpers.ts
│   │   │   └── constants.ts
│   │   ├── types/              # TypeScript types
│   │   │   ├── api.ts
│   │   │   ├── user.ts
│   │   │   └── triage.ts
│   │   ├── styles/             # CSS/styling
│   │   │   ├── globals.css
│   │   │   └── components.css
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── README.md
│
├── mobile/                     # SEPARATE React Native project
│   ├── android/                # Android-specific code
│   ├── ios/                    # iOS-specific code
│   ├── src/
│   │   ├── components/         # React Native components
│   │   │   ├── TriageChatScreen.tsx
│   │   │   ├── PatientProfileScreen.tsx
│   │   │   ├── PricingScreen.tsx
│   │   │   └── DashboardScreen.tsx
│   │   ├── screens/            # Screen components
│   │   │   ├── HomeScreen.tsx
│   │   │   ├── TriageScreen.tsx
│   │   │   └── BillingScreen.tsx
│   │   ├── navigation/         # Navigation setup
│   │   │   ├── AppNavigator.tsx
│   │   │   └── TabNavigator.tsx
│   │   ├── services/           # API service layer
│   │   │   ├── api.ts          # HTTP client for SAME backend
│   │   │   ├── auth.ts
│   │   │   └── types.ts
│   │   ├── hooks/              # Custom React Native hooks
│   │   │   ├── useAuth.ts
│   │   │   └── useTriage.ts
│   │   ├── utils/              # Utility functions
│   │   │   ├── helpers.ts
│   │   │   └── constants.ts
│   │   ├── types/              # TypeScript types
│   │   │   ├── api.ts
│   │   │   ├── user.ts
│   │   │   └── triage.ts
│   │   ├── styles/             # Styling
│   │   │   ├── colors.ts
│   │   │   └── typography.ts
│   │   ├── App.tsx
│   │   └── index.js
│   ├── package.json
│   ├── tsconfig.json
│   ├── metro.config.js
│   ├── react-native.config.js
│   └── README.md
│
├── messaging-backend/           # WhatsApp/SMS backend (separate)
│   ├── app/
│   │   ├── main.py
│   │   ├── services/
│   │   │   ├── whatsapp_service.py
│   │   │   ├── sms_service.py
│   │   │   └── pricing_flow.py
│   │   └── handlers/
│   │       ├── message_handler.py
│   │       └── triage_handler.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── docs/                       # Shared documentation
│   ├── api/                    # OpenAPI/Swagger specs
│   │   ├── openapi.yaml
│   │   └── README.md
│   ├── architecture.md
│   ├── deployment.md
│   └── user-guides/
│       ├── web-app-guide.md
│       └── mobile-app-guide.md
│
├── scripts/                    # Shared scripts
│   ├── setup.sh
│   ├── deploy-backend.sh
│   ├── deploy-web.sh
│   └── deploy-mobile.sh
│
├── docker-compose.yml
├── .gitignore
├── README.md
└── LICENSE
```

---

## 🔗 API Usage Pattern

### Backend API Endpoints (Shared)
```
Base URL: https://api.dedan.health/v1/

Authentication: Bearer JWT token

Endpoints:
POST /auth/login
POST /auth/logout
GET  /auth/me

POST /triage/assess
GET  /triage/history
POST /triage/feedback

GET  /users/profile
PUT  /users/profile

GET  /billing/plans
POST /billing/subscribe
GET  /billing/subscription
POST /billing/payment-method

GET  /analytics/usage
GET  /analytics/reports
```

### Web App API Usage (/web/src/services/api.ts)
```typescript
import axios from 'axios';

const API_BASE_URL = 'https://api.dedan.health/v1';

class DEDANAPIService {
  private client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  constructor() {
    // Add request interceptor for auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('dedan_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('dedan_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async triage(symptoms: string, demographics: any) {
    const response = await this.client.post('/triage/assess', {
      symptoms,
      demographics,
    });
    return response.data;
  }

  async getUserProfile() {
    const response = await this.client.get('/users/profile');
    return response.data;
  }

  async updateUserProfile(profile: any) {
    const response = await this.client.put('/users/profile', profile);
    return response.data;
  }

  async getBillingPlans() {
    const response = await this.client.get('/billing/plans');
    return response.data;
  }

  async subscribeToPlan(planId: string, paymentMethod: any) {
    const response = await this.client.post('/billing/subscribe', {
      plan_id: planId,
      payment_method: paymentMethod,
    });
    return response.data;
  }
}

export const dedanAPI = new DEDANAPIService();
```

### Mobile App API Usage (/mobile/src/services/api.ts)
```typescript
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://api.dedan.health/v1';

class DEDANAPIService {
  private client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000, // Longer timeout for mobile
    headers: {
      'Content-Type': 'application/json',
    },
  });

  constructor() {
    // Add request interceptor for auth token
    this.client.interceptors.request.use(async (config) => {
      const token = await AsyncStorage.getItem('dedan_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          await AsyncStorage.removeItem('dedan_token');
          // Navigate to login screen
        }
        return Promise.reject(error);
      }
    );
  }

  async triage(symptoms: string, demographics: any) {
    const response = await this.client.post('/triage/assess', {
      symptoms,
      demographics,
    });
    return response.data;
  }

  async getUserProfile() {
    const response = await this.client.get('/users/profile');
    return response.data;
  }

  async updateUserProfile(profile: any) {
    const response = await this.client.put('/users/profile', profile);
    return response.data;
  }

  async getBillingPlans() {
    const response = await this.client.get('/billing/plans');
    return response.data;
  }

  async subscribeToPlan(planId: string, paymentMethod: any) {
    const response = await this.client.post('/billing/subscribe', {
      plan_id: planId,
      payment_method: paymentMethod,
    });
    return response.data;
  }

  // Mobile-specific methods
  async uploadImage(imageUri: string) {
    const formData = new FormData();
    formData.append('image', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'upload.jpg',
    } as any);

    const response = await this.client.post('/triage/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getLocationBasedClinics(latitude: number, longitude: number) {
    const response = await this.client.get('/clinics/nearby', {
      params: { lat: latitude, lng: longitude },
    });
    return response.data;
  }
}

export const dedanAPI = new DEDANAPIService();
```

---

## 📦 Package.json Layouts

### Web App Package.json (/web/package.json)
```json
{
  "name": "dedan-health-web",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "axios": "^1.3.4",
    "@mui/material": "^5.11.0",
    "@mui/icons-material": "^5.11.0",
    "@emotion/react": "^11.10.5",
    "@emotion/styled": "^11.10.5",
    "workbox-window": "^6.5.3"
  },
  "devDependencies": {
    "@types/react": "^18.0.27",
    "@types/react-dom": "^18.0.10",
    "@typescript-eslint/eslint-plugin": "^5.52.0",
    "@typescript-eslint/parser": "^5.52.0",
    "@vitejs/plugin-react": "^3.1.0",
    "eslint": "^8.34.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.3.4",
    "typescript": "^4.9.4",
    "vite": "^4.1.1",
    "vite-plugin-pwa": "^0.14.4",
    "vitest": "^0.28.5"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
```

### Mobile App Package.json (/mobile/package.json)
```json
{
  "name": "dedan-health-mobile",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "android": "react-native run-android",
    "ios": "react-native run-ios",
    "start": "react-native start",
    "test": "jest",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "type-check": "tsc --noEmit",
    "build:android": "cd android && ./gradlew assembleRelease",
    "build:ios": "cd ios && xcodebuild -workspace DedanHealth.xcworkspace -scheme DedanHealth -configuration Release -destination generic/platform=iOS"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-native": "^0.71.2",
    "react-navigation": "^4.4.4",
    "@react-navigation/native": "^6.1.6",
    "@react-navigation/stack": "^6.3.16",
    "@react-navigation/bottom-tabs": "^6.5.7",
    "axios": "^1.3.4",
    "@react-native-async-storage/async-storage": "^1.17.11",
    "@react-native-community/netinfo": "^9.3.7",
    "react-native-image-picker": "^5.3.0",
    "react-native-permissions": "^3.7.3",
    "react-native-geolocation-service": "^5.3.0",
    "react-native-vector-icons": "^9.2.0",
    "react-native-safe-area-context": "^4.5.0",
    "react-native-screens": "^3.20.0"
  },
  "devDependencies": {
    "@babel/core": "^7.20.0",
    "@babel/preset-env": "^7.20.0",
    "@babel/runtime": "^7.20.0",
    "@react-native/eslint-config": "^0.71.1",
    "@react-native/metro-config": "^0.71.1",
    "@tsconfig/react-native": "^0.71.1",
    "@types/react": "^18.0.27",
    "@types/react-test-renderer": "^18.0.0",
    "babel-jest": "^29.3.1",
    "eslint": "^8.19.0",
    "jest": "^29.3.1",
    "metro-react-native-babel-preset": "^0.71.1",
    "prettier": "^2.8.4",
    "react-test-renderer": "^18.2.0",
    "typescript": "^4.9.4"
  },
  "jest": {
    "preset": "react-native"
  }
}
```

---

## 🚀 Development Independence

### Web App Development Workflow
```bash
# Web team can work completely independently
cd /web
npm install
npm start                    # Starts development server on localhost:3000
npm run build                # Builds for production
npm run test                  # Runs tests
```

### Mobile App Development Workflow
```bash
# Mobile team can work completely independently
cd /mobile
npm install
npm start                    # Starts Metro bundler
npm run android              # Runs on Android emulator/device
npm run ios                  # Runs on iOS simulator/device
npm run test                  # Runs Jest tests
```

### Backend Development Workflow
```bash
# Backend team maintains shared API
cd /backend
pip install -r requirements.txt
uvicorn app.main:app --reload  # Starts FastAPI server
pytest                       # Runs tests
```

---

## 🔄 Shared API Contract

### OpenAPI Specification (/docs/api/openapi.yaml)
Both web and mobile teams reference the same OpenAPI spec:

```yaml
openapi: 3.0.0
info:
  title: DEDAN Health API
  version: 1.0.0
  description: Shared API for web and mobile applications

servers:
  - url: https://api.dedan.health/v1
    description: Production server
  - url: http://localhost:8000/v1
    description: Development server

paths:
  /auth/login:
    post:
      summary: Authenticate user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                password:
                  type: string
      responses:
        200:
          description: Authentication successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  token:
                  type: string
                  user:
                    $ref: '#/components/schemas/User'

  /triage/assess:
    post:
      summary: Assess symptoms with AI triage
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                symptoms:
                  type: string
                demographics:
                  type: object
      responses:
        200:
          description: Triage assessment completed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TriageResult'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        email:
          type: string
        name:
          type: string
        role:
          type: string
    
    TriageResult:
      type: object
      properties:
        triage_level:
          type: string
          enum: [emergency, urgent, routine, self_care]
        confidence:
          type: number
        recommendations:
          type: array
          items:
            type: string

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

## 📋 Development Guidelines

### Rule #1: No Cross-Dependencies
- `/web` cannot import anything from `/mobile`
- `/mobile` cannot import anything from `/web`
- Both can only communicate with `/backend` via HTTP API

### Rule #2: Shared Types via API
- TypeScript types are duplicated in both projects
- API contracts are defined in OpenAPI spec
- Both teams must follow the same API contract

### Rule #3: Independent Deployment
- Web app can be deployed independently (Vercel, Netlify, etc.)
- Mobile app can be built and distributed independently
- Backend can be updated without breaking either frontend

### Rule #4: Version Compatibility
- Backend API versioning must be maintained
- Breaking changes require coordinated updates
- Both frontends should be backward compatible

---

## 🎯 Benefits of This Architecture

1. **Team Independence**: Web and mobile teams can work independently
2. **Technology Flexibility**: Each platform can use optimal technologies
3. **Scalability**: Each service can scale independently
4. **Maintenance**: Issues in one platform don't affect others
5. **Testing**: Each platform can have its own testing strategy
6. **Deployment**: Independent deployment pipelines and schedules

---

## 🔄 Communication Protocol

### API Versioning Strategy
- Use semantic versioning (v1.0.0, v1.1.0, v2.0.0)
- Maintain backward compatibility within major versions
- Communicate breaking changes through shared documentation

### Change Management
- Backend changes must be documented in OpenAPI spec
- Frontend teams must review API changes
- Use feature flags for gradual rollouts

### Testing Strategy
- Backend: Unit tests + integration tests + API tests
- Web: Unit tests + E2E tests + visual regression
- Mobile: Unit tests + integration tests + device testing
