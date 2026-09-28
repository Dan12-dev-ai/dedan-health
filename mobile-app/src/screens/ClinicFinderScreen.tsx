import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  Linking,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import Geolocation from 'react-native-geolocation-service';
import { Clinic } from '../types';
import { apiService } from '../services/api';

const ClinicFinderScreen: React.FC = () => {
  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);

  useEffect(() => {
    requestLocationPermission();
  }, []);

  const requestLocationPermission = async () => {
    setLoading(true);
    Geolocation.getCurrentPosition(
      (position) => {
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        setUserLocation(location);
        loadNearbyClinics(location.lat, location.lng);
      },
      (error) => {
        console.error('Location error:', error);
        Alert.alert('Location Error', 'Could not get your location. Showing all clinics.');
        loadMockClinics();
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 }
    );
  };

  const loadNearbyClinics = async (lat: number, lng: number) => {
    try {
      const nearbyClinics = await apiService.findNearbyClinics(lat, lng);
      setClinics(nearbyClinics);
    } catch (error) {
      console.error('Clinic finder error:', error);
      loadMockClinics();
    } finally {
      setLoading(false);
    }
  };

  const loadMockClinics = () => {
    const mockClinics: Clinic[] = [
      {
        id: '1',
        name: 'City General Hospital',
        address: '123 Main St, City Center',
        phone: '+1-555-0123',
        coordinates: { lat: -1.2921, lng: 36.8219 },
        services: ['Emergency', 'General Medicine', 'Pediatrics'],
        hours: '24/7 Emergency, 8AM-8PM General',
        emergency_services: true,
        distance: 1.2
      },
      {
        id: '2',
        name: 'Community Health Center',
        address: '456 Oak Ave, District 5',
        phone: '+1-555-0456',
        coordinates: { lat: -1.3021, lng: 36.8319 },
        services: ['Primary Care', 'Maternity', 'Vaccination'],
        hours: '8AM-6PM Mon-Fri, 9AM-2PM Sat',
        emergency_services: false,
        distance: 2.5
      }
    ];
    setClinics(mockClinics);
    setLoading(false);
  };

  const filteredClinics = clinics.filter(clinic =>
    clinic.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    clinic.address.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCallClinic = (phone: string) => {
    Linking.openURL(`tel:${phone}`);
  };

  const handleGetDirections = (clinic: Clinic) => {
    const url = `https://maps.google.com/maps?q=${clinic.coordinates.lat},${clinic.coordinates.lng}`;
    Linking.openURL(url);
  };

  const renderClinicCard = (clinic: Clinic) => (
    <View key={clinic.id} style={styles.clinicCard}>
      <View style={styles.clinicHeader}>
        <View style={styles.clinicInfo}>
          <Text style={styles.clinicName}>{clinic.name}</Text>
          <Text style={styles.clinicAddress}>{clinic.address}</Text>
          {clinic.distance && (
            <Text style={styles.clinicDistance}>{clinic.distance} km away</Text>
          )}
        </View>
        {clinic.emergency_services && (
          <View style={styles.emergencyBadge}>
            <Text style={styles.emergencyBadgeText}>24/7</Text>
          </View>
        )}
      </View>

      <View style={styles.clinicServices}>
        {clinic.services.map((service, index) => (
          <View key={index} style={styles.serviceChip}>
            <Text style={styles.serviceText}>{service}</Text>
          </View>
        ))}
      </View>

      <Text style={styles.clinicHours}>{clinic.hours}</Text>

      <View style={styles.clinicActions}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleCallClinic(clinic.phone)}
        >
          <Icon name="phone" size={20} color="#1976d2" />
          <Text style={styles.actionButtonText}>Call</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleGetDirections(clinic)}
        >
          <Icon name="directions" size={20} color="#1976d2" />
          <Text style={styles.actionButtonText}>Directions</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Find Nearby Clinics</Text>
        <Text style={styles.subtitle}>Locate healthcare facilities in your area</Text>
      </View>

      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholder="Search clinics..."
        />
        <TouchableOpacity
          style={styles.searchButton}
          onPress={() => userLocation && loadNearbyClinics(userLocation.lat, userLocation.lng)}
        >
          <Icon name="search" size={24} color="#ffffff" />
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1976d2" />
          <Text style={styles.loadingText}>Finding nearby clinics...</Text>
        </View>
      ) : (
        <ScrollView style={styles.clinicsList} showsVerticalScrollIndicator={false}>
          {filteredClinics.length > 0 ? (
            filteredClinics.map(renderClinicCard)
          ) : (
            <View style={styles.noResults}>
              <Icon name="local-hospital" size={48} color="#cccccc" />
              <Text style={styles.noResultsText}>
                {searchQuery ? 'No clinics found matching your search' : 'No clinics available'}
              </Text>
            </View>
          )}
        </ScrollView>
      )}
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
  searchContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  searchInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    paddingHorizontal: 15,
    paddingVertical: 10,
    marginRight: 10,
    fontSize: 16,
  },
  searchButton: {
    width: 48,
    height: 48,
    borderRadius: 8,
    backgroundColor: '#1976d2',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#666666',
    marginTop: 10,
  },
  clinicsList: {
    flex: 1,
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  clinicCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  clinicHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  clinicInfo: {
    flex: 1,
  },
  clinicName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 5,
  },
  clinicAddress: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 3,
  },
  clinicDistance: {
    fontSize: 14,
    color: '#1976d2',
    fontWeight: '500',
  },
  emergencyBadge: {
    backgroundColor: '#d32f2f',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  emergencyBadgeText: {
    fontSize: 12,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  clinicServices: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 10,
  },
  serviceChip: {
    backgroundColor: '#e3f2fd',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
    marginBottom: 5,
  },
  serviceText: {
    fontSize: 12,
    color: '#1976d2',
  },
  clinicHours: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 15,
  },
  clinicActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  actionButtonText: {
    fontSize: 14,
    color: '#1976d2',
    marginLeft: 5,
    fontWeight: '500',
  },
  noResults: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 50,
  },
  noResultsText: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
    marginTop: 15,
  },
});

export default ClinicFinderScreen;
