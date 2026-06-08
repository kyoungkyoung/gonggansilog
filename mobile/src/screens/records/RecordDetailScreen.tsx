import React, { useEffect, useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, Image,
  TouchableOpacity, Alert, ActivityIndicator,
} from 'react-native';
import { useAuth } from '../../store/AuthContext';
import { recordAPI } from '../../api/client';

export default function RecordDetailScreen({ route, navigation }: any) {
  const { id } = route.params;
  const { user } = useAuth();
  const [record, setRecord] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadRecord(); }, [id]);

  const loadRecord = async () => {
    try {
      const response = await recordAPI.detail(id);
      setRecord(response.data);
    } catch (error) {
      console.error('Record detail error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    Alert.alert('제출', '기록을 제출하시겠습니까?', [
      { text: '취소', style: 'cancel' },
      {
        text: '제출', onPress: async () => {
          try {
            await recordAPI.submit(id);
            Alert.alert('완료', '제출되었습니다.');
            loadRecord();
          } catch (e: any) {
            Alert.alert('오류', e.response?.data?.error || '제출에 실패했습니다.');
          }
        }
      },
    ]);
  };

  const handleApprove = async (action: string) => {
    try {
      await recordAPI.approve(id, action);
      Alert.alert('완료', action === 'approve' ? '승인되었습니다.' : '반려되었습니다.');
      loadRecord();
    } catch (e: any) {
      Alert.alert('오류', '처리에 실패했습니다.');
    }
  };

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" /></View>;
  if (!record) return <View style={styles.center}><Text>기록을 불러올 수 없습니다.</Text></View>;

  const typeLabel: any = { MOVE_IN: '입실', MOVE_OUT: '퇴실', PRE_MOVE_OUT: '사전 점검' };
  const statusLabel: any = {
    REQUESTED: '요청됨', OPEN: '업로드 가능', SUBMITTED: '제출됨',
    APPROVED: '승인됨', REJECTED: '반려됨',
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{typeLabel[record.record_type]} 기록</Text>
        <View style={[styles.badge, {
          backgroundColor: record.status === 'APPROVED' ? '#28a745' :
            record.status === 'REJECTED' ? '#dc3545' : '#007bff'
        }]}>
          <Text style={styles.badgeText}>{statusLabel[record.status]}</Text>
        </View>
      </View>

      {/* Inspection Results */}
      {record.item_responses?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>점검 결과</Text>
          {record.item_responses.map((resp: any) => (
            <View key={resp.id} style={styles.responseRow}>
              <Text style={styles.responseItem}>{resp.item_name}</Text>
              <View style={[styles.condBadge, {
                backgroundColor:
                  resp.condition_status === 'NORMAL' ? '#28a745' :
                  resp.condition_status === 'DEFECTIVE' ? '#dc3545' :
                  resp.condition_status === 'AGED' ? '#17a2b8' : '#fd7e14'
              }]}>
                <Text style={styles.condText}>
                  {resp.condition_status === 'NORMAL' ? '정상' :
                   resp.condition_status === 'DEFECTIVE' ? '하자' :
                   resp.condition_status === 'AGED' ? '노후' : '수리필요'}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Photos */}
      <View style={styles.section}>
        <View style={styles.row}>
          <Text style={styles.sectionTitle}>사진 ({record.photos?.length || 0})</Text>
          {(record.status === 'OPEN' || record.status === 'REJECTED') && (
            <TouchableOpacity
              style={styles.uploadBtn}
              onPress={() => navigation.navigate('AddPhotos', { recordId: id })}
            >
              <Text style={styles.uploadBtnText}>+ 사진 추가</Text>
            </TouchableOpacity>
          )}
        </View>
        <View style={styles.photoGrid}>
          {record.photos?.map((photo: any) => (
            <Image key={photo.id} source={{ uri: photo.image_url }} style={styles.photo} />
          ))}
        </View>
        {(!record.photos || record.photos.length === 0) && (
          <Text style={styles.emptyText}>사진이 없습니다.</Text>
        )}
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        {record.status === 'OPEN' && user?.user_type === 'TENANT' && (
          <TouchableOpacity style={[styles.actionBtn, { backgroundColor: '#007bff' }]} onPress={handleSubmit}>
            <Text style={styles.actionBtnText}>제출하기</Text>
          </TouchableOpacity>
        )}
        {record.status === 'SUBMITTED' && user?.user_type === 'LANDLORD' && (
          <View style={styles.row}>
            <TouchableOpacity
              style={[styles.actionBtn, { backgroundColor: '#28a745', flex: 1, marginRight: 5 }]}
              onPress={() => handleApprove('approve')}
            >
              <Text style={styles.actionBtnText}>승인</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionBtn, { backgroundColor: '#dc3545', flex: 1, marginLeft: 5 }]}
              onPress={() => handleApprove('reject')}
            >
              <Text style={styles.actionBtnText}>반려</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    backgroundColor: '#007bff', padding: 20,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
  },
  title: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  badge: { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 15 },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  section: {
    backgroundColor: '#fff', margin: 15, borderRadius: 10, padding: 15,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1, shadowRadius: 3, elevation: 2,
  },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 10 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  responseRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 8, borderBottomWidth: 0.5, borderBottomColor: '#eee',
  },
  responseItem: { fontSize: 14, flex: 1 },
  condBadge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 10 },
  condText: { color: '#fff', fontSize: 11, fontWeight: 'bold' },
  photoGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  photo: { width: 100, height: 100, borderRadius: 8 },
  emptyText: { color: '#999', textAlign: 'center', paddingVertical: 20 },
  uploadBtn: { backgroundColor: '#007bff', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  uploadBtnText: { color: '#fff', fontSize: 13, fontWeight: 'bold' },
  actions: { padding: 15 },
  actionBtn: { borderRadius: 10, padding: 15, alignItems: 'center' },
  actionBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
