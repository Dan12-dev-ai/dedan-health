import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Switch,
  ScrollView,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { AppSettings } from '../types';

const SettingsScreen: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings>({
    language: 'en',
    notifications_enabled: true,
    voice_input_enabled: true,
    low_data_mode: false,
    emergency_contacts: ['911', 'Local Hospital: +1-555-0123'],
  });

  const languages = [
    { value: 'en', label: 'English' },
    { value: 'sw', label: 'Swahili' },
    { value: 'am', label: 'Amharic' },
    { value: 'es', label: 'Spanish' },
    { value: 'fr', label: 'French' },
  ];

  const updateSetting = <K extends keyof AppSettings>(
    key: K,
    value: AppSettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleAddEmergencyContact = () => {
    Alert.prompt(
      'Add Emergency Contact',
      'Enter emergency contact number:',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Add',
          onPress: (contact) => {
            if (contact) {
              updateSetting('emergency_contacts', [...settings.emergency_contacts, contact]);
            }
          },
        },
      ],
      'plain-text'
    );
  };

  const handleDeleteEmergencyContact = (index: number) => {
    Alert.alert(
      'Delete Contact',
      'Are you sure you want to delete this emergency contact?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            const newContacts = settings.emergency_contacts.filter((_, i) => i !== index);
            updateSetting('emergency_contacts', newContacts);
          },
        },
      ]
    );
  };

  const renderSettingItem = (
    icon: string,
    title: string,
    subtitle: string,
    value: boolean,
    onToggle: () => void
  ) => (
    <View style={styles.settingItem}>
      <View style={styles.settingInfo}>
        <Icon name={icon} size={24} color="#1976d2" />
        <View style={styles.settingText}>
          <Text style={styles.settingTitle}>{title}</Text>
          <Text style={styles.settingSubtitle}>{subtitle}</Text>
        </View>
      </View>
      <Switch
        value={value}
        onValueChange={onToggle}
        trackColor={{ false: '#e0e0e0', true: '#bbdefb' }}
        thumbColor={value ? '#1976d2' : '#ffffff'}
      />
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Settings</Text>
        <Text style={styles.subtitle}>Customize your DEDAN experience</Text>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Language Setting */}
        <View style={styles.settingItem}>
          <View style={styles.settingInfo}>
            <Icon name="language" size={24} color="#1976d2" />
            <View style={styles.settingText}>
              <Text style={styles.settingTitle}>Language</Text>
              <Text style={styles.settingSubtitle}>
                {languages.find(l => l.value === settings.language)?.label}
              </Text>
            </View>
          </View>
          <Icon name="chevron-right" size={24} color="#cccccc" />
        </View>

        {/* Notification Setting */}
        {renderSettingItem(
          'notifications',
          'Push Notifications',
          'Receive follow-up reminders and alerts',
          settings.notifications_enabled,
          () => updateSetting('notifications_enabled', !settings.notifications_enabled)
        )}

        {/* Voice Input Setting */}
        {renderSettingItem(
          'mic',
          'Voice Input',
          'Use voice to describe symptoms',
          settings.voice_input_enabled,
          () => updateSetting('voice_input_enabled', !settings.voice_input_enabled)
        )}

        {/* Low Data Mode Setting */}
        {renderSettingItem(
          'data-saver',
          'Low Data Mode',
          'Reduce data usage for slow connections',
          settings.low_data_mode,
          () => updateSetting('low_data_mode', !settings.low_data_mode)
        )}

        {/* Emergency Contacts */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Emergency Contacts</Text>
          {settings.emergency_contacts.map((contact, index) => (
            <View key={index} style={styles.contactItem}>
              <View style={styles.contactInfo}>
                <Icon name="phone" size={20} color="#d32f2f" />
                <Text style={styles.contactText}>{contact}</Text>
              </View>
              <TouchableOpacity
                onPress={() => handleDeleteEmergencyContact(index)}
              >
                <Icon name="delete" size={20} color="#d32f2f" />
              </TouchableOpacity>
            </View>
          ))}
          
          <TouchableOpacity
            style={styles.addContactButton}
            onPress={handleAddEmergencyContact}
          >
            <Icon name="add" size={20} color="#1976d2" />
            <Text style={styles.addContactText}>Add Emergency Contact</Text>
          </TouchableOpacity>
        </View>

        {/* About Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          
          <TouchableOpacity style={styles.aboutItem}>
            <Icon name="info" size={24} color="#1976d2" />
            <Text style={styles.aboutText}>Version 1.0.0</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.aboutItem}>
            <Icon name="privacy-tip" size={24} color="#1976d2" />
            <Text style={styles.aboutText}>Privacy Policy</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.aboutItem}>
            <Icon name="help" size={24} color="#1976d2" />
            <Text style={styles.aboutText}>Help & Support</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#1976d2',
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  subtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginTop: 5,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#ffffff',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderRadius: 8,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  settingInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingText: {
    marginLeft: 15,
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333333',
    marginBottom: 2,
  },
  settingSubtitle: {
    fontSize: 14,
    color: '#666666',
  },
  section: {
    marginTop: 25,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 15,
  },
  contactItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#ffffff',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderRadius: 8,
    marginBottom: 10,
  },
  contactInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  contactText: {
    fontSize: 16,
    color: '#333333',
    marginLeft: 10,
  },
  addContactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#e3f2fd',
    paddingVertical: 15,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#1976d2',
    borderStyle: 'dashed',
  },
  addContactText: {
    fontSize: 16,
    color: '#1976d2',
    marginLeft: 10,
    fontWeight: '500',
  },
  aboutItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderRadius: 8,
    marginBottom: 10,
  },
  aboutText: {
    fontSize: 16,
    color: '#333333',
    marginLeft: 15,
  },
});

export default SettingsScreen;
