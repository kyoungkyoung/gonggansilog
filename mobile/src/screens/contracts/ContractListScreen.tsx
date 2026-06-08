import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity,
  StyleSheet, RefreshControl,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { contractAPI } from '../../api/client';

export default function ContractListScreen({ navigation }: any) {
  const [contracts, setContracts] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadContracts = async () => {
    try {
      const response = await contractAPI.list();
      setContracts(response.data.results || []);
    } catch (error) {
      console.error('Contract list error:', error);
    }
  };

  useFocusEffect(useCallback(() => { loadContracts(); }, []));

  const onRefresh = async () => {
    setRefreshing(true);
    await loadContracts();
    setRefreshing(false);
  };

  const renderContract = ({ item }: any) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('ContractDetail', { id: item.id })}
    >
      <Text style={styles.address}>{item.display_address}</Text>
      <View style={styles.row}>
        <Text style={styles.date}>{item.contract_date}</Text>
        <View style={[
          styles.badge,
          { backgroundColor: item.blockchain_status === 'ANCHORED' ? '#28a745' : '#6c757d' }
        ]}>
          <Text style={styles.badgeText}>
            {item.is_finalized ? '확정' : '진행중'}
          </Text>
        </View>
      </View>
      <View style={styles.row}>
        {item.tenant_username && (
          <Text style={styles.party}>임차인: {item.tenant_username}</Text>
        )}
        {item.landlord_username && (
          <Text style={styles.party}>임대인: {item.landlord_username}</Text>
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>내 계약</Text>
      </View>
      <FlatList
        data={contracts}
        renderItem={renderContract}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>등록된 계약이 없습니다.</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { backgroundColor: '#007bff', padding: 20, paddingTop: 60 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  list: { padding: 15 },
  card: {
    backgroundColor: '#fff', borderRadius: 10, padding: 15,
    marginBottom: 10, shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1, shadowRadius: 3, elevation: 2,
  },
  address: { fontSize: 16, fontWeight: '600', marginBottom: 8 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  date: { fontSize: 13, color: '#666' },
  badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  party: { fontSize: 12, color: '#888' },
  empty: { alignItems: 'center', padding: 40 },
  emptyText: { color: '#999', fontSize: 14 },
});
