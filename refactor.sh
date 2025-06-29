#!/bin/bash

VM_IP="94.131.86.226"

echo "🔧 Fixing Frontend API URL for VM IP: $VM_IP"

# Update frontend API configuration for VM
cat > frontend/src/services/api.ts << EOF
import axios from 'axios';
import type { Account, AccountCreate, Video, TaskLog, Stats, FetchRequest, UploadRequest, TikTokSource, TikTokSourceCreate, TaskProgress, ProxySettings, ProxyTestResult } from '../types';

const api = axios.create({
  baseURL: 'http://$VM_IP:8000/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(\`🔄 API Request: \${config.method?.toUpperCase()} \${config.url}\`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log(\`✅ API Response: \${response.status} \${response.config.url}\`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.status, error.message);
    console.error('URL:', error.config?.url);
    console.error('Response:', error.response?.data);
    return Promise.reject(error);
  }
);

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

  updateProxy: async (username: string, proxySettings: ProxySettings): Promise<{ message: string }> => {
    const response = await api.put(\`/accounts/\${username}/proxy\`, proxySettings);
    return response.data;
  },

  removeProxy: async (username: string): Promise<{ message: string }> => {
    const response = await api.delete(\`/accounts/\${username}/proxy\`);
    return response.data;
  },

  testProxy: async (username: string): Promise<ProxyTestResult> => {
    const response = await api.post(\`/accounts/\${username}/proxy/test\`);
    return response.data;
  },

  getProxy: async (username: string): Promise<any> => {
    const response = await api.get(\`/accounts/\${username}/proxy\`);
    return response.data;
  },
};

// Videos API
export const videosApi = {
  getAll: async (theme?: string, limit = 100): Promise<Video[]> => {
    const params = new URLSearchParams();
    if (theme) params.append('theme', theme);
    params.append('limit', limit.toString());

    const response = await api.get(\`/videos?\${params}\`);
    return response.data;
  },

  delete: async (videoLink: string): Promise<{ message: string }> => {
    const response = await api.delete(\`/videos/\${encodeURIComponent(videoLink)}\`);
    return response.data;
  },

  bulkDelete: async (videoLinks: string[]): Promise<any> => {
    const response = await api.post('/videos/bulk-delete', videoLinks);
    return response.data;
  },

  deleteByTheme: async (theme: string, status?: string): Promise<any> => {
    const params = status ? \`?status=\${status}\` : '';
    const response = await api.delete(\`/videos/by-theme/\${theme}\${params}\`);
    return response.data;
  },

  deleteByStatus: async (status: string): Promise<any> => {
    const response = await api.delete(\`/videos/by-status/\${status}\`);
    return response.data;
  },

  updateStatus: async (videoLink: string, newStatus: string): Promise<any> => {
    const response = await api.patch(\`/videos/\${encodeURIComponent(videoLink)}/status?new_status=\${newStatus}\`);
    return response.data;
  },

  getStats: async (): Promise<any> => {
    const response = await api.get('/videos/stats');
    return response.data;
  },
};

// TikTok Sources API
export const tikTokSourcesApi = {
  getAll: async (theme?: string, activeOnly = true): Promise<TikTokSource[]> => {
    const params = new URLSearchParams();
    if (theme) params.append('theme', theme);
    params.append('active_only', activeOnly.toString());

    const response = await api.get(\`/tiktok-sources?\${params}\`);
    return response.data;
  },

  create: async (source: TikTokSourceCreate): Promise<TikTokSource> => {
    const response = await api.post('/tiktok-sources', source);
    return response.data;
  },

  update: async (id: number, source: Partial<TikTokSourceCreate>): Promise<TikTokSource> => {
    const response = await api.put(\`/tiktok-sources/\${id}\`, source);
    return response.data;
  },

  delete: async (id: number): Promise<{ message: string }> => {
    const response = await api.delete(\`/tiktok-sources/\${id}\`);
    return response.data;
  },

  getThemes: async (): Promise<{ themes: string[] }> => {
    const response = await api.get('/tiktok-sources/themes');
    return response.data;
  },

  getByTheme: async (theme: string): Promise<TikTokSource[]> => {
    const response = await api.get(\`/tiktok-sources/by-theme/\${theme}\`);
    return response.data;
  },
};

// Tasks API
export const tasksApi = {
  getAll: async (status?: string, limit = 50): Promise<TaskLog[]> => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());

    const response = await api.get(\`/tasks?\${params}\`);
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
    const response = await api.get(\`/tasks/\${taskId}/progress\`);
    return response.data;
  },

  cancelTask: async (taskId: string): Promise<{ message: string }> => {
    const response = await api.post(\`/tasks/\${taskId}/cancel\`);
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

// Proxy monitoring API
export const proxyApi = {
  getMetrics: async (): Promise<any> => {
    const response = await api.get('/proxy/metrics');
    return response.data;
  },

  getUptimeStats: async (): Promise<any> => {
    const response = await api.get('/proxy/uptime');
    return response.data;
  },

  getPerformanceTrends: async (days: number): Promise<any> => {
    const response = await api.get(\`/proxy/performance-trends?days=\${days}\`);
    return response.data;
  },

  getAccountsStatus: async (): Promise<any> => {
    const response = await api.get('/proxy/accounts-status');
    return response.data;
  },

  runManualCheck: async (): Promise<any> => {
    const response = await api.post('/proxy/manual-check');
    return response.data;
  },

  startScheduler: async (): Promise<any> => {
    const response = await api.post('/proxy/scheduler/start');
    return response.data;
  },

  stopScheduler: async (): Promise<any> => {
    const response = await api.post('/proxy/scheduler/stop');
    return response.data;
  },

  getSchedulerStatus: async (): Promise<any> => {
    const response = await api.get('/proxy/scheduler/status');
    return response.data;
  },
};

export default api;
EOF

echo "✅ Updated frontend API URL to http://$VM_IP:8000/api"

# Update docker-compose.yml to use VM IP
echo "🔧 Updating docker-compose.yml..."
sed -i "s/VM_EXTERNAL_IP:-localhost/VM_EXTERNAL_IP:-$VM_IP/g" docker-compose.yml

# Update CORS settings in .env
echo "🌐 Updating CORS settings..."
if grep -q "ALLOWED_ORIGINS" .env; then
    sed -i "s|ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=http://$VM_IP:3000,http://localhost:3000|g" .env
else
    echo "ALLOWED_ORIGINS=http://$VM_IP:3000,http://localhost:3000" >> .env
fi

echo "🔨 Rebuilding frontend container..."
docker-compose up -d --build frontend

echo "⏳ Waiting for frontend to restart..."
sleep 10

echo ""
echo "🎯 Testing connectivity:"
echo "Backend health: \$(curl -s -o /dev/null -w "%{http_code}" http://$VM_IP:8000/health)"
echo "Frontend: \$(curl -s -o /dev/null -w "%{http_code}" http://$VM_IP:3000)"

echo ""
echo "✅ Configuration updated!"
echo "🌐 Frontend: http://$VM_IP:3000"
echo "🔧 Backend: http://$VM_IP:8000"
echo "📚 API Docs: http://$VM_IP:8000/docs"