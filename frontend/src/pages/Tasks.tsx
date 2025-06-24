import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, Activity, RefreshCw, Filter, StopCircle, Clock, CheckCircle, XCircle, Timer, User } from 'lucide-react';
import toast from 'react-hot-toast';
import { tasksApi, accountsApi, videosApi } from '../services/api';
import type { UploadRequest, TaskLog } from '../types';

interface TaskProgressCardProps {
  task: TaskLog;
}

const TaskProgressCard = ({ task }: TaskProgressCardProps) => {
  const queryClient = useQueryClient();

  // Poll for progress updates if task is running
  const { data: progress } = useQuery({
    queryKey: ['task-progress', task.id],
    queryFn: () => tasksApi.getProgress(task.id),
    refetchInterval: task.status === 'running' ? 2000 : false,
    enabled: task.status === 'running',
  });

  // Cancel task mutation
  const cancelMutation = useMutation({
    mutationFn: () => tasksApi.cancelTask(task.id),
    onSuccess: () => {
      queryClient.setQueryData(['task-progress', task.id], (oldData: any) => ({
        ...oldData,
        status: 'cancelled',
        message: 'Task cancelled by user request',
        current_item: 'Cancellation requested...',
        next_action_at: null,
        cooldown_seconds: null
      }));

      queryClient.setQueryData(['tasks'], (oldTasks: any[]) =>
        oldTasks?.map(t =>
          t.id === task.id
            ? { ...t, status: 'cancelled', message: 'Task cancelled by user request' }
            : t
        ) || []
      );

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

      {displayData.status === 'success' && (
        <div className="mb-3 text-sm text-green-700 bg-green-50 p-2 rounded flex items-center space-x-2">
          <CheckCircle className="w-4 h-4" />
          <span>Task completed successfully</span>
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

const Tasks = () => {
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [uploadData, setUploadData] = useState<UploadRequest>({
    account_username: '',
    video_links: [],
  });

  const queryClient = useQueryClient();

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks', statusFilter],
    queryFn: () => tasksApi.getAll(statusFilter || undefined),
    refetchInterval: 5000,
  });

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.getAll,
  });

  const { data: videos } = useQuery({
    queryKey: ['videos'],
    queryFn: () => videosApi.getAll(),
  });

  const uploadMutation = useMutation({
    mutationFn: tasksApi.uploadVideos,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      toast.success(`Upload started for ${data.total_videos} videos on @${data.account}`);
      setShowUploadForm(false);
      setUploadData({ account_username: '', video_links: [] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start upload');
    },
  });

  const cancelAllMutation = useMutation({
    mutationFn: async () => {
      const runningTasks = tasks?.filter(task => task.status === 'running') || [];
      const cancelPromises = runningTasks.map(task => tasksApi.cancelTask(task.id));
      return Promise.all(cancelPromises);
    },
    onSuccess: (results) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      toast.success(`Cancelled ${results.length} running tasks`);
    },
    onError: (error: any) => {
      toast.error('Failed to cancel some tasks: ' + error);
    },
  });

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!uploadData.account_username) {
      toast.error('Please select an account');
      return;
    }

    if (uploadData.video_links.length === 0) {
      toast.error('Please select at least one video');
      return;
    }

    uploadMutation.mutate(uploadData);
  };

  const refreshTasks = () => {
    queryClient.invalidateQueries({ queryKey: ['tasks'] });
    toast.success('Tasks refreshed');
  };

  const handleCancelAll = () => {
    const runningCount = tasks?.filter(task => task.status === 'running').length || 0;
    if (runningCount === 0) {
      toast.error('No running tasks to cancel');
      return;
    }

    if (confirm(`Are you sure you want to cancel all ${runningCount} running tasks? This cannot be undone.`)) {
      cancelAllMutation.mutate();
    }
  };

  // Get pending videos for selected account theme
  const selectedAccount = accounts?.find(acc => acc.username === uploadData.account_username);
  const pendingVideos = videos?.filter(video =>
    video.status === 'pending' &&
    (!selectedAccount || video.theme === selectedAccount.theme)
  ) || [];

  const runningTasks = tasks?.filter(task => task.status === 'running') || [];
  const completedTasks = tasks?.filter(task => ['success', 'failed', 'cancelled'].includes(task.status)) || [];

  if (tasksLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-pink-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
          <p className="text-gray-600">Monitor and manage bot operations</p>
        </div>
        <div className="flex space-x-3">
          {runningTasks.length > 0 && (
            <button
              onClick={handleCancelAll}
              disabled={cancelAllMutation.isPending}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 flex items-center disabled:opacity-50"
            >
              <StopCircle className="w-4 h-4 mr-2" />
              Cancel All ({runningTasks.length})
            </button>
          )}
          <button
            onClick={refreshTasks}
            className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={() => setShowUploadForm(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Videos
          </button>
        </div>
      </div>

      {/* Status Filter */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <Filter className="w-5 h-5 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="running">Running</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <span className="text-sm text-gray-500">
            {tasks?.length || 0} tasks • {runningTasks.length} running
          </span>
          {runningTasks.length > 0 && (
            <span className="text-sm text-blue-600 animate-pulse">
              • Live updates every 5s
            </span>
          )}
        </div>
      </div>

      {/* Running Tasks */}
      {runningTasks.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Activity className="w-5 h-5 mr-2 text-blue-600" />
              Active Tasks ({runningTasks.length})
            </h2>
            <div className="text-sm text-gray-600 bg-blue-50 px-3 py-1 rounded-full">
              🔴 Live monitoring active
            </div>
          </div>
          <div className="space-y-3">
            {runningTasks.map((task) => (
              <TaskProgressCard key={task.id} task={task} />
            ))}
          </div>
        </div>
      )}

      {/* Completed Tasks */}
      {completedTasks.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Recent Tasks ({completedTasks.length})
          </h2>
          <div className="space-y-3">
            {completedTasks.slice(0, 10).map((task) => (
              <TaskProgressCard key={task.id} task={task} />
            ))}
          </div>
        </div>
      )}

      {/* No Tasks */}
      {tasks?.length === 0 && (
        <div className="text-center py-12">
          <Activity className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No tasks yet</h3>
          <p className="mt-1 text-sm text-gray-500">Start by fetching videos or uploading content.</p>
        </div>
      )}

      {/* Upload Videos Modal */}
      {showUploadForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-screen overflow-y-auto">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Videos to Instagram</h2>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Instagram Account *
                </label>
                <select
                  value={uploadData.account_username}
                  onChange={(e) => {
                    setUploadData({
                      ...uploadData,
                      account_username: e.target.value,
                      video_links: []
                    });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                >
                  <option value="">Select Instagram account...</option>
                  {accounts?.filter(acc => acc.status === 'active').map(account => (
                    <option key={account.username} value={account.username}>
                      @{account.username} ({account.theme} theme)
                    </option>
                  ))}
                </select>
              </div>

              {uploadData.account_username && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Videos to Upload *
                  </label>
                  {pendingVideos.length > 0 ? (
                    <div className="max-h-60 overflow-y-auto border border-gray-300 rounded-md">
                      {pendingVideos.map((video, index) => (
                        <label key={`${video.link}-${index}`} className="flex items-center p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0">
                          <input
                            type="checkbox"
                            checked={uploadData.video_links.includes(video.link)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setUploadData({
                                  ...uploadData,
                                  video_links: [...uploadData.video_links, video.link]
                                });
                              } else {
                                setUploadData({
                                  ...uploadData,
                                  video_links: uploadData.video_links.filter(link => link !== video.link)
                                });
                              }
                            }}
                            className="mr-3 rounded border-gray-300 text-green-600 focus:ring-green-500"
                          />
                          <div className="flex-1">
                            <p className="text-sm text-gray-900">TikTok Video #{index + 1}</p>
                            <p className="text-xs text-gray-500 truncate" title={video.link}>
                              {video.link.length > 50 ? `${video.link.substring(0, 50)}...` : video.link}
                            </p>
                            <div className="flex items-center space-x-2 mt-1">
                              <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">
                                {video.theme}
                              </span>
                              <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                                {video.status}
                              </span>
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 text-center text-gray-500 border border-gray-300 rounded-md">
                      <p>No pending videos available</p>
                      {selectedAccount && (
                        <p className="text-xs mt-1">
                          Account theme: {selectedAccount.theme}
                        </p>
                      )}
                      <p className="text-xs mt-1">
                        Go to Videos page to fetch new content
                      </p>
                    </div>
                  )}

                  {pendingVideos.length > 0 && (
                    <div className="mt-2 flex justify-between text-xs text-gray-500">
                      <span>{uploadData.video_links.length} of {pendingVideos.length} selected</span>
                      <button
                        type="button"
                        onClick={() => {
                          if (uploadData.video_links.length === pendingVideos.length) {
                            setUploadData({ ...uploadData, video_links: [] });
                          } else {
                            setUploadData({
                              ...uploadData,
                              video_links: pendingVideos.map(v => v.link)
                            });
                          }
                        }}
                        className="text-green-600 hover:text-green-800 underline"
                      >
                        {uploadData.video_links.length === pendingVideos.length ? 'Deselect All' : 'Select All'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {uploadData.video_links.length > 0 && (
                <div className="bg-blue-50 p-3 rounded-md">
                  <p className="text-sm text-blue-800">
                    <strong>📋 Upload Process:</strong>
                  </p>
                  <ul className="text-xs text-blue-700 mt-1 space-y-1">
                    <li>• Videos will be downloaded and uploaded one by one</li>
                    <li>• Random cooldowns (5-25 minutes) between uploads for safety</li>
                    <li>• You can monitor progress and cancel at any time</li>
                    <li>• Notifications will be sent to Telegram</li>
                  </ul>
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowUploadForm(false);
                    setUploadData({ account_username: '', video_links: [] });
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploadMutation.isPending || uploadData.video_links.length === 0}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center"
                >
                  {uploadMutation.isPending ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Starting...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload {uploadData.video_links.length} Videos
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tasks;