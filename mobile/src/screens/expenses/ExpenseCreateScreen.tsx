import React, { useState } from 'react';
import {
  View, Text, TextInput, ScrollView, StyleSheet,
  TouchableOpacity, Image, Alert, ActivityIndicator,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { expenseAPI } from '../../api/client';

export default function ExpenseCreateScreen({ route, navigation }: any) {
  const { contractId } = route.params;
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('REPAIR');
  const [paidBy, setPaidBy] = useState('LANDLORD');
  const [expenseDate, setExpenseDate] = useState('');
  const [description, setDescription] = useState('');
  const [receipt, setReceipt] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const pickReceipt = async () => {
    const result = await ImagePicker.launchCameraAsync({ quality: 0.8 });
    if (!result.canceled) setReceipt(result.assets[0]);
  };

  const handleSubmit = async () => {
    if (!title || !amount || !expenseDate) {
      Alert.alert('오류', '제목, 금액, 날짜는 필수입니다.');
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('amount', amount);
      formData.append('category', category);
      formData.append('paid_by', paidBy);
      formData.append('expense_date', expenseDate);
      formData.append('description', description);
      if (receipt) {
        formData.append('receipt_image', {
          uri: receipt.uri,
          name: 'receipt.jpg',
          type: 'image/jpeg',
        } as any);
      }
      await expenseAPI.create(contractId, formData);
      Alert.alert('완료', '비용이 등록되었습니다.');
      navigation.goBack();
    } catch (error) {
      Alert.alert('오류', '등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    { value: 'REPAIR', label: '수리비' },
    { value: 'CLEANING', label: '청소비' },
    { value: 'RESTORATION', label: '원상복구비' },
    { value: 'OTHER', label: '기타' },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.form}>
        <Text style={styles.label}>제목 *</Text>
        <TextInput style={styles.input} placeholder="예: 화장실 배관 수리비" value={title} onChangeText={setTitle} />

        <Text style={styles.label}>금액 *</Text>
        <TextInput style={styles.input} placeholder="금액 입력" value={amount}
          onChangeText={setAmount} keyboardType="numeric" />

        <Text style={styles.label}>카테고리</Text>
        <View style={styles.chipRow}>
          {categories.map((c) => (
            <TouchableOpacity key={c.value}
              style={[styles.chip, category === c.value && styles.chipActive]}
              onPress={() => setCategory(c.value)}>
              <Text style={[styles.chipText, category === c.value && { color: '#fff' }]}>{c.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>부담자</Text>
        <View style={styles.chipRow}>
          <TouchableOpacity
            style={[styles.chip, paidBy === 'LANDLORD' && styles.chipActive]}
            onPress={() => setPaidBy('LANDLORD')}>
            <Text style={[styles.chipText, paidBy === 'LANDLORD' && { color: '#fff' }]}>임대인</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.chip, paidBy === 'TENANT' && styles.chipActive]}
            onPress={() => setPaidBy('TENANT')}>
            <Text style={[styles.chipText, paidBy === 'TENANT' && { color: '#fff' }]}>임차인</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.label}>날짜 * (YYYY-MM-DD)</Text>
        <TextInput style={styles.input} placeholder="2026-01-01" value={expenseDate} onChangeText={setExpenseDate} />

        <Text style={styles.label}>영수증 사진</Text>
        <TouchableOpacity style={styles.receiptBtn} onPress={pickReceipt}>
          {receipt ? (
            <Image source={{ uri: receipt.uri }} style={styles.receiptImg} />
          ) : (
            <Text style={styles.receiptPlaceholder}>📷 영수증 촬영</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={[styles.submitBtn, loading && { opacity: 0.5 }]} onPress={handleSubmit} disabled={loading}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitText}>비용 등록</Text>}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  form: { padding: 20 },
  label: { fontSize: 14, fontWeight: 'bold', marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 12, fontSize: 16 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, borderWidth: 1, borderColor: '#ddd', backgroundColor: '#fff' },
  chipActive: { backgroundColor: '#007bff', borderColor: '#007bff' },
  chipText: { fontSize: 14 },
  receiptBtn: {
    backgroundColor: '#fff', borderWidth: 1, borderColor: '#ddd', borderRadius: 8,
    height: 150, alignItems: 'center', justifyContent: 'center', overflow: 'hidden',
  },
  receiptImg: { width: '100%', height: '100%', resizeMode: 'contain' },
  receiptPlaceholder: { color: '#999', fontSize: 16 },
  submitBtn: { backgroundColor: '#28a745', borderRadius: 10, padding: 15, alignItems: 'center', marginTop: 20 },
  submitText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
