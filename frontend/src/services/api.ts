import axios from 'axios';
import type { Account, AccountCreate, Video, TaskLog, Stats, FetchRequest, UploadRequest, TikTokSource, TikTokSourceCreate, TaskProgress, ProxySettings, ProxyTestResult } from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
});

// Accounts API
export const accountsApi = {
  getAll: async (): Promise<Account[]> => {
    const response = await api.get('/accounts');
    return response.data;
  },

  create: async (account: AccountCreate): Promise<{ message: string }> => {
    const response = await api.post('/accounts', account);
    return response.data;
  },

  // Proxy management
  updateProxy: async (username: string, proxySettings: ProxySettings): Promise<{ message: string }> => {
    const response = await api.put(`/accounts/${username}/proxy`, proxySettings);
    return response.data;
  },

  removeProxy: async (username: string): Promise<{ message: string }> => {
    const response = await api.delete(`/accounts/${username}/proxy`);
    return response.data;
  },

  testProxy: async (username: string): Promise<ProxyTestResult> => {
    const response = await api.post(`/accounts/${username}/proxy/test`);
    return response.data;
  },

  getProxy: async (username: string): Promise<any> => {
    const response = await api.get(`/accounts/${username}/proxy`);
    return response.data;
  },
};

// Videos API
export const videosApi = {
  getAll: async (theme?: string, limit = 100): Promise<Video[]> => {
    const params = new URLSearchParams();
    if (theme) params.append('theme', theme);
    params.append('limit', limit.toString());

    const response = await api.get(`/videos?${params}`);
    return response.data;
  },
};

// TikTok Sources API
export const tikTokSourcesApi = {
  getAll: async (theme?: string, activeOnly = true): Promise<TikTokSource[]> => {
    const params = new URLSearchParams();
    if (theme) params.append('theme', theme);
    params.append('active_only', activeOnly.toString());

    const response = await api.get(`/tiktok-sources?${params}`);
    return response.data;
  },

  create: async (source: TikTokSourceCreate): Promise<TikTokSource> => {
    const response = await api.post('/tiktok-sources', source);
    return response.data;
  },

  update: async (id: number, source: Partial<TikTokSourceCreate>): Promise<TikTokSource> => {
    const response = await api.put(`/tiktok-sources/${id}`, source);
    return response.data;
  },

  delete: async (id: number): Promise<{ message: string }> => {
    const response = await api.delete(`/tiktok-sources/${id}`);
    return response.data;
  },

  getThemes: async (): Promise<{ themes: string[] }> => {
    const response = await api.get('/tiktok-sources/themes');
    return response.data;
  },

  getByTheme: async (theme: string): Promise<TikTokSource[]> => {
    const response = await api.get(`/tiktok-sources/by-theme/${theme}`);
    return response.data;
  },
};

// Tasks API
export const tasksApi = {
  getAll: async (status?: string, limit = 50): Promise<TaskLog[]> => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());

    const response = await api.get(`/tasks?${params}`);
    return response.data;
  },

  fetchVideos: async (request: FetchRequest): Promise<{ success: boolean; task_id: string; message: string; videos_count: number }> => {
    const response = await api.post('/tasks/fetch', request);
    return response.data;
  },

  uploadVideos: async (request: UploadRequest): Promise<{ success: boolean; task_id: string; celery_task_id: string; message: string; total_videos: number; account: string }> => {
    const response = await api.post('/tasks/upload', request);
    return response.data;
  },

  getProgress: async (taskId: string): Promise<TaskProgress> => {
    const response = await api.get(`/tasks/${taskId}/progress`);
    return response.data;
  },

  cancelTask: async (taskId: string): Promise<{ message: string }> => {
    const response = await api.post(`/tasks/${taskId}/cancel`);
    return response.data;
  },
};

// Stats API
export const statsApi = {
  get: async (): Promise<Stats> => {
    const response = await api.get('/stats');
    return response.data;
  },
};

export default api;