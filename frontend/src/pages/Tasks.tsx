import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, Activity, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { tasksApi, accountsApi, videosApi } from '../services/api';
import type { UploadRequest } from '../types';

const Tasks = () => {
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadData, setUploadData] = useState<UploadRequest>({
    account_username: '',
    video_links: [],
  });

  const queryClient = useQueryClient();

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.getAll(),
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
      toast.success(data.message);
      setShowUploadForm(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start upload');
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Activity className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-600" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTaskTypeColor = (taskType: string) => {
    switch (taskType) {
      case 'fetch':
        return 'bg-purple-100 text-purple-800';
      case 'upload':
        return 'bg-green-100 text-green-800';
      case 'download':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Get pending videos for selected account
  const selectedAccount = accounts?.find(acc => acc.username === uploadData.account_username);
  const pendingVideos = videos?.filter(video =>
    video.status === 'pending' &&
    (!selectedAccount || video.theme === selectedAccount.theme)
  ) || [];

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
          <p className="text-gray-600">Monitor and manage bot tasks</p>
        </div>
        <button
          onClick={() => setShowUploadForm(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center"
        >
          <Upload className="w-4 h-4 mr-2" />
          Upload Videos
        </button>
      </div>

      {/* Tasks List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Tasks</h2>
        </div>

        <div className="divide-y divide-gray-200">
          {tasks?.map((task) => (
            <div key={task.id} className="px-6 py-4 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(task.status)}
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getTaskTypeColor(task.task_type)}`}>
                        {task.task_type}
                      </span>
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(task.status)}`}>
                        {task.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-900 mt-1">
                      {task.message || `${task.task_type} task`}
                    </p>
                    {task.account_username && (
                      <p className="text-xs text-gray-500">
                        Account: @{task.account_username}
                      </p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">
                    {new Date(task.created_at).toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-400">
                    ID: {task.id.slice(0, 8)}...
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {tasks?.length === 0 && (
          <div className="text-center py-12">
            <Activity className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No tasks yet</h3>
            <p className="mt-1 text-sm text-gray-500">Start by fetching videos or uploading content.</p>
          </div>
        )}
      </div>

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
                            <p className="text-sm text-gray-900">TikTok Video</p>
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