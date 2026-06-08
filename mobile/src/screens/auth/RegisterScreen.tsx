import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, Alert, ScrollView,
} from 'react-native';
import { useAuth } from '../../store/AuthContext';

export default function RegisterScreen({ navigation }: any) {
  const { register } = useAuth();
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    passwordConfirm: '',
    user_type: 'TENANT' as 'TENANT' | 'LANDLORD',
    phone_number: '',
  });
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!form.username || !form.email || !form.password || !form.phone_number) {
      Alert.alert('오류', '모든 필수 항목을 입력해주세요.');
      return;
    }
    if (form.password !== form.passwordConfirm) {
      Alert.alert('오류', '비밀번호가 일치하지 않습니다.');
      return;
    }
    if (form.password.length < 8) {
      Alert.alert('오류', '비밀번호는 8자 이상이어야 합니다.');
      return;
    }

    setLoading(true);
    try {
      await register({
        username: form.username,
        email: form.email,
        password: form.password,
        user_type: form.user_type,
        phone_number: form.phone_number,
      });
    } catch (error: any) {
      const msg = error.response?.data?.username?.[0] || '회원가입에 실패했습니다.';
      Alert.alert('오류', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.inner}>
      <Text style={styles.title}>회원가입</Text>

      {/* User Type Selection */}
      <View style={styles.typeRow}>
        <TouchableOpacity
          style={[styles.typeBtn, form.user_type === 'TENANT' && styles.typeBtnActive]}
          onPress={() => setForm({ ...form, user_type: 'TENANT' })}
        >
          <Text style={[styles.typeText, form.user_type === 'TENANT' && styles.typeTextActive]}>
            임차인
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.typeBtn, form.user_type === 'LANDLORD' && styles.typeBtnActive]}
          onPress={() => setForm({ ...form, user_type: 'LANDLORD' })}
        >
          <Text style={[styles.typeText, form.user_type === 'LANDLORD' && styles.typeTextActive]}>
            임대인
          </Text>
        </TouchableOpacity>
      </View>

      <TextInput style={styles.input} placeholder="아이디 *" value={form.username}
        onChangeText={(v) => setForm({ ...form, username: v })} autoCapitalize="none" />
      <TextInput style={styles.input} placeholder="이메일 *" value={form.email}
        onChangeText={(v) => setForm({ ...form, email: v })} keyboardType="email-address" autoCapitalize="none" />
      <TextInput style={styles.input} placeholder="전화번호 *" value={form.phone_number}
        onChangeText={(v) => setForm({ ...form, phone_number: v })} keyboardType="phone-pad" />
      <TextInput style={styles.input} placeholder="비밀번호 * (8자 이상)" value={form.password}
        onChangeText={(v) => setForm({ ...form, password: v })} secureTextEntry />
      <TextInput style={styles.input} placeholder="비밀번호 확인 *" value={form.passwordConfirm}
        onChangeText={(v) => setForm({ ...form, passwordConfirm: v })} secureTextEntry />

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={handleRegister}
        disabled={loading}
      >
        <Text style={styles.buttonText}>{loading ? '가입 중...' : '회원가입'}</Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={() => navigation.goBack()}>
        <Text style={styles.link}>이미 계정이 있으신가요? 로그인</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  inner: { paddingHorizontal: 30, paddingTop: 60, paddingBottom: 40 },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', marginBottom: 30 },
  typeRow: { flexDirection: 'row', marginBottom: 20, gap: 10 },
  typeBtn: {
    flex: 1, padding: 12, borderRadius: 8, borderWidth: 1,
    borderColor: '#ddd', alignItems: 'center',
  },
  typeBtnActive: { backgroundColor: '#007bff', borderColor: '#007bff' },
  typeText: { fontSize: 16, color: '#333' },
  typeTextActive: { color: '#fff', fontWeight: 'bold' },
  input: {
    borderWidth: 1, borderColor: '#ddd', borderRadius: 8,
    padding: 15, marginBottom: 12, fontSize: 16,
  },
  button: {
    backgroundColor: '#007bff', borderRadius: 8,
    padding: 15, alignItems: 'center', marginTop: 10,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  link: { textAlign: 'center', color: '#007bff', marginTop: 20, fontSize: 14 },
});
