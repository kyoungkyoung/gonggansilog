import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, RefreshControl,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { recordingAPI } from '../../api/client';

export default function RecordingListScreen() {
  const [recordings, setRecordings] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadRecordings = async () => {
    try {
      const response = await recordingAPI.list();
      setRecordings(response.data.results || []);
    } catch (error) {
      console.error('Recording list error:', error);
    }
  };

  useFocusEffect(useCallback(() => { loadRecordings(); }, []));

  const onRefresh = async () => {
    setRefreshing(true);
    await loadRecordings();
    setRefreshing(false);
  };

  const consentBadge = (status: string) => {
    const colors: any = {
      APPROVED: '#28a745',
      PENDING: '#ffc107',
      REJECTED: '#dc3545',
      NOT_REQUIRED: '#6c757d',
    };
    const labels: any = {
      APPROVED: '동의완료',
      PENDING: '대기중',
      REJECTED: '거절',
      NOT_REQUIRED: '',
    };
    if (!labels[status]) return null;
    return (
      <View style={[styles.badge, { backgroundColor: colors[status] }]}>
        <Text style={styles.badgeText}>{labels[status]}</Text>
      </View>
    );
  };

  const renderRecording = ({ item }: any) => (
    <View style={styles.card}>
      <View style={styles.row}>
        <Text style={styles.title}>{item.display_title}</Text>
        {consentBadge(item.consent_status)}
      </View>
      <Text style={styles.meta}>
        {item.recorded_at?.substring(0, 10)} · {item.duration_display}
      </Text>
      {item.summary ? (
        <Text style={styles.summary} numberOfLines={2}>{item.summary}</Text>
      ) : (
        <Text style={styles.processing}>
          {item.processing_status === 'COMPLETED' ? '' : 'AI 처리 중...'}
        </Text>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>녹음 기록</Text>
      </View>
      <FlatList
        data={recordings}
        renderItem={renderRecording}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>녹음 기록이 없습니다.</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { backgroundColor: '#007bff', padding: 20, paddingTop: 60 },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  list: { padding: 15 },
  card: {
    backgroundColor: '#fff', borderRadius: 10, padding: 15,
    marginBottom: 10, shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1, shadowRadius: 3, elevation: 2,
  },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 16, fontWeight: '600', flex: 1 },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  badgeText: { color: '#fff', fontSize: 11, fontWeight: 'bold' },
  meta: { fontSize: 12, color: '#888', marginTop: 4 },
  summary: { fontSize: 13, color: '#555', marginTop: 8 },
  processing: { fontSize: 12, color: '#ffc107', marginTop: 8 },
  empty: { alignItems: 'center', padding: 40 },
  emptyText: { color: '#999', fontSize: 14 },
});
