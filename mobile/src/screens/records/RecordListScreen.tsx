import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity,
  StyleSheet, RefreshControl,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { recordAPI } from '../../api/client';

export default function RecordListScreen({ route, navigation }: any) {
  const { contractId } = route.params;
  const [records, setRecords] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadRecords = async () => {
    try {
      const response = await recordAPI.list(contractId);
      setRecords(response.data.results || response.data || []);
    } catch (error) {
      console.error('Record list error:', error);
    }
  };

  useFocusEffect(useCallback(() => { loadRecords(); }, []));

  const onRefresh = async () => {
    setRefreshing(true);
    await loadRecords();
    setRefreshing(false);
  };

  const typeLabel: any = { MOVE_IN: '입실', MOVE_OUT: '퇴실', PRE_MOVE_OUT: '사전 점검' };
  const typeColor: any = { MOVE_IN: '#28a745', MOVE_OUT: '#fd7e14', PRE_MOVE_OUT: '#17a2b8' };
  const statusLabel: any = {
    REQUESTED: '요청됨', OPEN: '업로드 가능', SUBMITTED: '제출됨',
    APPROVED: '승인됨', REJECTED: '반려됨',
  };
  const statusColor: any = {
    REQUESTED: '#6c757d', OPEN: '#ffc107', SUBMITTED: '#17a2b8',
    APPROVED: '#28a745', REJECTED: '#dc3545',
  };

  const renderRecord = ({ item }: any) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('RecordDetail', { id: item.id })}
    >
      <View style={styles.row}>
        <View style={[styles.badge, { backgroundColor: typeColor[item.record_type] }]}>
          <Text style={styles.badgeText}>{typeLabel[item.record_type]}</Text>
        </View>
        <View style={[styles.badge, { backgroundColor: statusColor[item.status] }]}>
          <Text style={styles.badgeText}>{statusLabel[item.status]}</Text>
        </View>
      </View>
      <View style={styles.row}>
        <Text style={styles.meta}>사진 {item.photo_count}장</Text>
        <Text style={styles.meta}>{item.created_at?.substring(0, 10)}</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={records}
        renderItem={renderRecord}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>기록이 없습니다.</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  list: { padding: 15 },
  card: {
    backgroundColor: '#fff', borderRadius: 10, padding: 15,
    marginBottom: 10, shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1, shadowRadius: 3, elevation: 2,
  },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  meta: { fontSize: 13, color: '#888' },
  empty: { alignItems: 'center', padding: 40 },
  emptyText: { color: '#999' },
});
