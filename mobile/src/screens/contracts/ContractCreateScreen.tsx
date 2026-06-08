import React, { useState } from 'react';
import {
  View, Text, TextInput, ScrollView, StyleSheet,
  TouchableOpacity, Alert, ActivityIndicator,
} from 'react-native';
import { useAuth } from '../../store/AuthContext';
import { contractAPI } from '../../api/client';

export default function ContractCreateScreen({ navigation }: any) {
  const { user } = useAuth();
  const [form, setForm] = useState({
    address: '',
    contract_date: '',
    move_in_date: '',
    move_out_date: '',
    tenant_name: '',
    tenant_phone: '',
    landlord_name: '',
    landlord_phone: '',
    country: 'KR',
  });
  const [loading, setLoading] = useState(false);

  const updateField = (key: string, value: string) => {
    setForm({ ...form, [key]: value });
  };

  const handleSubmit = async () => {
    if (!form.address || !form.contract_date || !form.move_in_date) {
      Alert.alert('오류', '주소, 계약일, 입실일은 필수입니다.');
      return;
    }
    setLoading(true);
    try {
      const response = await contractAPI.create(form);
      Alert.alert('완료', '계약이 등록되었습니다.');
      navigation.replace('ContractDetail', { id: response.data.id });
    } catch (error: any) {
      Alert.alert('오류', '등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const isTenant = user?.user_type === 'TENANT';

  return (
    <ScrollView style={styles.container}>
      <View style={styles.form}>
        <Text style={styles.label}>주소 *</Text>
        <TextInput style={styles.input} placeholder="예: 서울시 강남구 테헤란로 123"
          value={form.address} onChangeText={(v) => updateField('address', v)} />

        <Text style={styles.label}>계약일 * (YYYY-MM-DD)</Text>
        <TextInput style={styles.input} placeholder="2026-01-01"
          value={form.contract_date} onChangeText={(v) => updateField('contract_date', v)} />

        <Text style={styles.label}>입실일 * (YYYY-MM-DD)</Text>
        <TextInput style={styles.input} placeholder="2026-02-01"
          value={form.move_in_date} onChangeText={(v) => updateField('move_in_date', v)} />

        <Text style={styles.label}>퇴실 예정일 (YYYY-MM-DD)</Text>
        <TextInput style={styles.input} placeholder="선택 사항"
          value={form.move_out_date} onChangeText={(v) => updateField('move_out_date', v)} />

        {isTenant ? (
          <>
            <Text style={styles.sectionHeader}>임대인 정보</Text>
            <TextInput style={styles.input} placeholder="임대인 이름"
              value={form.landlord_name} onChangeText={(v) => updateField('landlord_name', v)} />
            <TextInput style={styles.input} placeholder="임대인 연락처"
              value={form.landlord_phone} onChangeText={(v) => updateField('landlord_phone', v)} />
          </>
        ) : (
          <>
            <Text style={styles.sectionHeader}>임차인 정보</Text>
            <TextInput style={styles.input} placeholder="임차인 이름"
              value={form.tenant_name} onChangeText={(v) => updateField('tenant_name', v)} />
            <TextInput style={styles.input} placeholder="임차인 연락처"
              value={form.tenant_phone} onChangeText={(v) => updateField('tenant_phone', v)} />
          </>
        )}

        <TouchableOpacity style={[styles.submitBtn, loading && { opacity: 0.5 }]}
          onPress={handleSubmit} disabled={loading}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitText}>계약 등록</Text>}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  form: { padding: 20 },
  label: { fontSize: 14, fontWeight: 'bold', marginBottom: 6, marginTop: 12 },
  input: {
    backgroundColor: '#fff', borderWidth: 1, borderColor: '#ddd',
    borderRadius: 8, padding: 12, fontSize: 16, marginBottom: 4,
  },
  sectionHeader: { fontSize: 16, fontWeight: 'bold', marginTop: 20, marginBottom: 8, color: '#007bff' },
  submitBtn: { backgroundColor: '#007bff', borderRadius: 10, padding: 15, alignItems: 'center', marginTop: 20 },
  submitText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
