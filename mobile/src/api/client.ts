import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: JWT 토큰 자동 첨부
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: 401 시 토큰 갱신
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = await AsyncStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          await AsyncStorage.setItem('access_token', access);
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // 토큰 갱신 실패 → 로그아웃
        await AsyncStorage.removeItem('access_token');
        await AsyncStorage.removeItem('refresh_token');
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login/', { username, password }),
  register: (data: any) =>
    api.post('/auth/register/', data),
  me: () => api.get('/auth/me/'),
  updateProfile: (data: any) => api.patch('/auth/profile/', data),
  refreshToken: (refresh: string) =>
    api.post('/auth/token/refresh/', { refresh }),
};

// Dashboard API
export const dashboardAPI = {
  get: () => api.get('/dashboard/'),
};

// Contract API
export const contractAPI = {
  list: () => api.get('/contracts/'),
  detail: (id: number) => api.get(`/contracts/${id}/`),
  create: (data: any) => api.post('/contracts/', data),
  extend: (id: number, months: number, note?: string) =>
    api.post(`/contracts/${id}/extend/`, { months, note }),
  terminate: (id: number, note?: string) =>
    api.post(`/contracts/${id}/terminate/`, { note }),
  history: (id: number) => api.get(`/contracts/${id}/history/`),
};

// Record API
export const recordAPI = {
  list: (contractId: number) => api.get(`/contracts/${contractId}/records/`),
  detail: (id: number) => api.get(`/records/${id}/`),
  create: (contractId: number, data: any) =>
    api.post(`/contracts/${contractId}/records/`, data),
  uploadPhotos: (id: number, formData: FormData) =>
    api.post(`/records/${id}/upload-photos/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  saveResponses: (id: number, responses: any[]) =>
    api.post(`/records/${id}/save-responses/`, { responses }),
  submit: (id: number) => api.post(`/records/${id}/submit/`),
  approve: (id: number, action: string, comment?: string) =>
    api.post(`/records/${id}/approve/`, { action, comment }),
};

// Defect API
export const defectAPI = {
  list: (contractId: number) => api.get(`/contracts/${contractId}/defects/`),
  detail: (id: number) => api.get(`/defects/${id}/`),
  create: (contractId: number, formData: FormData) =>
    api.post(`/contracts/${contractId}/defects/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  respond: (id: number, action: string, response?: string) =>
    api.post(`/defects/${id}/respond/`, { action, response }),
};

// Repair API
export const repairAPI = {
  list: (contractId: number) => api.get(`/contracts/${contractId}/repairs/`),
  detail: (id: number) => api.get(`/repairs/${id}/`),
  create: (contractId: number, formData: FormData) =>
    api.post(`/contracts/${contractId}/repairs/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  updateStatus: (id: number, action: string, data?: any) =>
    api.post(`/repairs/${id}/update-status/`, { action, ...data }),
  comment: (id: number, message: string) =>
    api.post(`/repairs/${id}/comment/`, { message }),
};

// Expense API
export const expenseAPI = {
  list: (contractId: number) => api.get(`/contracts/${contractId}/expenses/`),
  detail: (id: number) => api.get(`/expenses/${id}/`),
  create: (contractId: number, formData: FormData) =>
    api.post(`/contracts/${contractId}/expenses/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  summary: (contractId: number) =>
    api.get(`/contracts/${contractId}/expenses/summary/`),
};

// Recording API
export const recordingAPI = {
  list: () => api.get('/recordings/'),
  detail: (id: number) => api.get(`/recordings/${id}/`),
  consent: (id: number, action: string, reason?: string) =>
    api.post(`/recordings/${id}/consent/`, { action, reason }),
};

// Report API
export const reportAPI = {
  generate: (recordId: number, language?: string) =>
    api.post(`/reports/generate/${recordId}/`, { language }),
};

// Template API
export const templateAPI = {
  list: (country?: string, propertyType?: string) =>
    api.get('/templates/', { params: { country, property_type: propertyType } }),
};
