import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { FollowUpReminder } from '../types';

const FollowUpScreen: React.FC = () => {
  const [reminders, setReminders] = useState<FollowUpReminder[]>([]);

  useEffect(() => {
    loadReminders();
  }, []);

  const loadReminders = () => {
    // Mock data - in production, load from storage/API
    const mockReminders: FollowUpReminder[] = [
      {
        id: '1',
        session_id: 'session_123',
        message: 'How are you feeling today? Any changes in your symptoms?',
        scheduled_time: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours from now
        sent: false,
        type: 'check_in',
      },
      {
        id: '2',
        session_id: 'session_456',
        message: 'Reminder: Please take your prescribed medication as directed.',
        scheduled_time: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours from now
        sent: false,
        type: 'reminder',
      },
      {
        id: '3',
        session_id: 'session_789',
        message: 'Health tip: Stay hydrated and get adequate rest for faster recovery.',
        scheduled_time: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000), // 3 days from now
        sent: false,
        type: 'educational',
      },
    ];
    setReminders(mockReminders);
  };

  const markAsComplete = (reminderId: string) => {
    setReminders(prev =>
      prev.map(reminder =>
        reminder.id === reminderId
          ? { ...reminder, sent: true }
          : reminder
      )
    );
  };

  const deleteReminder = (reminderId: string) => {
    Alert.alert(
      'Delete Reminder',
      'Are you sure you want to delete this reminder?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () =>
            setReminders(prev => prev.filter(reminder => reminder.id !== reminderId)),
        },
      ]
    );
  };

  const getReminderIcon = (type: string) => {
    switch (type) {
      case 'check_in':
        return 'question-answer';
      case 'reminder':
        return 'notification-important';
      case 'educational':
        return 'school';
      default:
        return 'info';
    }
  };

  const getReminderColor = (type: string) => {
    switch (type) {
      case 'check_in':
        return '#1976d2';
      case 'reminder':
        return '#f57c00';
      case 'educational':
        return '#388e3c';
      default:
        return '#666666';
    }
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `In ${days} day${days > 1 ? 's' : ''}`;
    } else if (hours > 0) {
      return `In ${hours} hour${hours > 1 ? 's' : ''}`;
    } else {
      return 'Now';
    }
  };

  const renderReminder = (reminder: FollowUpReminder) => (
    <View key={reminder.id} style={styles.reminderCard}>
      <View style={styles.reminderHeader}>
        <View style={styles.reminderInfo}>
          <View style={[styles.reminderIcon, { backgroundColor: getReminderColor(reminder.type) }]}>
            <Icon name={getReminderIcon(reminder.type)} size={20} color="#ffffff" />
          </View>
          <View style={styles.reminderText}>
            <Text style={styles.reminderMessage}>{reminder.message}</Text>
            <Text style={styles.reminderTime}>{formatTime(reminder.scheduled_time)}</Text>
          </View>
        </View>
        <View style={styles.reminderStatus}>
          {reminder.sent ? (
            <View style={styles.completedBadge}>
              <Icon name="check-circle" size={16} color="#388e3c" />
              <Text style={styles.completedText}>Completed</Text>
            </View>
          ) : (
            <Text style={styles.pendingText}>Pending</Text>
          )}
        </View>
      </View>

      {!reminder.sent && (
        <View style={styles.reminderActions}>
          <TouchableOpacity
            style={styles.completeButton}
            onPress={() => markAsComplete(reminder.id)}
          >
            <Icon name="check" size={16} color="#ffffff" />
            <Text style={styles.completeButtonText}>Mark Complete</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.deleteButton}
            onPress={() => deleteReminder(reminder.id)}
          >
            <Icon name="delete" size={16} color="#d32f2f" />
            <Text style={styles.deleteButtonText}>Delete</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Follow-up Care</Text>
        <Text style={styles.subtitle}>Track your health progress and reminders</Text>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {reminders.length > 0 ? (
          reminders.map(renderReminder)
        ) : (
          <View style={styles.noReminders}>
            <Icon name="follow-the-signs" size={48} color="#cccccc" />
            <Text style={styles.noRemindersText}>No follow-up reminders yet</Text>
            <Text style={styles.noRemindersSubtext}>
              Complete a triage assessment to receive follow-up care reminders
            </Text>
          </View>
        )}
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
  reminderCard: {
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
  reminderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  reminderInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  reminderIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  reminderText: {
    flex: 1,
  },
  reminderMessage: {
    fontSize: 16,
    color: '#333333',
    marginBottom: 5,
    lineHeight: 22,
  },
  reminderTime: {
    fontSize: 14,
    color: '#666666',
  },
  reminderStatus: {
    alignItems: 'flex-end',
  },
  completedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e8f5e8',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  completedText: {
    fontSize: 12,
    color: '#388e3c',
    marginLeft: 4,
    fontWeight: '500',
  },
  pendingText: {
    fontSize: 12,
    color: '#f57c00',
    fontWeight: '500',
  },
  reminderActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  completeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1976d2',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  completeButtonText: {
    fontSize: 14,
    color: '#ffffff',
    marginLeft: 5,
    fontWeight: '500',
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffebee',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  deleteButtonText: {
    fontSize: 14,
    color: '#d32f2f',
    marginLeft: 5,
    fontWeight: '500',
  },
  noReminders: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 50,
  },
  noRemindersText: {
    fontSize: 18,
    color: '#666666',
    marginTop: 15,
    marginBottom: 5,
  },
  noRemindersSubtext: {
    fontSize: 14,
    color: '#999999',
    textAlign: 'center',
    lineHeight: 20,
  },
});

export default FollowUpScreen;
