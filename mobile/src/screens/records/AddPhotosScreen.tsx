import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, Image,
  TouchableOpacity, Alert, ActivityIndicator,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { recordAPI } from '../../api/client';

export default function AddPhotosScreen({ route, navigation }: any) {
  const { recordId } = route.params;
  const [photos, setPhotos] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);

  const pickImages = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsMultipleSelection: true,
      quality: 0.8,
    });

    if (!result.canceled) {
      setPhotos([...photos, ...result.assets]);
    }
  };

  const takePhoto = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('권한 필요', '카메라 접근 권한이 필요합니다.');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      quality: 0.8,
    });

    if (!result.canceled) {
      setPhotos([...photos, ...result.assets]);
    }
  };

  const removePhoto = (index: number) => {
    setPhotos(photos.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (photos.length === 0) {
      Alert.alert('오류', '사진을 선택해주세요.');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      photos.forEach((photo, i) => {
        const uri = photo.uri;
        const name = uri.split('/').pop() || `photo_${i}.jpg`;
        const type = 'image/jpeg';
        formData.append('images', { uri, name, type } as any);
        formData.append('categories', 'OTHER');
        formData.append('template_items', '');
      });

      await recordAPI.uploadPhotos(recordId, formData);
      Alert.alert('완료', `${photos.length}장의 사진이 업로드되었습니다.`);
      navigation.goBack();
    } catch (error: any) {
      Alert.alert('오류', '업로드에 실패했습니다.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      {/* Guidelines */}
      <View style={styles.guideCard}>
        <Text style={styles.guideTitle}>사진 촬영 가이드라인</Text>
        <View style={styles.guideRow}>
          <View style={styles.guideItem}>
            <Text style={styles.guideIcon}>📸</Text>
            <Text style={styles.guideLabel}>전체 촬영</Text>
          </View>
          <View style={styles.guideItem}>
            <Text style={styles.guideIcon}>🔍</Text>
            <Text style={styles.guideLabel}>근접 촬영</Text>
          </View>
          <View style={styles.guideItem}>
            <Text style={styles.guideIcon}>📍</Text>
            <Text style={styles.guideLabel}>위치 촬영</Text>
          </View>
          <View style={styles.guideItem}>
            <Text style={styles.guideIcon}>📅</Text>
            <Text style={styles.guideLabel}>날짜 증명</Text>
          </View>
        </View>
      </View>

      {/* Photo Actions */}
      <View style={styles.buttonRow}>
        <TouchableOpacity style={[styles.pickBtn, { backgroundColor: '#007bff' }]} onPress={takePhoto}>
          <Text style={styles.pickBtnText}>📷 카메라</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.pickBtn, { backgroundColor: '#28a745' }]} onPress={pickImages}>
          <Text style={styles.pickBtnText}>🖼 갤러리</Text>
        </TouchableOpacity>
      </View>

      {/* Preview */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>선택된 사진 ({photos.length})</Text>
        <View style={styles.photoGrid}>
          {photos.map((photo, index) => (
            <View key={index} style={styles.photoWrapper}>
              <Image source={{ uri: photo.uri }} style={styles.photo} />
              <TouchableOpacity style={styles.removeBtn} onPress={() => removePhoto(index)}>
                <Text style={styles.removeBtnText}>✕</Text>
              </TouchableOpacity>
            </View>
          ))}
        </View>
        {photos.length === 0 && (
          <Text style={styles.emptyText}>카메라 또는 갤러리에서 사진을 선택해주세요.</Text>
        )}
      </View>

      {/* Upload Button */}
      <TouchableOpacity
        style={[styles.uploadBtn, (uploading || photos.length === 0) && { opacity: 0.5 }]}
        onPress={handleUpload}
        disabled={uploading || photos.length === 0}
      >
        {uploading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.uploadBtnText}>업로드 ({photos.length}장)</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  guideCard: {
    backgroundColor: '#e3f2fd', margin: 15, borderRadius: 10, padding: 15,
  },
  guideTitle: { fontSize: 14, fontWeight: 'bold', color: '#0d47a1', marginBottom: 10 },
  guideRow: { flexDirection: 'row', justifyContent: 'space-around' },
  guideItem: { alignItems: 'center' },
  guideIcon: { fontSize: 24 },
  guideLabel: { fontSize: 11, color: '#333', marginTop: 4 },
  buttonRow: { flexDirection: 'row', paddingHorizontal: 15, gap: 10 },
  pickBtn: { flex: 1, borderRadius: 10, padding: 15, alignItems: 'center' },
  pickBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  section: {
    backgroundColor: '#fff', margin: 15, borderRadius: 10, padding: 15,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1, shadowRadius: 3, elevation: 2,
  },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 10 },
  photoGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  photoWrapper: { position: 'relative' },
  photo: { width: 100, height: 100, borderRadius: 8 },
  removeBtn: {
    position: 'absolute', top: -5, right: -5,
    backgroundColor: '#dc3545', borderRadius: 12,
    width: 24, height: 24, alignItems: 'center', justifyContent: 'center',
  },
  removeBtnText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  emptyText: { color: '#999', textAlign: 'center', paddingVertical: 30 },
  uploadBtn: {
    backgroundColor: '#007bff', margin: 15, borderRadius: 10,
    padding: 15, alignItems: 'center',
  },
  uploadBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
