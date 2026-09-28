/**
 * DEDAN-Health — Session State
 *
 * Holds the patient profile + current chat session in memory, persisted to
 * offlineStorage (IndexedDB) so the triage transcript survives reloads and
 * works offline. `created_at` is a stable Date captured once per session.
 */

import React, {
  createContext, useContext, useEffect, useMemo, useRef, useState,
  ReactNode, useCallback,
} from 'react';
import {
  PatientProfile, ChatMessage, TriageRequest, TriageResponse, Language, Session,
} from '../types';
import { offlineStorage } from '../services/offlineStorage';

interface DedanState {
  profile: PatientProfile | null;
  sessionId: string;
  messages: ChatMessage[];
  language: Language;
  setProfile: (profile: PatientProfile) => void;
  setLanguage: (lang: Language) => void;
  addMessage: (msg: ChatMessage) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  pushTriageResult: (response: TriageResponse) => void;
  resetSession: () => void;
  saveRequest: (request: TriageRequest) => Promise<void>;
}

const DedanStateContext = createContext<DedanState | undefined>(undefined);

function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

export const DedanStateProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const createdAtRef = useRef<Date>(new Date());
  const [profile, setProfileState] = useState<PatientProfile | null>(() => {
    try {
      const raw = localStorage.getItem('dedan:profile');
      return raw ? (JSON.parse(raw) as PatientProfile) : null;
    } catch { return null; }
  });
  const [language, setLanguageState] = useState<Language>('en');
  const [sessionId] = useState<string>(generateSessionId());
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  useEffect(() => {
    offlineStorage.init().catch(() => {});
    offlineStorage.getAllSessions().then((sessions) => {
      const current = (sessions as Session[]).find((s) => s.session_id === sessionId);
      if (current?.messages) setMessages(current.messages as ChatMessage[]);
      createdAtRef.current = current?.created_at instanceof Date ? current.created_at : new Date();
    }).catch(() => {});
  }, [sessionId]);

  const persist = useCallback(
    (msgs: ChatMessage[], prof: PatientProfile | null) => {
      void offlineStorage.saveSession({
        session_id: sessionId,
        patient_profile: prof ?? ({} as PatientProfile),
        messages: msgs,
        created_at: createdAtRef.current,
        updated_at: new Date(),
      });
    },
    [sessionId]
  );

  useEffect(() => { persist(messages, profile); }, [messages, profile, persist]);

  const persistProfile = useCallback((p: PatientProfile) => setProfileState(p), []);
  const persistLanguage = useCallback((lang: Language) => setLanguageState(lang), []);

  const addMessage = useCallback((msg: ChatMessage) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  const pushTriageResult = useCallback(
    (response: TriageResponse) => {
      addMessage({
        id: `ai_${Date.now()}`, type: 'assistant', content: response.patient_summary,
        timestamp: new Date(), triage_data: response,
      });
    },
    [addMessage]
  );

  const resetSession = useCallback(() => {
    setMessages([]);
    setProfileState(null);
    localStorage.removeItem('dedan:profile');
  }, [sessionId]);

    const saveRequest = useCallback(
    async (request: TriageRequest) => {
      // Explicit checkpoint: re-persist messages + patient. (The effect
      // above already persists on change; this guarantees an on-demand save.)
      await persist(messages, request.patient);
    },
    [messages, persist]
  );

  const value = useMemo<DedanState>(() => ({
    profile, sessionId, messages, language,
    setProfile: persistProfile, setLanguage: persistLanguage,
    addMessage, setMessages, pushTriageResult, resetSession, saveRequest,
  }), [profile, sessionId, messages, language, persistProfile, persistLanguage, addMessage, pushTriageResult, resetSession, saveRequest]);

  return <DedanStateContext.Provider value={value}>{children}</DedanStateContext.Provider>;
};

export const useDedanState = (): DedanState => {
  const ctx = useContext(DedanStateContext);
  if (!ctx) throw new Error('useDedanState must be used within DedanStateProvider');
  return ctx;
};
