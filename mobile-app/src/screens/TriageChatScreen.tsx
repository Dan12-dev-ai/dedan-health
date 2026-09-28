import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Image,
  PermissionsAndroid,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { StackNavigationProp } from '@react-navigation/stack';
import Voice from 'react-native-voice';
import { RootStackParamList } from '../navigation/AppNavigator';
import { PatientProfile, ChatMessage, TriageResponse } from '../types';
import { apiService } from '../services/api';

type TriageChatScreenNavigationProp = StackNavigationProp<RootStackParamList, 'TriageChat'>;

interface Props {
  route: {
    params: {
      profile: PatientProfile;
      sessionId: string;
    };
  };
  navigation: TriageChatScreenNavigationProp;
}

const TriageChatScreen: React.FC<Props> = ({ route, navigation }) => {
  const { profile, sessionId } = route.params;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [selectedImage, setSelectedImage] = useState<{ uri: string; name: string } | null>(null);
  const [multimodalResponse, setMultimodalResponse] = useState<any>(null);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    Voice.onSpeechStart = onSpeechStart;
    Voice.onSpeechEnd = onSpeechEnd;
    Voice.onSpeechResults = onSpeechResults;
    Voice.onSpeechError = onSpeechError;

    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const onSpeechStart = () => {
    setIsRecording(true);
  };

  const onSpeechEnd = () => {
    setIsRecording(false);
  };

  const onSpeechResults = (e: any) => {
    if (e.value && e.value.length > 0) {
      setVoiceTranscript(e.value[0]);
    }
  };

  const onSpeechError = (e: any) => {
    console.error('Speech recognition error:', e);
    setIsRecording(false);
    Alert.alert('Voice Error', 'Could not recognize speech. Please try again.');
  };

  const startRecording = async () => {
    try {
      await Voice.start('en-US');
    } catch (error) {
      console.error('Voice start error:', error);
      Alert.alert('Voice Error', 'Could not start recording. Please check microphone permissions.');
    }
  };

  const stopRecording = async () => {
    try {
      await Voice.stop();
    } catch (error) {
      console.error('Voice stop error:', error);
    }
  };

  const clearVoice = () => {
    setVoiceTranscript('');
  };

  // Request camera permission (Android)
  const requestCameraPermission = async (): Promise<boolean> => {
    if (Platform.OS === 'android') {
      try {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.CAMERA,
          {
            title: 'Camera Permission',
            message: 'DEDAN Health needs camera access to take photos for your assessment.',
            buttonNeutral: 'Ask Me Later',
            buttonNegative: 'Cancel',
            buttonPositive: 'OK',
          }
        );
        return granted === PermissionsAndroid.RESULTS.GRANTED;
      } catch (err) {
        console.warn('Camera permission error:', err);
        return false;
      }
    }
    return true; // iOS handles permissions differently
  };

  // Request gallery permission (Android)
  const requestGalleryPermission = async (): Promise<boolean> => {
    if (Platform.OS === 'android') {
      try {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
          {
            title: 'Storage Permission',
            message: 'DEDAN Health needs storage access to select photos for your assessment.',
            buttonNeutral: 'Ask Me Later',
            buttonNegative: 'Cancel',
            buttonPositive: 'OK',
          }
        );
        return granted === PermissionsAndroid.RESULTS.GRANTED;
      } catch (err) {
        console.warn('Storage permission error:', err);
        return false;
      }
    }
    return true;
  };

  // Image picker - uses react-native-image-picker when available
  const pickImage = async (source: 'camera' | 'gallery') => {
    const hasPermission = source === 'camera' 
      ? await requestCameraPermission() 
      : await requestGalleryPermission();
    
    if (!hasPermission) {
      Alert.alert(
        'Permission Denied',
        'Camera/gallery permission is required to attach photos. Please enable it in Settings.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Open Settings', onPress: () => Linking.openSettings() },
        ]
      );
      return;
    }

    try {
      // Dynamic import of react-native-image-picker
      const { launchCamera, launchImageLibrary } = require('react-native-image-picker');
      
      const options = {
        mediaType: 'photo' as const,
        maxWidth: 1024,
        maxHeight: 1024,
        quality: 0.8,
        includeBase64: false,
      };

      const result = source === 'camera' 
        ? await launchCamera(options)
        : await launchImageLibrary(options);

      if (result.didCancel) return;
      if (result.errorCode) {
        Alert.alert('Image Error', result.errorMessage || 'Failed to pick image');
        return;
      }

      const asset = result.assets?.[0];
      if (asset?.uri) {
        setSelectedImage({ uri: asset.uri, name: asset.fileName || 'photo.jpg' });
      }
    } catch (error) {
      // react-native-image-picker not installed - show guidance
      Alert.alert(
        'Image Picker Not Available',
        'Please install react-native-image-picker to use photo features.',
        [{ text: 'OK' }]
      );
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  // Multimodal submit - sends text + voice transcript + image to backend
  const handleMultimodalSubmit = async () => {
    if ((!inputText.trim() && !voiceTranscript && !selectedImage) || isLoading) return;

    setIsLoading(true);
    setMultimodalResponse(null);

    try {
      // Build multimodal request
      const multimodalRequest: any = {
        text: inputText.trim() || undefined,
        voice_transcript: voiceTranscript || undefined,
        image_ids: [],
        image_data_list: [],
        patient: profile,
        session_id: sessionId,
        conversation_history: [],
        consent: true,
      };

      // If image is selected, upload it first
      if (selectedImage) {
        try {
          const { uploadImage } = require('../services/multimodalService');
          // For mobile, we'd need to convert the image to a File-like object
          // For now, skip image upload on mobile until fully integrated
          console.log('Image selected:', selectedImage.name);
        } catch (imgError) {
          console.error('Image upload error:', imgError);
        }
      }

      // Submit to multimodal analysis endpoint
      const result = await apiService.submitMultimodalAnalysis(multimodalRequest);
      
      if (result) {
        setMultimodalResponse(result);
        
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: result.recommended_next_step || result.patient_summary || 'Assessment complete.',
          timestamp: new Date(),
          triage_data: result,
        };

        setMessages(prev => [...prev, assistantMessage]);

        // Vibrate for emergency/urgent
        if (result.urgency === 'emergency' || result.urgency === 'urgent') {
          // Vibration.vibrate(1000);
        }
      } else {
        throw new Error('No response from analysis');
      }
    } catch (error) {
      console.error('Multimodal analysis error:', error);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'I apologize, but I encountered an error. Please check your connection and try again. If symptoms persist, please seek medical attention.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Legacy triage for text-only (fallback)
  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputText,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const triageRequest = {
        patient: profile,
        symptoms: {
          symptoms: inputText,
          voice_input: isRecording,
        },
        session_id: sessionId,
        consent: true,
      };

      const response = await apiService.performTriage(triageRequest);

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.patient_summary,
        timestamp: new Date(),
        triage_data: response,
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (response.triage_level === 'emergency' || response.triage_level === 'urgent') {
        // Vibration.vibrate(1000);
      }
    } catch (error) {
      console.error('Triage error:', error);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'I apologize, but I encountered an error. Please check your connection and try again. If symptoms persist, please seek medical attention.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const shareReport = async (triageData: TriageResponse) => {
    const reportText = `
 DEDAN Health Triage Report
 ========================
 Triage Level: ${triageData.triage_level.toUpperCase()}
 Summary: ${triageData.patient_summary}
 Next Step: ${triageData.suggested_next_step}
 Confidence: ${Math.round(triageData.confidence_score * 100)}%

 ${triageData.disclaimer}
    `.trim();

    try {
      await Share.share({
        message: reportText,
        title: 'DEDAN Health Triage Report',
      });
    } catch (error) {
      console.error('Share error:', error);
    }
  };

  const getTriageColor = (level: string) => {
    switch (level) {
      case 'emergency': return '#d32f2f';
      case 'urgent': return '#f57c00';
      case 'routine': return '#1976d2';
      case 'self_care': return '#388e3c';
      default: return '#666666';
    }
  };

  const getTriageIcon = (level: string) => {
    switch (level) {
      case 'emergency': return '🔴';
      case 'urgent': return '🟡';
      case 'routine': return '🟢';
      case 'self_care': return '🔵';
      default: return '⚪';
    }
  };

  const renderMessage = (message: ChatMessage) => (
    <View key={message.id} style={styles.messageContainer}>
      <View style={[
        styles.messageBubble,
        message.type === 'user' ? styles.userMessage : styles.assistantMessage
      ]}>
        <Text style={[
          styles.messageText,
          message.type === 'user' ? styles.userMessageText : styles.assistantMessageText
        ]}>
          {message.content}
        </Text>
        <Text style={styles.messageTime}>
          {message.timestamp.toLocaleTimeString()}
        </Text>
      </View>

      {/* Triage Results */}
      {message.triage_data && (
        <View style={styles.triageResult}>
          <View style={styles.triageHeader}>
            <Text style={styles.triageIcon}>
              {getTriageIcon(message.triage_data.triage_level)}
            </Text>
            <View style={styles.triageInfo}>
              <Text style={[
                styles.triageLevel,
                { color: getTriageColor(message.triage_data.triage_level) }
              ]}>
                {message.triage_data.triage_level.toUpperCase()}
              </Text>
              <Text style={styles.confidenceText}>
                Confidence: {Math.round(message.triage_data.confidence_score * 100)}%
              </Text>
            </View>
          </View>

          <Text style={styles.nextStepText}>
            <Text style={styles.nextStepLabel}>Next Step: </Text>
            {message.triage_data.suggested_next_step}
          </Text>

          {message.triage_data.emergency_contacts && (
            <View style={styles.emergencyContacts}>
              <Text style={styles.emergencyTitle}>Emergency Contacts:</Text>
              {message.triage_data.emergency_contacts.map((contact: string, index: number) => (
                <Text key={index} style={styles.contactText}>• {contact}</Text>
              ))}
            </View>
          )}

          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={styles.shareButton}
              onPress={() => shareReport(message.triage_data!)}
            >
              <Icon name="share" size={16} color="#1976d2" />
              <Text style={styles.shareButtonText}>Share Report</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.disclaimerText}>
            {message.triage_data.disclaimer}
          </Text>
        </View>
      )}
    </View>
  );

  // Render safety alert for emergency/urgent responses
  const renderSafetyAlert = (response: any) => {
    if (!response) return null;
    
    const isEmergency = response.urgency === 'emergency';
    const isUrgent = response.urgency === 'urgent';
    
    if (!isEmergency && !isUrgent) return null;

    return (
      <View style={[
        styles.triageResult,
        { borderColor: isEmergency ? '#d32f2f' : '#f57c00', borderWidth: 2 }
      ]}>
        <Text style={[
          styles.triageLevel,
          { color: isEmergency ? '#d32f2f' : '#f57c00' }
        ]}>
          ⚠️ {isEmergency ? 'EMERGENCY' : 'URGENT'} - {response.safety_notice}
        </Text>
        {response.requires_professional_review && (
          <Text style={styles.nextStepText}>
            <Text style={styles.nextStepLabel}>Professional Review Required</Text>
          </Text>
        )}
        {response.warning_signs && response.warning_signs.length > 0 && (
          <Text style={styles.nextStepText}>
            <Text style={styles.nextStepLabel}>Warning Signs:</Text>
            {response.warning_signs.map((sign: string, i: number) => (
              <Text key={i}> • {sign}</Text>
            ))}
          </Text>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>DEDAN Triage Chat</Text>
        <Text style={styles.headerSubtitle}>AI-powered symptom assessment</Text>
      </View>

      <KeyboardAvoidingView 
        style={styles.flex} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          showsVerticalScrollIndicator={false}
        >
          {messages.map(renderMessage)}
          {isLoading && (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>DEDAN is analyzing your symptoms...</Text>
            </View>
          )}
          
          {/* Multimodal response */}
          {multimodalResponse && renderSafetyAlert(multimodalResponse)}
        </ScrollView>

        {/* Image preview */}
        {selectedImage && (
          <View style={styles.imagePreviewContainer}>
            <Image source={{ uri: selectedImage.uri }} style={styles.imagePreview} />
            <TouchableOpacity style={styles.imageRemoveButton} onPress={removeImage}>
              <Icon name="close" size={20} color="#fff" />
            </TouchableOpacity>
          </View>
        )}

        {/* Voice transcript tag */}
        {voiceTranscript ? (
          <View style={styles.voiceTranscriptContainer}>
            <Text style={styles.voiceTranscriptText} numberOfLines={2}>
              🎙 {voiceTranscript}
            </Text>
            <TouchableOpacity onPress={clearVoice}>
              <Icon name="close" size={16} color="#666" />
            </TouchableOpacity>
          </View>
        ) : null}

        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Describe your symptoms..."
            multiline
            maxLength={500}
            editable={!isLoading}
          />
          
          {/* Image attach button */}
          <TouchableOpacity 
            style={styles.iconButton} 
            onPress={() => pickImage('gallery')}
            disabled={isLoading}
          >
            <Icon name="image" size={24} color="#1976d2" />
          </TouchableOpacity>

          {/* Camera button */}
          <TouchableOpacity 
            style={styles.iconButton} 
            onPress={() => pickImage('camera')}
            disabled={isLoading}
          >
            <Icon name="camera-alt" size={24} color="#1976d2" />
          </TouchableOpacity>
          
          {/* Voice button */}
          <TouchableOpacity
            style={[
              styles.voiceButton,
              isRecording && styles.voiceButtonActive
            ]}
            onPress={isRecording ? stopRecording : startRecording}
            disabled={isLoading}
          >
            <Icon 
              name={isRecording ? "mic-off" : "mic"} 
              size={24} 
              color={isRecording ? "#ffffff" : "#1976d2"} 
            />
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[
              styles.sendButton,
              !inputText.trim() && !voiceTranscript && !selectedImage && styles.sendButtonDisabled
            ]}
            onPress={handleMultimodalSubmit}
            disabled={(!inputText.trim() && !voiceTranscript && !selectedImage) || isLoading}
          >
            <Icon name="send" size={24} color="#ffffff" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  flex: {
    flex: 1,
  },
  header: {
    backgroundColor: '#1976d2',
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  messageContainer: {
    marginBottom: 15,
  },
  messageBubble: {
    maxWidth: '80%',
    borderRadius: 12,
    paddingHorizontal: 15,
    paddingVertical: 10,
    marginBottom: 5,
  },
  userMessage: {
    backgroundColor: '#1976d2',
    alignSelf: 'flex-end',
  },
  assistantMessage: {
    backgroundColor: '#ffffff',
    alignSelf: 'flex-start',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userMessageText: {
    color: '#ffffff',
  },
  assistantMessageText: {
    color: '#333333',
  },
  messageTime: {
    fontSize: 12,
    color: '#666666',
    marginTop: 5,
    textAlign: 'right',
  },
  triageResult: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 15,
    marginTop: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  triageHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  triageIcon: {
    fontSize: 24,
    marginRight: 10,
  },
  triageInfo: {
    flex: 1,
  },
  triageLevel: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  confidenceText: {
    fontSize: 12,
    color: '#666666',
  },
  nextStepText: {
    fontSize: 14,
    marginBottom: 10,
    lineHeight: 20,
  },
  nextStepLabel: {
    fontWeight: 'bold',
  },
  emergencyContacts: {
    backgroundColor: '#ffebee',
    borderRadius: 4,
    padding: 10,
    marginBottom: 10,
  },
  emergencyTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#c62828',
    marginBottom: 5,
  },
  contactText: {
    fontSize: 13,
    color: '#333333',
    marginBottom: 2,
  },
  actionButtons: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  shareButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e3f2fd',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  shareButtonText: {
    fontSize: 14,
    color: '#1976d2',
    marginLeft: 5,
  },
  disclaimerText: {
    fontSize: 12,
    color: '#666666',
    fontStyle: 'italic',
  },
  loadingContainer: {
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#666666',
    fontStyle: 'italic',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#ffffff',
    paddingHorizontal: 15,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 10,
    marginRight: 10,
    maxHeight: 100,
    fontSize: 16,
  },
  voiceButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#e3f2fd',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  voiceButtonActive: {
    backgroundColor: '#d32f2f',
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#1976d2',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#cccccc',
  },
  // Multimodal additions
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#e3f2fd',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 5,
  },
  imagePreviewContainer: {
    position: 'relative',
    marginHorizontal: 20,
    marginVertical: 8,
  },
  imagePreview: {
    width: '100%',
    height: 150,
    borderRadius: 8,
  },
  imageRemoveButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceTranscriptContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e3f2fd',
    marginHorizontal: 20,
    marginVertical: 4,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  voiceTranscriptText: {
    flex: 1,
    fontSize: 14,
    color: '#1976d2',
    marginRight: 8,
  },
});

export default TriageChatScreen;
