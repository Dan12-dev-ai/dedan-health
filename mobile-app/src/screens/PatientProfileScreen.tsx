import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  Picker,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import { PatientProfile } from '../types';

type PatientProfileScreenNavigationProp = StackNavigationProp<RootStackParamList, 'PatientProfile'>;

interface Props {
  navigation: PatientProfileScreenNavigationProp;
}

const PatientProfileScreen: React.FC<Props> = ({ navigation }) => {
  const [profile, setProfile] = useState<Partial<PatientProfile>>({
    age: '',
    sex: '',
    location: '',
    pregnancy_status: false,
    chronic_conditions: [],
    language: 'en',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const chronicConditionsOptions = [
    'Diabetes',
    'Hypertension',
    'Asthma',
    'Heart Disease',
    'HIV/AIDS',
    'Tuberculosis',
    'Malaria',
    'None'
  ];

  const languages = [
    { value: 'en', label: 'English' },
    { value: 'sw', label: 'Swahili' },
    { value: 'am', label: 'Amharic' },
    { value: 'es', label: 'Spanish' },
    { value: 'fr', label: 'French' }
  ];

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!profile.age || profile.age < 0 || profile.age > 120) {
      newErrors.age = 'Please enter a valid age (0-120)';
    }

    if (!profile.sex) {
      newErrors.sex = 'Please select sex';
    }

    if (profile.pregnancy_status && profile.sex !== 'female') {
      newErrors.pregnancy_status = 'Pregnancy status only applicable for female patients';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      const cleanProfile: PatientProfile = {
        age: Number(profile.age),
        sex: profile.sex as 'male' | 'female' | 'other',
        location: profile.location,
        pregnancy_status: profile.pregnancy_status,
        chronic_conditions: profile.chronic_conditions?.filter(c => c !== 'None') || [],
        language: profile.language as 'en' | 'sw' | 'am' | 'es' | 'fr'
      };

      // Generate session ID
      const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      navigation.navigate('TriageChat', { profile: cleanProfile, sessionId });
    }
  };

  const handleChronicConditionToggle = (condition: string) => {
    const currentConditions = profile.chronic_conditions || [];
    
    if (condition === 'None') {
      setProfile({ ...profile, chronic_conditions: [] });
      return;
    }

    const updatedConditions = currentConditions.includes(condition)
      ? currentConditions.filter(c => c !== condition)
      : [...currentConditions, condition];

    setProfile({ ...profile, chronic_conditions: updatedConditions });
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Icon name="person" size={40} color="#1976d2" />
          <Text style={styles.title}>Patient Information</Text>
          <Text style={styles.subtitle}>
            Please provide basic information to help DEDAN assess your symptoms accurately
          </Text>
        </View>

        <View style={styles.form}>
          {/* Age */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Age *</Text>
            <TextInput
              style={[styles.input, errors.age && styles.inputError]}
              value={profile.age?.toString()}
              onChangeText={(text) => setProfile({ ...profile, age: text ? parseInt(text) : '' })}
              placeholder="Enter your age"
              keyboardType="numeric"
              maxLength={3}
            />
            {errors.age && <Text style={styles.errorText}>{errors.age}</Text>}
          </View>

          {/* Sex */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Sex *</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={profile.sex}
                onValueChange={(value) => setProfile({ ...profile, sex: value })}
                style={styles.picker}
              >
                <Picker.Item label="Select sex" value="" />
                <Picker.Item label="Male" value="male" />
                <Picker.Item label="Female" value="female" />
                <Picker.Item label="Other" value="other" />
              </Picker>
            </View>
            {errors.sex && <Text style={styles.errorText}>{errors.sex}</Text>}
          </View>

          {/* Location */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Location (City/Region)</Text>
            <TextInput
              style={styles.input}
              value={profile.location}
              onChangeText={(text) => setProfile({ ...profile, location: text })}
              placeholder="Enter your location"
            />
            <Text style={styles.helperText}>Helps us find nearby healthcare facilities</Text>
          </View>

          {/* Language */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Preferred Language *</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={profile.language}
                onValueChange={(value) => setProfile({ ...profile, language: value })}
                style={styles.picker}
              >
                {languages.map((lang) => (
                  <Picker.Item key={lang.value} label={lang.label} value={lang.value} />
                ))}
              </Picker>
            </View>
          </View>

          {/* Pregnancy Status */}
          {profile.sex === 'female' && (
            <View style={styles.inputGroup}>
              <View style={styles.checkboxContainer}>
                <TouchableOpacity
                  style={styles.checkbox}
                  onPress={() => setProfile({ ...profile, pregnancy_status: !profile.pregnancy_status })}
                >
                  <View style={[styles.checkboxInner, profile.pregnancy_status && styles.checkboxChecked]}>
                    {profile.pregnancy_status && <Icon name="check" size={16} color="#ffffff" />}
                  </View>
                </TouchableOpacity>
                <Text style={styles.checkboxLabel}>
                  Pregnant or recently pregnant (within 6 weeks)
                </Text>
              </View>
              {errors.pregnancy_status && <Text style={styles.errorText}>{errors.pregnancy_status}</Text>}
            </View>
          )}

          {/* Chronic Conditions */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Chronic Conditions (select all that apply)</Text>
            <View style={styles.conditionsContainer}>
              {chronicConditionsOptions.map((condition) => (
                <TouchableOpacity
                  key={condition}
                  style={[
                    styles.conditionChip,
                    profile.chronic_conditions?.includes(condition) && styles.conditionChipSelected
                  ]}
                  onPress={() => handleChronicConditionToggle(condition)}
                >
                  <Text style={[
                    styles.conditionChipText,
                    profile.chronic_conditions?.includes(condition) && styles.conditionChipTextSelected
                  ]}>
                    {condition}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Privacy Notice */}
          <View style={styles.privacyNotice}>
            <Icon name="info" size={20} color="#1976d2" />
            <Text style={styles.privacyText}>
              Your information is kept confidential and used only to provide accurate medical triage. 
              Data is anonymized for system improvement.
            </Text>
          </View>

          {/* Submit Button */}
          <TouchableOpacity style={styles.submitButton} onPress={handleSubmit}>
            <Text style={styles.submitButtonText}>Start Triage Assessment</Text>
            <Icon name="arrow-forward" size={20} color="#ffffff" />
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
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 30,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 15,
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
    lineHeight: 22,
  },
  form: {
    paddingBottom: 20,
  },
  inputGroup: {
    marginBottom: 25,
  },
  label: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333333',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    paddingHorizontal: 15,
    paddingVertical: 12,
    fontSize: 16,
    backgroundColor: '#ffffff',
  },
  inputError: {
    borderColor: '#d32f2f',
  },
  errorText: {
    fontSize: 14,
    color: '#d32f2f',
    marginTop: 5,
  },
  helperText: {
    fontSize: 14,
    color: '#666666',
    marginTop: 5,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    backgroundColor: '#ffffff',
  },
  picker: {
    height: 50,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkbox: {
    marginRight: 10,
  },
  checkboxInner: {
    width: 24,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#e0e0e0',
    backgroundColor: '#ffffff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#1976d2',
    borderColor: '#1976d2',
  },
  checkboxLabel: {
    fontSize: 16,
    color: '#333333',
    flex: 1,
  },
  conditionsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  conditionChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  conditionChipSelected: {
    backgroundColor: '#1976d2',
    borderColor: '#1976d2',
  },
  conditionChipText: {
    fontSize: 14,
    color: '#666666',
  },
  conditionChipTextSelected: {
    color: '#ffffff',
  },
  privacyNotice: {
    flexDirection: 'row',
    backgroundColor: '#e3f2fd',
    borderRadius: 8,
    padding: 15,
    marginBottom: 25,
    alignItems: 'flex-start',
  },
  privacyText: {
    fontSize: 14,
    color: '#1976d2',
    marginLeft: 10,
    flex: 1,
    lineHeight: 20,
  },
  submitButton: {
    flexDirection: 'row',
    backgroundColor: '#1976d2',
    borderRadius: 8,
    paddingVertical: 15,
    paddingHorizontal: 20,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginRight: 10,
  },
});

export default PatientProfileScreen;
