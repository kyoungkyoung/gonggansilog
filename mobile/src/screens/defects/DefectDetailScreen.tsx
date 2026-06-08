import React, { useEffect, useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, Image,
  TouchableOpacity, TextInput, Alert, ActivityIndicator,
} from 'react-native';
import { useAuth } from '../../store/AuthContext';
import { defectAPI } from '../../api/client';

export default function DefectDetailScreen({ route }: any) {
  const { id } = route.params;
  const { user } = useAuth();
  const [defect, setDefect] = useState<any>(null);
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadDefect(); }, [id]);

  const loadDefect = async () => {
    try {
      const res = await defectAPI.detail(id);
      setDefect(res.data);
      setResponse(res.data.landlord_response || '');
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleRespond = async (action: string) => {
    try {
      await defectAPI.respond(id, action, response);
      Alert.alert('완료', '처리되었습니다.');
      loadDefect();
    } catch (e) { Alert.alert('오류', '처리에 실패했습니다.'); }
  };

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" /></View>;
  if (!defect) return <View style={styles.center}><Text>불러올 수 없습니다.</Text></View>;

  const sevColor: any = { CRITICAL: '#dc3545', MAJOR: '#ffc107', MINOR: '#6c757d' };
  const sevLabel: any = { CRITICAL: '긴급', MAJOR: '중요', MINOR: '경미' };
  const statusColor: any = { REPORTED: '#dc3545', ACKNOWLEDGED: '#17a2b8', IN_PROGRESS: '#ffc107', RESOLVED: '#28a745' };
  const statusLabel: any = { REPORTED: '신고됨', ACKNOWLEDGED: '확인됨', IN_PROGRESS: '처리중', RESOLVED: '해결됨' };

  return (
    <ScrollView style={styles.container}>
      <View style={[styles.header, { backgroundColor: statusColor[defect.status] }]}>
        <Text style={styles.title}>{defect.title}</Text>
        <View style={styles.badges}>
          <View style={[styles.badge, { backgroundColor: sevColor[defect.severity] }]}>
            <Text style={styles.badgeText}>{sevLabel[defect.severity]}</Text>
          </View>
          <View style={[styles.badge, { backgroundColor: 'rgba(255,255,255,0.3)' }]}>
            <Text style={styles.badgeText}>{statusLabel[defect.status]}</Text>
          </View>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.meta}>신고자: {defect.reported_by?.username} · {defect.created_at?.substring(0, 10)}</Text>
        {defect.location && <Text style={styles.meta}>📍 {defect.location}</Text>}
        <Text style={styles.desc}>{defect.description}</Text>
      </View>

      {defect.photos?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>사진</Text>
          <View style={styles.photoGrid}>
            {defect.photos.map((p: any) => (
              <Image key={p.id} source={{ uri: p.image_url }} style={styles.photo} />
            ))}
          </View>
        </View>
      )}

      {defect.landlord_response && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>임대인 답변</Text>
          <View style={styles.responseBox}>
            <Text>{defect.landlord_response}</Text>
          </View>
        </View>
      )}

      {user?.user_type === 'LANDLORD' && defect.status !== 'RESOLVED' && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>답변하기</Text>
          <TextInput style={styles.input} placeholder="답변을 입력하세요"
            value={response} onChangeText={setResponse} multiline />
          <View style={styles.actionRow}>
            {defect.status === 'REPORTED' && (
              <TouchableOpacity style={[styles.actionBtn, { backgroundColor: '#17a2b8' }]} onPress={() => handleRespond('acknowledge')}>
                <Text style={styles.actionText}>확인</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity style={[styles.actionBtn, { backgroundColor: '#ffc107' }]} onPress={() => handleRespond('in_progress')}>
              <Text style={styles.actionText}>처리중</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.actionBtn, { backgroundColor: '#28a745' }]} onPress={() => handleRespond('resolve')}>
              <Text style={styles.actionText}>해결</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { padding: 20 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#fff', marginBottom: 8 },
  badges: { flexDirection: 'row', gap: 8 },
  badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  section: { backgroundColor: '#fff', margin: 15, borderRadius: 10, padding: 15 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 10 },
  meta: { fontSize: 13, color: '#888', marginBottom: 4 },
  desc: { fontSize: 15, lineHeight: 22, marginTop: 10 },
  photoGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  photo: { width: 100, height: 100, borderRadius: 8 },
  responseBox: { backgroundColor: '#e3f2fd', padding: 12, borderRadius: 8, borderLeftWidth: 3, borderLeftColor: '#007bff' },
  input: { backgroundColor: '#f8f9fa', borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 12, minHeight: 80, textAlignVertical: 'top' },
  actionRow: { flexDirection: 'row', gap: 8, marginTop: 10 },
  actionBtn: { flex: 1, padding: 12, borderRadius: 8, alignItems: 'center' },
  actionText: { color: '#fff', fontWeight: 'bold' },
});
