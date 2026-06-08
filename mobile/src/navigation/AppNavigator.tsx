import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { ActivityIndicator, View, Text } from 'react-native';
import { useAuth } from '../store/AuthContext';

// Auth Screens
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';

// Main Screens
import DashboardScreen from '../screens/dashboard/DashboardScreen';
import ContractListScreen from '../screens/contracts/ContractListScreen';
import ContractDetailScreen from '../screens/contracts/ContractDetailScreen';
import ContractCreateScreen from '../screens/contracts/ContractCreateScreen';
import RecordingListScreen from '../screens/recordings/RecordingListScreen';
import SettingsScreen from '../screens/dashboard/SettingsScreen';

// Record Screens
import RecordListScreen from '../screens/records/RecordListScreen';
import RecordDetailScreen from '../screens/records/RecordDetailScreen';
import AddPhotosScreen from '../screens/records/AddPhotosScreen';

// Defect Screens
import DefectCreateScreen from '../screens/defects/DefectCreateScreen';
import DefectDetailScreen from '../screens/defects/DefectDetailScreen';

// Repair Screens
import RepairDetailScreen from '../screens/repairs/RepairDetailScreen';

// Expense Screens
import ExpenseCreateScreen from '../screens/expenses/ExpenseCreateScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#007bff',
        headerShown: false,
      }}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen}
        options={{ tabBarLabel: '홈', tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>🏠</Text> }} />
      <Tab.Screen name="Contracts" component={ContractListScreen}
        options={{ tabBarLabel: '계약', tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>📋</Text> }} />
      <Tab.Screen name="Recordings" component={RecordingListScreen}
        options={{ tabBarLabel: '녹음', tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>🎙</Text> }} />
      <Tab.Screen name="Settings" component={SettingsScreen}
        options={{ tabBarLabel: '설정', tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>⚙️</Text> }} />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#007bff" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {isAuthenticated ? (
          <>
            <Stack.Screen name="Main" component={MainTabs} />
            <Stack.Screen name="ContractDetail" component={ContractDetailScreen}
              options={{ headerShown: true, title: '계약 상세' }} />
            <Stack.Screen name="ContractCreate" component={ContractCreateScreen}
              options={{ headerShown: true, title: '계약 등록' }} />
            <Stack.Screen name="RecordList" component={RecordListScreen}
              options={{ headerShown: true, title: '입퇴실 기록' }} />
            <Stack.Screen name="RecordDetail" component={RecordDetailScreen}
              options={{ headerShown: true, title: '기록 상세' }} />
            <Stack.Screen name="AddPhotos" component={AddPhotosScreen}
              options={{ headerShown: true, title: '사진 추가' }} />
            <Stack.Screen name="DefectCreate" component={DefectCreateScreen}
              options={{ headerShown: true, title: '하자 신고' }} />
            <Stack.Screen name="DefectDetail" component={DefectDetailScreen}
              options={{ headerShown: true, title: '하자 상세' }} />
            <Stack.Screen name="RepairDetail" component={RepairDetailScreen}
              options={{ headerShown: true, title: '수리 상세' }} />
            <Stack.Screen name="ExpenseCreate" component={ExpenseCreateScreen}
              options={{ headerShown: true, title: '비용 등록' }} />
          </>
        ) : (
          <>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Register" component={RegisterScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
