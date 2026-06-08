import React, { useEffect, useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, Image,
  TouchableOpacity, TextInput, Alert, ActivityIndicator,
} from 'react-native';
import { useAuth } from '../../store/AuthContext';
import { repairAPI } from '../../api/client';

export default function RepairDetailScreen({ route }: any) {
  const { id } = route.params;
  const { user } = useAuth();
  const [repair, setRepair] = useState<any>(null);
  const [comment, setComment] = useState('');
  const [costInput, setCostInput] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadRepair(); }, [id]);

  const loadRepair = async () => {
    try {
      const res = await repairAPI.detail(id);
      setRepair(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleStatus = async (action: string) => {
    try {
      const data: any = {};
      if (action === 'provide_quote') data.estimated_cost = parseInt(costInput);
      if (action === 'complete_repair') data.actual_cost = parseInt(costInput || repair.estimated_cost);
      await repairAPI.updateStatus(id, action, data);
      Alert.alert('완료', '처리되었습니다.');
      loadRepair();
    } catch (e) { Alert.alert('오류', '처리에 실패했습니다.'); }
  };

  const handleComment = async () => {
    if (!comment.trim()) return;
    try {
      await repairAPI.comment(id, comment);
      setComment('');
      loadRepair();
    } catch (e) { Alert.alert('오류', '코멘트 등록에 실패했습니다.'); }
  };

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" /></View>;
  if (!repair) return <View style={styles.center}><Text>불러올 수 없습니다.</Text></View>;

  const statusLabel: any = {
    REQUESTED: '요청됨', QUOTE_PROVIDED: '견적 제시', APPROVED: '승인됨',
    IN_PROGRESS: '수리 중', COMPLETED: '완료', CANCELLED: '취소',
  };
  const statusColor: any = {
    REQUESTED: '#dc3545', QUOTE_PROVIDED: '#17a2b8', APPROVED: '#007bff',
    IN_PROGRESS: '#ffc107', COMPLETED: '#28a745', CANCELLED: '#6c757d',
  };

  return (
    <ScrollView style={styles.container}>
      <View style={[styles.header, { backgroundColor: statusColor[repair.status] }]}>
        <Text style={styles.title}>{repair.title}</Text>
        <Text style={styles.statusText}>{statusLabel[repair.status]}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.desc}>{repair.description}</Text>
        {repair.location && <Text style={styles.meta}>📍 {repair.location}</Text>}
        <Text style={styles.meta}>요청자: {repair.requested_by?.username} · {repair.created_at?.substring(0, 10)}</Text>
      </View>

      {/* Cost */}
      {(repair.estimated_cost || repair.actual_cost) && (
        <View style={styles.costRow}>
          {repair.estimated_cost && (
            <View style={[styles.costCard, { borderLeftColor: '#17a2b8' }]}>
              <Text style={styles.costLabel}>견적</Text>
              <Text style={styles.costAmount}>{Number(repair.estimated_cost).toLocaleString()}원</Text>
            </View>
          )}
          {repair.actual_cost && (
            <View style={[styles.costCard, { borderLeftColor: '#28a745' }]}>
              <Text style={styles.costLabel}>실제 비용</Text>
              <Text style={styles.costAmount}>{Number(repair.actual_cost).toLocaleString()}원</Text>
            </View>
          )}
        </View>
      )}

      {/* Photos */}
      {repair.photos?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>사진</Text>
          <View style={styles.photoGrid}>
            {repair.photos.map((p: any) => (
              <View key={p.id}>
                <Image source={{ uri: p.image_url }} style={styles.photo} />
                <Text style={styles.photoType}>
                  {p.photo_type === 'ISSUE' ? '문제' : p.photo_type === 'IN_PROGRESS' ? '시공중' : '완료'}
                </Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Landlord Actions */}
      {user?.user_type === 'LANDLORD' && repair.status !== 'COMPLETED' && repair.status !== 'CANCELLED' && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>작업</Text>
          {repair.status === 'REQUESTED' && (
            <>
              <TextInput style={styles.input} placeholder="견적 금액" value={costInput}
                onChangeText={setCostInput} keyboardType="numeric" />
              <TouchableOpacity style={[styles.actionBtn, { backgroundColor: '#17a2b8' }]}
                onPress={() => handleStatus('provide_quote')}>
                <Text style={styles.actionText}>견적 제시</Text>
              </TouchableOpacity>
            </>
          )}
          {repair.status === 'APPROVED' && (
            <TouchableOpacity style={[styles.actionBtn, { backgroundColor: '#ffc107' }]}
              onPress={() => handleStatus('start_repair')}>
              <Text style={styles.actionText}>수리 시작</Text>
            </TouchableOpacity>
          )}
          {repair.status === 'IN_PROGRESS' && (
            <>
              <TextInput style={styles.input} placeholder="실제 비용" value={costInput}
                onChangeText={setCostInput} keyboardType="numeric" />
              <TouchableOpacity style={[styles.actionBtn, { backgroundColor: '#28a745' }]}
                onPress={() => handleStatus('complete_repair')}>
                <Text style={styles.actionText}>수리 완료</Text>
              </TouchableOpacity>
            </>
          )}
        </View>
      )}

      {repair.status === 'QUOTE_PROVIDED' && user?.user_type === 'TENANT' && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>견적: {Number(repair.estimated_cost).toLocaleString()}원</Text>
          <TouchableOpacity style={[styles.actionBtn, { backgroundColor: '#28a745' }]}
            onPress={() => handleStatus('approve_quote')}>
            <Text style={styles.actionText}>견적 승인</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Comments */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>코멘트</Text>
        {repair.comments?.map((c: any) => (
          <View key={c.id} style={styles.commentBox}>
            <Text style={styles.commentAuthor}>{c.author?.username}</Text>
            <Text>{c.message}</Text>
            <Text style={styles.commentDate}>{c.created_at?.substring(0, 16)}</Text>
          </View>
        ))}
        {repair.status !== 'COMPLETED' && repair.status !== 'CANCELLED' && (
          <View style={styles.commentInput}>
            <TextInput style={[styles.input, { flex: 1 }]} placeholder="코멘트 입력"
              value={comment} onChangeText={setComment} />
            <TouchableOpacity style={styles.sendBtn} onPress={handleComment}>
              <Text style={styles.sendText}>전송</Text>
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
  header: { padding: 20 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  statusText: { color: 'rgba(255,255,255,0.9)', marginTop: 4 },
  section: { backgroundColor: '#fff', margin: 15, borderRadius: 10, padding: 15 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 10 },
  desc: { fontSize: 15, lineHeight: 22 },
  meta: { fontSize: 13, color: '#888', marginTop: 4 },
  costRow: { flexDirection: 'row', paddingHorizontal: 15, gap: 8 },
  costCard: { flex: 1, backgroundColor: '#fff', borderRadius: 10, padding: 12, borderLeftWidth: 3, alignItems: 'center' },
  costLabel: { fontSize: 12, color: '#666' },
  costAmount: { fontSize: 18, fontWeight: 'bold', marginTop: 4 },
  photoGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  photo: { width: 100, height: 100, borderRadius: 8 },
  photoType: { fontSize: 10, textAlign: 'center', color: '#666', marginTop: 2 },
  input: { backgroundColor: '#f8f9fa', borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 12, marginBottom: 10 },
  actionBtn: { borderRadius: 10, padding: 14, alignItems: 'center' },
  actionText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  commentBox: { backgroundColor: '#f8f9fa', borderRadius: 8, padding: 10, marginBottom: 8 },
  commentAuthor: { fontWeight: 'bold', marginBottom: 4 },
  commentDate: { fontSize: 11, color: '#888', marginTop: 4 },
  commentInput: { flexDirection: 'row', gap: 8, marginTop: 10 },
  sendBtn: { backgroundColor: '#007bff', borderRadius: 8, paddingHorizontal: 16, justifyContent: 'center' },
  sendText: { color: '#fff', fontWeight: 'bold' },
});
