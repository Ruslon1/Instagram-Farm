import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, ExternalLink, Filter, Download } from 'lucide-react';
import toast from 'react-hot-toast';
import { videosApi, tasksApi } from '../services/api';
import type { FetchRequest } from '../types';

const Videos = () => {
  const [selectedTheme, setSelectedTheme] = useState<string>('');
  const [showFetchForm, setShowFetchForm] = useState(false);
  const [fetchData, setFetchData] = useState<FetchRequest>({
    theme: '',
    source_usernames: [''],
    videos_per_account: 10,
  });

  const queryClient = useQueryClient();

  const { data: videos, isLoading, error } = useQuery({
    queryKey: ['videos', selectedTheme],
    queryFn: () => videosApi.getAll(selectedTheme || undefined),
  });

  const fetchMutation = useMutation({
    mutationFn: tasksApi.fetchVideos,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      toast.success(`${data.message} (${data.videos_count} videos)`);
      setShowFetchForm(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to fetch videos');
    },
  });

  const handleFetchSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const validSources = fetchData.source_usernames.filter(username => username.trim());
    if (!fetchData.theme || validSources.length === 0) {
      toast.error('Please provide theme and at least one TikTok username');
      return;
    }

    fetchMutation.mutate({
      ...fetchData,
      source_usernames: validSources,
    });
  };

  const addSourceInput = () => {
    setFetchData({
      ...fetchData,
      source_usernames: [...fetchData.source_usernames, ''],
    });
  };

  const updateSourceInput = (index: number, value: string) => {
    const newSources = [...fetchData.source_usernames];
    newSources[index] = value;
    setFetchData({
      ...fetchData,
      source_usernames: newSources,
    });
  };

  const removeSourceInput = (index: number) => {
    if (fetchData.source_usernames.length > 1) {
      const newSources = fetchData.source_usernames.filter((_, i) => i !== index);
      setFetchData({
        ...fetchData,
        source_usernames: newSources,
      });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'downloaded':
        return 'bg-blue-100 text-blue-800';
      case 'uploaded':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const themes = [...new Set(videos?.map(video => video.theme) || [])];

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
        <p className="text-red-800">Failed to load videos</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Videos</h1>
          <p className="text-gray-600">Manage TikTok videos for Instagram posting</p>
        </div>
        <button
          onClick={() => setShowFetchForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
        >
          <Download className="w-4 h-4 mr-2" />
          Fetch Videos
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <Filter className="w-5 h-5 text-gray-400" />
          <select
            value={selectedTheme}
            onChange={(e) => setSelectedTheme(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Themes</option>
            {themes.map(theme => (
              <option key={theme} value={theme}>{theme}</option>
            ))}
          </select>
          <span className="text-sm text-gray-500">
            Showing {videos?.length || 0} videos
          </span>
        </div>
      </div>

      {/* Videos Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {videos?.map((video, index) => (
          <div key={`${video.link}-${index}`} className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                  {video.theme}
                </span>
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(video.status)}`}>
                  {video.status}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center text-gray-600">
                  <Play className="w-4 h-4 mr-2" />
                  <span className="text-sm">TikTok Video</span>
                </div>
                <a
                  href={video.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>

              {video.created_at && (
                <p className="text-xs text-gray-500 mt-2">
                  Added: {new Date(video.created_at).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {videos?.length === 0 && (
        <div className="text-center py-12">
          <Play className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No videos found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {selectedTheme ? `No videos found for theme "${selectedTheme}"` : 'Start by fetching videos from TikTok sources.'}
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowFetchForm(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Fetch Videos
            </button>
          </div>
        </div>
      )}

      {/* Fetch Videos Modal */}
      {showFetchForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-screen overflow-y-auto">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Fetch Videos from TikTok</h2>

            <form onSubmit={handleFetchSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Theme *
                </label>
                <input
                  type="text"
                  value={fetchData.theme}
                  onChange={(e) => setFetchData({ ...fetchData, theme: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., ishowspeed, gaming"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  TikTok Usernames *
                </label>
                {fetchData.source_usernames.map((username, index) => (
                  <div key={index} className="flex items-center space-x-2 mb-2">
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => updateSourceInput(index, e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="TikTok username (without @)"
                    />
                    {fetchData.source_usernames.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeSourceInput(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addSourceInput}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  + Add another username
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Videos per Account
                </label>
                <input
                  type="number"
                  value={fetchData.videos_per_account}
                  onChange={(e) => setFetchData({ ...fetchData, videos_per_account: parseInt(e.target.value) || 10 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="50"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowFetchForm(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={fetchMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {fetchMutation.isPending ? 'Fetching...' : 'Fetch Videos'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Videos;