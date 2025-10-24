import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Clock, CheckCircle, XCircle, Activity, Timer, User, StopCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { tasksApi } from '../services/api';
import type { TaskLog } from '../types';

interface TaskProgressCardProps {
  task: TaskLog;
}

const TaskProgressCard = ({ task }: TaskProgressCardProps) => {
  const queryClient = useQueryClient();

  // Poll for progress updates if task is running
  const { data: progress } = useQuery({
    queryKey: ['task-progress', task.id],
    queryFn: () => tasksApi.getProgress(task.id),
    refetchInterval: task.status === 'running' ? 2000 : false, // Poll every 2 seconds
    enabled: task.status === 'running',
  });

  // Cancel task mutation
  const cancelMutation = useMutation({
    mutationFn: () => tasksApi.cancelTask(task.id),
    onSuccess: () => {
      // Immediately update the local cache to show cancelled status
      queryClient.setQueryData(['task-progress', task.id], (oldData: any) => ({
        ...oldData,
        status: 'cancelled',
        message: 'Task cancelled by user request',
        current_item: 'Cancellation requested...',
        next_action_at: null,
        cooldown_seconds: null
      }));

      // Also update the tasks list
      queryClient.setQueryData(['tasks'], (oldTasks: any[]) =>
        oldTasks?.map(t =>
          t.id === task.id
            ? { ...t, status: 'cancelled', message: 'Task cancelled by user request' }
            : t
        ) || []
      );

      // Invalidate queries to refresh from server
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['task-progress', task.id] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });

      toast.success('Task cancellation requested - it will stop at the next checkpoint');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to cancel task');
    },
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
        return <StopCircle className="w-5 h-5 text-gray-600" />;
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

  const handleCancelTask = () => {
    if (confirm('Are you sure you want to cancel this task? This action cannot be undone.')) {
      cancelMutation.mutate();
    }
  };

  // Use progress data if available, otherwise fall back to task data
  const displayData = progress || task;
  const progressPercent = displayData.progress || 0;
  const totalItems = displayData.total_items || 0;
  const currentProgress = totalItems > 0 ? Math.round((progressPercent / 100) * totalItems) : 0;

  return (
    <div className={`border rounded-lg p-4 ${getStatusColor(displayData.status)}`}>
      {/* Header with status and controls */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3 flex-1">
          {getStatusIcon(displayData.status)}
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
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
            <p className="text-sm text-gray-600">
              {displayData.message || `${task.task_type} task`}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 ml-3">
          <span className="text-xs text-gray-500 whitespace-nowrap">
            {new Date(displayData.created_at).toLocaleTimeString()}
          </span>

          {/* Cancel button for running tasks */}
          {displayData.status === 'running' && (
            <button
              onClick={handleCancelTask}
              disabled={cancelMutation.isPending}
              className="p-1 text-red-600 hover:bg-red-100 rounded transition-colors disabled:opacity-50 flex-shrink-0"
              title="Cancel task"
            >
              <StopCircle className="w-4 h-4" />
            </button>
          )}
        </div>
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
                  : displayData.status === 'cancelled'
                  ? 'bg-gray-500'
                  : 'bg-blue-500'
              }`}
              style={{ width: `${Math.min(progressPercent, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Current Item */}
      {displayData.current_item && displayData.status === 'running' && (
        <div className="mb-3 p-2 bg-white bg-opacity-50 rounded text-sm">
          <span className="font-medium text-gray-700">Currently: </span>
          <span className="text-gray-600">{displayData.current_item}</span>
        </div>
      )}

      {/* Cooldown Timer */}
      {displayData.status === 'running' && progress?.remaining_cooldown && progress.remaining_cooldown > 0 && (
        <div className="mb-3 p-2 bg-orange-50 border border-orange-200 rounded">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-sm text-orange-700">
              <Timer className="w-4 h-4" />
              <span>Next upload in: {formatCooldown(progress.remaining_cooldown)}</span>
            </div>
            <button
              onClick={handleCancelTask}
              disabled={cancelMutation.isPending}
              className="text-xs text-red-600 hover:text-red-800 underline disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Status Messages */}
      {displayData.status === 'cancelled' && (
        <div className="mb-3 text-sm text-gray-600 bg-gray-100 p-2 rounded flex items-center space-x-2">
          <StopCircle className="w-4 h-4" />
          <span>Task cancelled - stopping at next checkpoint</span>
        </div>
      )}

      {displayData.status === 'failed' && displayData.message && (
        <div className="mb-3 text-sm text-red-700 bg-red-50 p-2 rounded flex items-center space-x-2">
          <XCircle className="w-4 h-4" />
          <span className="flex-1">{displayData.message}</span>
        </div>
      )}

      {displayData.status === 'success' && totalItems > 0 && (
        <div className="mb-3 text-sm text-green-700 bg-green-50 p-2 rounded flex items-center space-x-2">
          <CheckCircle className="w-4 h-4" />
          <span>Completed {totalItems} items successfully</span>
        </div>
      )}

      {/* Cancellation in progress indicator */}
      {cancelMutation.isPending && (
        <div className="mb-3 text-sm text-orange-700 bg-orange-50 p-2 rounded flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
          <span>Sending cancellation request...</span>
        </div>
      )}

      {/* Task ID */}
      <div className="pt-2 border-t border-gray-200">
        <span className="text-xs text-gray-400">
          Task ID: {task.id.slice(0, 8)}...
        </span>
        {cancelMutation.isPending && (
          <span className="ml-2 text-xs text-orange-600">
            Cancelling...
          </span>
        )}
      </div>
    </div>
  );
};

export default TaskProgressCard;