import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, Activity, RefreshCw, Filter, StopCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { tasksApi, accountsApi, videosApi } from '../services/api';
import TaskProgressCard from '../components/TaskProgressCard';
import type { UploadRequest } from '../types';

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
    refetchInterval: 5000, // Refresh every 5 seconds for live updates
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
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start upload');
    },
  });

  // Mass cancel all running tasks
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

  // Get pending videos for selected account
  const selectedAccount = accounts?.find(acc => acc.username === uploadData.account_username);
  const pendingVideos = videos?.filter(video =>
    video.status === 'pending' &&
    (!selectedAccount || video.theme === selectedAccount.theme)
  ) || [];

  // Group tasks by status
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
                  Account *
                </label>
                <select
                  value={uploadData.account_username}
                  onChange={(e) => {
                    setUploadData({
                      ...uploadData,
                      account_username: e.target.value,
                      video_links: [] // Reset video selection when account changes
                    });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                >
                  <option value="">Select account...</option>
                  {accounts?.filter(acc => acc.status === 'active').map(account => (
                    <option key={account.username} value={account.username}>
                      @{account.username} ({account.theme})
                    </option>
                  ))}
                </select>
              </div>

              {uploadData.account_username && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Videos to Upload *
                  </label>
                  <div className="max-h-60 overflow-y-auto border border-gray-300 rounded-md">
                    {pendingVideos.length > 0 ? (
                      pendingVideos.map((video, index) => (
                        <label key={index} className="flex items-center p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0">
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
                            <p className="text-xs text-gray-500">{video.theme}</p>
                          </div>
                        </label>
                      ))
                    ) : (
                      <div className="p-4 text-center text-gray-500">
                        <p>No pending videos available for this account's theme</p>
                        {selectedAccount && (
                          <p className="text-xs mt-1">Theme: {selectedAccount.theme}</p>
                        )}
                      </div>
                    )}
                  </div>
                  {pendingVideos.length > 0 && (
                    <div className="mt-2 flex justify-between text-xs text-gray-500">
                      <span>{uploadData.video_links.length} selected</span>
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
                        className="text-green-600 hover:text-green-800"
                      >
                        {uploadData.video_links.length === pendingVideos.length ? 'Deselect All' : 'Select All'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              <div className="bg-blue-50 p-3 rounded-md">
                <p className="text-sm text-blue-800">
                  <strong>Note:</strong> Videos will be uploaded with random cooldowns (5-25 minutes) between uploads for safety.
                  You can monitor the progress in real-time and cancel at any time.
                </p>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowUploadForm(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploadMutation.isPending || uploadData.video_links.length === 0}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {uploadMutation.isPending ? 'Starting...' : `Upload ${uploadData.video_links.length} Videos`}
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