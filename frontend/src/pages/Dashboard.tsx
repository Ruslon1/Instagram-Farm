import { useQuery } from '@tanstack/react-query';
import {
  Users,
  Video,
  TrendingUp,
  Activity,
  Play,
  Upload,
} from 'lucide-react';
import { statsApi } from '../services/api';
import StatsCard from '../components/StatsCard';
import ActionButton from '../components/ActionButton';

const Dashboard = () => {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['stats'],
    queryFn: statsApi.get,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-pink-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">Failed to load dashboard stats</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Monitor and control your Instagram bot</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Active Accounts"
          value={stats?.active_accounts || 0}
          icon={Users}
          color="blue"
        />
        <StatsCard
          title="Pending Videos"
          value={stats?.pending_videos || 0}
          icon={Video}
          color="purple"
        />
        <StatsCard
          title="Posts Today"
          value={stats?.posts_today || 0}
          icon={TrendingUp}
          color="green"
        />
        <StatsCard
          title="Running Tasks"
          value={stats?.running_tasks || 0}
          icon={Activity}
          color="orange"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ActionButton
            title="Fetch Videos"
            description="Download new videos from TikTok sources"
            icon={Play}
            color="blue"
            href="/videos"
          />
          <ActionButton
            title="Upload Videos"
            description="Start uploading pending videos to Instagram"
            icon={Upload}
            color="green"
            href="/tasks"
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;