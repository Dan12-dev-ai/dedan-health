import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/MaterialIcons';

import HomeScreen from '../screens/HomeScreen';
import PatientProfileScreen from '../screens/PatientProfileScreen';
import TriageChatScreen from '../screens/TriageChatScreen';
import ClinicFinderScreen from '../screens/ClinicFinderScreen';
import FollowUpScreen from '../screens/FollowUpScreen';
import SettingsScreen from '../screens/SettingsScreen';

export type RootStackParamList = {
  Home: undefined;
  PatientProfile: undefined;
  TriageChat: { profile: any; sessionId: string };
  ClinicFinder: undefined;
  FollowUp: undefined;
  Settings: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator();

const MainTabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Home':
              iconName = 'home';
              break;
            case 'ClinicFinder':
              iconName = 'local-hospital';
              break;
            case 'FollowUp':
              iconName = 'follow-the-signs';
              break;
            case 'Settings':
              iconName = 'settings';
              break;
            default:
              iconName = 'help';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#1976d2',
        tabBarInactiveTintColor: '#666666',
        tabBarStyle: {
          backgroundColor: '#ffffff',
          borderTopWidth: 1,
          borderTopColor: '#e0e0e0',
        },
        headerShown: false,
      })}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen}
        options={{ title: 'Home' }}
      />
      <Tab.Screen 
        name="ClinicFinder" 
        component={ClinicFinderScreen}
        options={{ title: 'Clinics' }}
      />
      <Tab.Screen 
        name="FollowUp" 
        component={FollowUpScreen}
        options={{ title: 'Follow-up' }}
      />
      <Tab.Screen 
        name="Settings" 
        component={SettingsScreen}
        options={{ title: 'Settings' }}
      />
    </Tab.Navigator>
  );
};

const AppNavigator: React.FC = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: {
            backgroundColor: '#1976d2',
          },
          headerTintColor: '#ffffff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        <Stack.Screen
          name="MainTabs"
          component={MainTabNavigator}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="PatientProfile"
          component={PatientProfileScreen}
          options={{ 
            title: 'Patient Information',
            headerBackTitle: 'Back'
          }}
        />
        <Stack.Screen
          name="TriageChat"
          component={TriageChatScreen}
          options={{ 
            title: 'DEDAN Triage',
            headerBackTitle: 'Back'
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;
