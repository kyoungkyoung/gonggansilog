import React, { useState } from 'react';
import {
  View, Text, TextInput, ScrollView, StyleSheet,
  TouchableOpacity, Image, Alert, ActivityIndicator,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { defectAPI } from '../../api/client';

export default function DefectCreateScreen({ route, navigation }: any) {
  const { contractId } = route.params;
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [severity, setSeverity] = useState('MINOR');
  const [photos, setPhotos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const pickImages = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsMultipleSelection: true,
      quality: 0.8,
    });
    if (!result.canceled) setPhotos([...photos, ...result.assets]);
  };

  const takePhoto = async () => {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) return;
    const result = await ImagePicker.launchCameraAsync({ quality: 0.8 });
    if (!result.canceled) setPhotos([...photos, ...result.assets]);
  };

  const handleSubmit = async () => {
    if (!title || !description) {
      Alert.alert('오류', '제목과 설명을 입력해주세요.');
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('description', description);
      formData.append('location', location);
      formData.append('severity', severity);
      photos.forEach((photo, i) => {
        formData.append('images', {
          uri: photo.uri,
          name: photo.uri.split('/').pop() || `photo_${i}.jpg`,
          type: 'image/jpeg',
        } as any);
      });
      await defectAPI.create(contractId, formData);
      Alert.alert('완료', '하자 신고가 등록되었습니다.');
      navigation.goBack();
    } catch (error) {
      Alert.alert('오류', '등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const severities = [
    { value: 'MINOR', label: '경미', color: '#6c757d' },
    { value: 'MAJOR', label: '중요', color: '#ffc107' },
    { value: 'CRITICAL', label: '긴급', color: '#dc3545' },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.form}>
        <Text style={styles.label}>제목 *</Text>
        <TextInput style={styles.input} placeholder="예: 화장실 천장 누수" value={title} onChangeText={setTitle} />

        <Text style={styles.label}>위치</Text>
        <TextInput style={styles.input} placeholder="예: 화장실, 주방" value={location} onChangeText={setLocation} />

        <Text style={styles.label}>심각도 *</Text>
        <View style={styles.severityRow}>
          {severities.map((s) => (
            <TouchableOpacity
              key={s.value}
              style={[styles.sevBtn, severity === s.value && { backgroundColor: s.color, borderColor: s.color }]}
              onPress={() => setSeverity(s.value)}
            >
              <Text style={[styles.sevText, severity === s.value && { color: '#fff' }]}>{s.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>설명 *</Text>
        <TextInput style={[styles.input, { height: 100 }]} placeholder="하자 상세 설명"
          value={description} onChangeText={setDescription} multiline textAlignVertical="top" />

        <Text style={styles.label}>사진</Text>
        <View style={styles.photoActions}>
          <TouchableOpacity style={styles.photoBtn} onPress={takePhoto}>
            <Text>📷 카메라</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.photoBtn} onPress={pickImages}>
            <Text>🖼 갤러리</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.photoGrid}>
          {photos.map((p, i) => (
            <View key={i} style={styles.photoWrap}>
              <Image source={{ uri: p.uri }} style={styles.photo} />
              <TouchableOpacity style={styles.removeBtn} onPress={() => setPhotos(photos.filter((_, idx) => idx !== i))}>
                <Text style={styles.removeTxt}>✕</Text>
              </TouchableOpacity>
            </View>
          ))}
        </View>

        <TouchableOpacity style={[styles.submitBtn, loading && { opacity: 0.5 }]} onPress={handleSubmit} disabled={loading}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitText}>하자 신고 등록</Text>}
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
  severityRow: { flexDirection: 'row', gap: 8 },
  sevBtn: { flex: 1, padding: 10, borderRadius: 8, borderWidth: 1, borderColor: '#ddd', alignItems: 'center' },
  sevText: { fontSize: 14, fontWeight: '600' },
  photoActions: { flexDirection: 'row', gap: 10, marginBottom: 10 },
  photoBtn: { flex: 1, backgroundColor: '#fff', padding: 12, borderRadius: 8, alignItems: 'center', borderWidth: 1, borderColor: '#ddd' },
  photoGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  photoWrap: { position: 'relative' },
  photo: { width: 80, height: 80, borderRadius: 8 },
  removeBtn: { position: 'absolute', top: -5, right: -5, backgroundColor: '#dc3545', borderRadius: 10, width: 20, height: 20, alignItems: 'center', justifyContent: 'center' },
  removeTxt: { color: '#fff', fontSize: 10 },
  submitBtn: { backgroundColor: '#dc3545', borderRadius: 10, padding: 15, alignItems: 'center', marginTop: 20 },
  submitText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
