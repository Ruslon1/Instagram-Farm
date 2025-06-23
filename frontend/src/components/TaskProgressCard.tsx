import { useQuery } from '@tanstack/react-query';
import { Clock, CheckCircle, XCircle, Activity, Timer, User } from 'lucide-react';
import { tasksApi } from '../services/api';
import type { TaskLog } from '../types';

interface TaskProgressCardProps {
  task: TaskLog;
}

const TaskProgressCard = ({ task }: TaskProgressCardProps) => {
  // Poll for progress updates if task is running
  const { data: progress } = useQuery({
    queryKey: ['task-progress', task.id],
    queryFn: () => tasksApi.getProgress(task.id),
    refetchInterval: task.status === 'running' ? 2000 : false, // Poll every 2 seconds
    enabled: task.status === 'running',
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Activity className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-gray-600" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-50 border-blue-200';
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'failed':
        return 'bg-red-50 border-red-200';
      case 'cancelled':
        return 'bg-gray-50 border-gray-200';
      default:
        return 'bg-yellow-50 border-yellow-200';
    }
  };

  const formatCooldown = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const displayData = progress || task;
  const progressPercent = displayData.progress || 0;
  const totalItems = displayData.total_items || 0;
  const currentProgress = Math.round((progressPercent / 100) * totalItems);

  return (
    <div className={`border rounded-lg p-4 ${getStatusColor(displayData.status)}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          {getStatusIcon(displayData.status)}
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-medium text-gray-900 capitalize">
                {task.task_type}
              </span>
              {task.account_username && (
                <div className="flex items-center space-x-1 text-sm text-gray-600">
                  <User className="w-3 h-3" />
                  <span>@{task.account_username}</span>
                </div>
              )}
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {displayData.message || `${task.task_type} task`}
            </p>
          </div>
        </div>

        <span className="text-xs text-gray-500">
          {new Date(displayData.created_at).toLocaleTimeString()}
        </span>
      </div>

      {/* Progress Bar */}
      {totalItems > 0 && (
        <div className="mb-3">
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-gray-600">
              Progress: {currentProgress}/{totalItems}
            </span>
            <span className="text-sm font-medium text-gray-900">
              {progressPercent}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                displayData.status === 'success' 
                  ? 'bg-green-500' 
                  : displayData.status === 'failed'
                  ? 'bg-red-500'
                  : 'bg-blue-500'
              }`}
              style={{ width: `${Math.min(progressPercent, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Current Item */}
      {displayData.current_item && (
        <div className="mb-3 p-2 bg-white bg-opacity-50 rounded text-sm">
          <span className="font-medium text-gray-700">Currently: </span>
          <span className="text-gray-600">{displayData.current_item}</span>
        </div>
      )}

      {/* Cooldown Timer */}
      {displayData.status === 'running' && progress?.remaining_cooldown && progress.remaining_cooldown > 0 && (
        <div className="flex items-center space-x-2 text-sm text-orange-600 bg-orange-50 p-2 rounded">
          <Timer className="w-4 h-4" />
          <span>Next upload in: {formatCooldown(progress.remaining_cooldown)}</span>
        </div>
      )}

      {/* Task ID (for debugging) */}
      <div className="mt-2 pt-2 border-t border-gray-200">
        <span className="text-xs text-gray-400">
          ID: {task.id.slice(0, 8)}...
        </span>
      </div>
    </div>
  );
};

export default TaskProgressCard;