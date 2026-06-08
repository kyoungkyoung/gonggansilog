import React, { useEffect, useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet,
  TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { contractAPI } from '../../api/client';

export default function ContractDetailScreen({ route, navigation }: any) {
  const { id } = route.params;
  const [contract, setContract] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadContract();
  }, [id]);

  const loadContract = async () => {
    try {
      const response = await contractAPI.detail(id);
      setContract(response.data);
    } catch (error) {
      console.error('Contract detail error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#007bff" />
      </View>
    );
  }

  if (!contract) {
    return (
      <View style={styles.loading}>
        <Text>계약 정보를 불러올 수 없습니다.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.addressCard}>
        <Text style={styles.address}>{contract.display_address}</Text>
        <View style={[
          styles.statusBadge,
          { backgroundColor: contract.is_finalized ? '#28a745' : '#ffc107' }
        ]}>
          <Text style={styles.statusText}>
            {contract.is_finalized ? '계약 확정' : '진행중'}
          </Text>
        </View>
      </View>

      {/* Contract Info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>계약 정보</Text>
        <InfoRow label="계약일" value={contract.contract_date} />
        <InfoRow label="입실일" value={contract.move_in_date} />
        <InfoRow label="퇴실일" value={contract.move_out_date || '미정'} />
        <InfoRow label="임대인" value={contract.landlord?.username || contract.landlord_name || '-'} />
        <InfoRow label="임차인" value={contract.tenant?.username || contract.tenant_name || '-'} />
      </View>

      {/* Quick Stats */}
      <View style={styles.statsRow}>
        <StatCard label="기록" count={contract.records_count} color="#007bff" />
        <StatCard label="하자" count={contract.defects_count} color="#dc3545" />
        <StatCard label="수리" count={contract.repairs_count} color="#fd7e14" />
      </View>

      {/* Blockchain */}
      {contract.is_finalized && contract.blockchain_status === 'ANCHORED' && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>블록체인 증거</Text>
          <Text style={styles.hashText}>
            TX: {contract.blockchain_tx_hash?.substring(0, 20)}...
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

function StatCard({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <Text style={[styles.statCount, { color }]}>{count}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  addressCard: {
    backgroundColor: '#007bff', padding: 20,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
  },
  address: { fontSize: 18, fontWeight: 'bold', color: '#fff', flex: 1 },
  statusBadge: { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 15 },
  statusText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  section: {
    backgroundColor: '#fff', margin: 15, borderRadius: 10,
    padding: 15, shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1, shadowRadius: 3, elevation: 2,
  },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 12 },
  infoRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    paddingVertical: 8, borderBottomWidth: 0.5, borderBottomColor: '#eee',
  },
  infoLabel: { fontSize: 14, color: '#666' },
  infoValue: { fontSize: 14, fontWeight: '500' },
  statsRow: { flexDirection: 'row', paddingHorizontal: 15, gap: 8 },
  statCard: {
    flex: 1, backgroundColor: '#fff', borderRadius: 10, padding: 15,
    alignItems: 'center', borderLeftWidth: 3,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1, shadowRadius: 3, elevation: 2,
  },
  statCount: { fontSize: 24, fontWeight: 'bold' },
  statLabel: { fontSize: 12, color: '#666', marginTop: 2 },
  hashText: { fontSize: 12, color: '#666', fontFamily: 'monospace' },
});
