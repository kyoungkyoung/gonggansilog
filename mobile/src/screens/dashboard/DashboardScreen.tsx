import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { useAuth } from '../../store/AuthContext';
import { dashboardAPI, contractAPI } from '../../api/client';

export default function DashboardScreen({ navigation }: any) {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<any>(null);
  const [contracts, setContracts] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [dashRes, contractRes] = await Promise.all([
        dashboardAPI.get(),
        contractAPI.list(),
      ]);
      setDashboard(dashRes.data);
      setContracts(contractRes.data.results || []);
    } catch (error) {
      console.error('Dashboard load error:', error);
    }
  };

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, [])
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.greeting}>
          {user?.username}님, 환영합니다!
        </Text>
        <Text style={styles.userType}>
          {user?.user_type === 'TENANT' ? '임차인' : '임대인'}
        </Text>
      </View>

      {/* Notification Cards */}
      {dashboard && (
        <View style={styles.notifRow}>
          <View style={[styles.notifCard, { backgroundColor: '#e3f2fd' }]}>
            <Text style={styles.notifCount}>{dashboard.contracts_count}</Text>
            <Text style={styles.notifLabel}>계약</Text>
          </View>
          <View style={[styles.notifCard, { backgroundColor: '#fff3e0' }]}>
            <Text style={styles.notifCount}>{dashboard.unread_defects}</Text>
            <Text style={styles.notifLabel}>하자</Text>
          </View>
          <View style={[styles.notifCard, { backgroundColor: '#e8f5e9' }]}>
            <Text style={styles.notifCount}>{dashboard.unread_repairs}</Text>
            <Text style={styles.notifLabel}>수리</Text>
          </View>
          <View style={[styles.notifCard, { backgroundColor: '#fce4ec' }]}>
            <Text style={styles.notifCount}>{dashboard.pending_recordings}</Text>
            <Text style={styles.notifLabel}>녹음</Text>
          </View>
        </View>
      )}

      {/* Recent Contracts */}
      <Text style={styles.sectionTitle}>내 계약</Text>
      {contracts.length > 0 ? (
        contracts.map((contract: any) => (
          <TouchableOpacity
            key={contract.id}
            style={styles.contractCard}
            onPress={() => navigation.navigate('ContractDetail', { id: contract.id })}
          >
            <Text style={styles.contractAddress}>{contract.display_address}</Text>
            <View style={styles.contractInfo}>
              <Text style={styles.contractDate}>
                {contract.contract_date} ~ {contract.move_out_date || '미정'}
              </Text>
              <View style={[
                styles.statusBadge,
                { backgroundColor: contract.is_finalized ? '#28a745' : '#6c757d' }
              ]}>
                <Text style={styles.statusText}>
                  {contract.is_finalized ? '확정' : '진행중'}
                </Text>
              </View>
            </View>
          </TouchableOpacity>
        ))
      ) : (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyText}>등록된 계약이 없습니다.</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { backgroundColor: '#007bff', padding: 20, paddingTop: 60 },
  greeting: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  userType: { fontSize: 14, color: '#cce5ff', marginTop: 4 },
  notifRow: { flexDirection: 'row', padding: 15, gap: 8 },
  notifCard: {
    flex: 1, padding: 12, borderRadius: 10, alignItems: 'center',
  },
  notifCount: { fontSize: 24, fontWeight: 'bold', color: '#333' },
  notifLabel: { fontSize: 12, color: '#666', marginTop: 2 },
  sectionTitle: {
    fontSize: 18, fontWeight: 'bold', paddingHorizontal: 15,
    paddingTop: 10, paddingBottom: 8,
  },
  contractCard: {
    backgroundColor: '#fff', marginHorizontal: 15, marginBottom: 10,
    borderRadius: 10, padding: 15, shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 3,
    elevation: 2,
  },
  contractAddress: { fontSize: 16, fontWeight: '600', marginBottom: 8 },
  contractInfo: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  contractDate: { fontSize: 13, color: '#666' },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
  statusText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  emptyCard: {
    backgroundColor: '#fff', marginHorizontal: 15, borderRadius: 10,
    padding: 30, alignItems: 'center',
  },
  emptyText: { color: '#999', fontSize: 14 },
});
