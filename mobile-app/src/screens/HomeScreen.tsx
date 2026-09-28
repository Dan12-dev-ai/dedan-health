import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  StatusBar,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import { apiService } from '../services/api';

type HomeScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Home'>;

interface Props {
  navigation: HomeScreenNavigationProp;
}

const HomeScreen: React.FC<Props> = ({ navigation }) => {
  const [isOnline, setIsOnline] = useState(true);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  useEffect(() => {
    checkAPIHealth();
  }, []);

  const checkAPIHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const isHealthy = await apiService.healthCheck();
      setIsOnline(isHealthy);
    } catch (error) {
      setIsOnline(false);
    } finally {
      setIsCheckingHealth(false);
    }
  };

  const handleStartTriage = () => {
    navigation.navigate('PatientProfile');
  };

  const handleClinicFinder = () => {
    navigation.navigate('ClinicFinder');
  };

  const handleEmergency = () => {
    Alert.alert(
      'Emergency Services',
      'Call emergency services immediately or go to the nearest hospital.\n\nEmergency: 911\nLocal Hospital: [Add local number]',
      [
        { text: 'Call Emergency', style: 'destructive' },
        { text: 'Find Nearest Hospital', onPress: () => navigation.navigate('ClinicFinder') },
        { text: 'Cancel', style: 'cancel' }
      ]
    );
  };

  const handleOfflineMode = () => {
    Alert.alert(
      'Offline Mode',
      'You are currently offline. Limited functionality is available.\n\nFeatures available:\n• Basic symptom assessment\n• Emergency guides\n• Clinic information (cached)',
      [{ text: 'OK' }]
    );
  };

  const features = [
    {
      id: 'triage',
      title: 'AI Triage',
      description: 'Get AI-powered symptom assessment',
      icon: 'medical-services',
      color: '#1976d2',
      onPress: handleStartTriage,
    },
    {
      id: 'clinics',
      title: 'Find Clinics',
      description: 'Locate nearby healthcare facilities',
      icon: 'local-hospital',
      color: '#388e3c',
      onPress: handleClinicFinder,
    },
    {
      id: 'emergency',
      title: 'Emergency',
      description: 'Get emergency help immediately',
      icon: 'emergency',
      color: '#d32f2f',
      onPress: handleEmergency,
    },
    {
      id: 'followup',
      title: 'Follow-up Care',
      description: 'Track your health progress',
      icon: 'follow-the-signs',
      color: '#f57c00',
      onPress: () => navigation.navigate('FollowUp'),
    },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1976d2" />
      
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <View style={styles.logoContainer}>
            <Icon name="local-hospital" size={40} color="#ffffff" />
          </View>
          <View style={styles.headerText}>
            <Text style={styles.title}>DEDAN Health</Text>
            <Text style={styles.subtitle}>Digital Empathy-Driven AI Navigator</Text>
          </View>
        </View>
        
        {/* Connection Status */}
        <View style={styles.statusContainer}>
          {isCheckingHealth ? (
            <Text style={styles.checkingStatus}>Checking connection...</Text>
          ) : (
            <View style={styles.connectionStatus}>
              <Icon 
                name={isOnline ? 'wifi' : 'wifi-off'} 
                size={16} 
                color={isOnline ? '#4caf50' : '#ff9800'} 
              />
              <Text style={[styles.statusText, { color: isOnline ? '#4caf50' : '#ff9800' }]}>
                {isOnline ? 'Online' : 'Offline'}
              </Text>
            </View>
          )}
        </View>
      </View>

      {/* Main Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Welcome Section */}
        <View style={styles.welcomeSection}>
          <Text style={styles.welcomeTitle}>Welcome to DEDAN Health</Text>
          <Text style={styles.welcomeDescription}>
            AI-powered primary-care triage for underserved regions
          </Text>
        </View>

        {/* Features Grid */}
        <View style={styles.featuresGrid}>
          {features.map((feature) => (
            <TouchableOpacity
              key={feature.id}
              style={[styles.featureCard, { backgroundColor: feature.color }]}
              onPress={feature.onPress}
              activeOpacity={0.8}
            >
              <View style={styles.featureIcon}>
                <Icon name={feature.icon} size={32} color="#ffffff" />
              </View>
              <Text style={styles.featureTitle}>{feature.title}</Text>
              <Text style={styles.featureDescription}>{feature.description}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Offline Notice */}
        {!isOnline && (
          <View style={styles.offlineNotice}>
            <Icon name="warning" size={24} color="#ff9800" />
            <Text style={styles.offlineNoticeText}>
              You are offline. Some features may be limited.
            </Text>
            <TouchableOpacity onPress={handleOfflineMode}>
              <Text style={styles.learnMoreText}>Learn more</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Quick Tips */}
        <View style={styles.tipsSection}>
          <Text style={styles.tipsTitle}>Quick Tips</Text>
          <View style={styles.tipItem}>
            <Icon name="check-circle" size={20} color="#4caf50" />
            <Text style={styles.tipText}>Voice input available for hands-free use</Text>
          </View>
          <View style={styles.tipItem}>
            <Icon name="check-circle" size={20} color="#4caf50" />
            <Text style={styles.tipText}>Works on low-bandwidth connections</Text>
          </View>
          <View style={styles.tipItem}>
            <Icon name="check-circle" size={20} color="#4caf50" />
            <Text style={styles.tipText}>Supports multiple local languages</Text>
          </View>
        </View>
      </ScrollView>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          © 2025 DEDAN Health - Not a replacement for professional medical care
        </Text>
      </View>
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
    paddingTop: 10,
    paddingBottom: 20,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  logoContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  subtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  statusContainer: {
    alignItems: 'flex-end',
  },
  checkingStatus: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    fontSize: 12,
    marginLeft: 5,
    fontWeight: '500',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  welcomeSection: {
    paddingVertical: 30,
    alignItems: 'center',
  },
  welcomeTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333333',
    textAlign: 'center',
    marginBottom: 10,
  },
  welcomeDescription: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
    lineHeight: 24,
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  featureCard: {
    width: '48%',
    backgroundColor: '#1976d2',
    borderRadius: 12,
    padding: 20,
    marginBottom: 15,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  featureIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 5,
  },
  featureDescription: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    lineHeight: 16,
  },
  offlineNotice: {
    backgroundColor: '#fff3e0',
    borderRadius: 8,
    padding: 15,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#ff9800',
  },
  offlineNoticeText: {
    flex: 1,
    fontSize: 14,
    color: '#e65100',
    marginLeft: 10,
  },
  learnMoreText: {
    fontSize: 14,
    color: '#1976d2',
    textDecorationLine: 'underline',
  },
  tipsSection: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  tipsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 15,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  tipText: {
    fontSize: 14,
    color: '#666666',
    marginLeft: 10,
    flex: 1,
  },
  footer: {
    backgroundColor: '#ffffff',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  footerText: {
    fontSize: 12,
    color: '#666666',
    textAlign: 'center',
  },
});

export default HomeScreen;
