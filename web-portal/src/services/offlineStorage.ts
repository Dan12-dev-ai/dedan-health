import { OfflineContent, ChatMessage, Session } from '../types';

const DB_NAME = 'DEDAN_Health_DB';
const DB_VERSION = 1;
const STORE_NAME = 'offline_content';
const SESSION_STORE = 'sessions';

class OfflineStorage {
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        
        // Create offline content store
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const contentStore = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
          contentStore.createIndex('type', 'type', { unique: false });
          contentStore.createIndex('language', 'language', { unique: false });
        }

        // Create sessions store
        if (!db.objectStoreNames.contains(SESSION_STORE)) {
          const sessionStore = db.createObjectStore(SESSION_STORE, { keyPath: 'session_id' });
          sessionStore.createIndex('created_at', 'created_at', { unique: false });
        }
      };
    });
  }

  async saveOfflineContent(content: OfflineContent): Promise<void> {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.put({ ...content, id: `${content.type}_${content.language}` });
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getOfflineContent(type: string, language: string): Promise<OfflineContent | null> {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(`${type}_${language}`);
      
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
    });
  }

  async saveSession(session: Session): Promise<void> {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([SESSION_STORE], 'readwrite');
      const store = transaction.objectStore(SESSION_STORE);
      const request = store.put(session);
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getSession(sessionId: string): Promise<Session | null> {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([SESSION_STORE], 'readonly');
      const store = transaction.objectStore(SESSION_STORE);
      const request = store.get(sessionId);
      
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
    });
  }

  async getAllSessions(): Promise<Session[]> {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([SESSION_STORE], 'readonly');
      const store = transaction.objectStore(SESSION_STORE);
      const request = store.getAll();
      
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  }

  async clearOldData(): Promise<void> {
    if (!this.db) await this.init();
    
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([SESSION_STORE], 'readwrite');
      const store = transaction.objectStore(SESSION_STORE);
      const request = store.openCursor();
      
      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        if (cursor) {
          const session = cursor.value as Session;
          if (new Date(session.updated_at) < thirtyDaysAgo) {
            cursor.delete();
          }
          cursor.continue();
        } else {
          resolve();
        }
      };
      
      request.onerror = () => reject(request.error);
    });
  }

  // Initialize with default offline content
  async initializeDefaultContent(): Promise<void> {
    const defaultContent: OfflineContent[] = [
      {
        type: 'faq',
        title: 'What is DEDAN Health?',
        content: 'DEDAN Health is an AI-powered medical triage service that helps you understand your symptoms and get appropriate medical care recommendations.',
        language: 'en'
      },
      {
        type: 'emergency_guide',
        title: 'Emergency Symptoms',
        content: 'Seek immediate medical attention for: Chest pain, difficulty breathing, severe bleeding, unconsciousness, severe allergic reactions, or pregnancy complications.',
        language: 'en'
      },
      {
        type: 'educational',
        title: 'Understanding Fever',
        content: 'Fever is your body\'s response to infection. Mild fever (<38.5°C) can be managed at home. Seek care for high fever (>39°C) or fever lasting more than 3 days.',
        language: 'en'
      }
    ];

    for (const content of defaultContent) {
      await this.saveOfflineContent(content);
    }
  }
}

export const offlineStorage = new OfflineStorage();
