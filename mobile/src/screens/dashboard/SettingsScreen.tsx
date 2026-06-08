import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../store/AuthContext';
import { changeLanguage } from '../../i18n';

export default function SettingsScreen() {
  const { user, logout } = useAuth();
  const { t, i18n } = useTranslation();

  const handleLogout = () => {
    Alert.alert(t('logout'), t('logoutConfirm'), [
      { text: t('cancel'), style: 'cancel' },
      { text: t('logout'), style: 'destructive', onPress: logout },
    ]);
  };

  const languages = [
    { code: 'ko', label: '한국어' },
    { code: 'en', label: 'English' },
    { code: 'ja', label: '日本語' },
  ];

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{t('settings')}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>{t('profile')}</Text>
        <Text style={styles.username}>{user?.username}</Text>
        <Text style={styles.info}>{user?.email}</Text>
        <Text style={styles.info}>
          {user?.user_type === 'TENANT' ? t('tenant') : t('landlord')}
        </Text>
        <Text style={styles.info}>{user?.phone_number}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>{t('language')}</Text>
        <View style={styles.langRow}>
          {languages.map((lang) => (
            <TouchableOpacity
              key={lang.code}
              style={[
                styles.langBtn,
                i18n.language === lang.code && styles.langBtnActive,
              ]}
              onPress={() => changeLanguage(lang.code)}
            >
              <Text style={[
                styles.langText,
                i18n.language === lang.code && styles.langTextActive,
              ]}>
                {lang.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>{t('logout')}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { backgroundColor: '#007bff', padding: 20, paddingTop: 60 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  card: {
    backgroundColor: '#fff', margin: 15, borderRadius: 10,
    padding: 20, shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1, shadowRadius: 3, elevation: 2,
  },
  cardTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 12, color: '#333' },
  username: { fontSize: 20, fontWeight: 'bold', marginBottom: 4 },
  info: { fontSize: 14, color: '#666', marginBottom: 2 },
  langRow: { flexDirection: 'row', gap: 10 },
  langBtn: {
    flex: 1, padding: 12, borderRadius: 8, borderWidth: 1,
    borderColor: '#ddd', alignItems: 'center',
  },
  langBtnActive: { backgroundColor: '#007bff', borderColor: '#007bff' },
  langText: { fontSize: 14, color: '#333' },
  langTextActive: { color: '#fff', fontWeight: 'bold' },
  logoutBtn: {
    backgroundColor: '#dc3545', margin: 15, borderRadius: 10,
    padding: 15, alignItems: 'center',
  },
  logoutText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
