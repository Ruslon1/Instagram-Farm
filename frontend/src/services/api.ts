import axios from 'axios';
import type { Account, AccountCreate, Video, TaskLog, Stats, FetchRequest, UploadRequest } from '../types';

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

  uploadVideos: async (request: UploadRequest): Promise<{ success: boolean; task_id: string; celery_task_id: string; message: string }> => {
    const response = await api.post('/tasks/upload', request);
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