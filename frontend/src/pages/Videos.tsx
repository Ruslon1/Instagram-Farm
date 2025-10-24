import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, ExternalLink, Filter, Download, Trash2, CheckSquare, Square, TrendingUp } from 'lucide-react';
import toast from 'react-hot-toast';
import { videosApi, tasksApi, tikTokSourcesApi } from '../services/api';
import type { FetchRequest } from '../types';

const Videos = () => {
  const [selectedTheme, setSelectedTheme] = useState<string>('');
  const [showFetchForm, setShowFetchForm] = useState(false);
  const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set());
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [fetchData, setFetchData] = useState<FetchRequest>({
    theme: '',
    source_usernames: [],
    videos_per_account: 10,
  });

  const queryClient = useQueryClient();

  const { data: videos, isLoading, error } = useQuery({
    queryKey: ['videos', selectedTheme],
    queryFn: () => videosApi.getAll(selectedTheme || undefined),
  });

  const { data: themesData } = useQuery({
    queryKey: ['themes'],
    queryFn: tikTokSourcesApi.getThemes,
  });

  const { data: videoStats } = useQuery({
    queryKey: ['video-stats'],
    queryFn: videosApi.getStats,
  });

  // Get TikTok sources for selected theme
  const { data: availableSources } = useQuery({
    queryKey: ['tiktok-sources-by-theme', fetchData.theme],
    queryFn: () => fetchData.theme ? tikTokSourcesApi.getByTheme(fetchData.theme) : Promise.resolve([]),
    enabled: !!fetchData.theme,
  });

  const fetchMutation = useMutation({
    mutationFn: tasksApi.fetchVideos,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      queryClient.invalidateQueries({ queryKey: ['video-stats'] });
      toast.success(`${data.message} (${data.videos_count} videos)`);
      setShowFetchForm(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to fetch videos');
    },
  });

  // Delete mutations
  const deleteMutation = useMutation({
    mutationFn: videosApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['video-stats'] });
      toast.success('Video deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete video');
    },
  });

  const bulkDeleteMutation = useMutation({
    mutationFn: videosApi.bulkDelete,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['video-stats'] });
      toast.success(`Deleted ${data.deleted_count} videos`);
      setSelectedVideos(new Set());
      setShowBulkActions(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete videos');
    },
  });

  const deleteByThemeMutation = useMutation({
    mutationFn: ({ theme, status }: { theme: string; status?: string }) => videosApi.deleteByTheme(theme, status),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['video-stats'] });
      toast.success(data.message);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete videos');
    },
  });

  const deleteByStatusMutation = useMutation({
    mutationFn: videosApi.deleteByStatus,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['video-stats'] });
      toast.success(data.message);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete videos');
    },
  });

  const handleFetchSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!fetchData.theme || fetchData.source_usernames.length === 0) {
      toast.error('Please select theme and at least one TikTok source');
      return;
    }

    fetchMutation.mutate(fetchData);
  };

  const handleThemeChange = (theme: string) => {
    setFetchData({
      ...fetchData,
      theme,
      source_usernames: [], // Reset selected sources when theme changes
    });
  };

  const handleSourceToggle = (username: string, checked: boolean) => {
    if (checked) {
      setFetchData({
        ...fetchData,
        source_usernames: [...fetchData.source_usernames, username],
      });
    } else {
      setFetchData({
        ...fetchData,
        source_usernames: fetchData.source_usernames.filter(u => u !== username),
      });
    }
  };

  const handleVideoSelect = (videoLink: string, checked: boolean) => {
    const newSelected = new Set(selectedVideos);
    if (checked) {
      newSelected.add(videoLink);
    } else {
      newSelected.delete(videoLink);
    }
    setSelectedVideos(newSelected);
    setShowBulkActions(newSelected.size > 0);
  };

  const handleSelectAll = () => {
    if (selectedVideos.size === videos?.length) {
      setSelectedVideos(new Set());
      setShowBulkActions(false);
    } else {
      setSelectedVideos(new Set(videos?.map(v => v.link) || []));
      setShowBulkActions(true);
    }
  };

  const handleDeleteVideo = (videoLink: string) => {
    if (confirm('Are you sure you want to delete this video?')) {
      deleteMutation.mutate(videoLink);
    }
  };

  const handleBulkDelete = () => {
    if (confirm(`Are you sure you want to delete ${selectedVideos.size} selected videos?`)) {
      bulkDeleteMutation.mutate(Array.from(selectedVideos));
    }
  };

  const handleDeleteByTheme = (theme: string, status?: string) => {
    const confirmMessage = status
      ? `Are you sure you want to delete all ${status} videos in theme "${theme}"?`
      : `Are you sure you want to delete ALL videos in theme "${theme}"?`;

    if (confirm(confirmMessage)) {
      deleteByThemeMutation.mutate({ theme, status });
    }
  };

  const handleDeleteByStatus = (status: string) => {
    if (confirm(`Are you sure you want to delete ALL videos with status "${status}"?`)) {
      deleteByStatusMutation.mutate(status);
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

  const themes = themesData?.themes || [];

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
        <div className="flex space-x-3">
          {showBulkActions && (
            <button
              onClick={handleBulkDelete}
              disabled={bulkDeleteMutation.isPending}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 flex items-center disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete Selected ({selectedVideos.size})
            </button>
          )}
          <button
            onClick={() => setShowFetchForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
          >
            <Download className="w-4 h-4 mr-2" />
            Fetch Videos
          </button>
        </div>
      </div>

      {/* Video Stats */}
      {videoStats && (
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Video Statistics
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{videoStats.total_videos}</div>
              <div className="text-sm text-gray-600">Total Videos</div>
            </div>
            {Object.entries(videoStats.by_status).map(([status, count]) => (
              <div key={status} className="text-center">
                <div className="text-xl font-bold text-gray-900">{count as number}</div>
                <div className="text-sm text-gray-600 capitalize flex items-center justify-center">
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(status)}`}>
                    {status}
                  </span>
                </div>
                <button
                  onClick={() => handleDeleteByStatus(status)}
                  className="text-xs text-red-600 hover:text-red-800 mt-1"
                >
                  Delete all {status}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
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
            {videos && videos.length > 0 && (
              <button
                onClick={handleSelectAll}
                className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
              >
                {selectedVideos.size === videos.length ? (
                  <CheckSquare className="w-4 h-4 mr-1" />
                ) : (
                  <Square className="w-4 h-4 mr-1" />
                )}
                {selectedVideos.size === videos.length ? 'Deselect All' : 'Select All'}
              </button>
            )}
          </div>

          {selectedTheme && (
            <div className="flex space-x-2">
              <button
                onClick={() => handleDeleteByTheme(selectedTheme, 'pending')}
                className="text-sm text-orange-600 hover:text-orange-800"
              >
                Delete Pending
              </button>
              <button
                onClick={() => handleDeleteByTheme(selectedTheme, 'failed')}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Delete Failed
              </button>
              <button
                onClick={() => handleDeleteByTheme(selectedTheme)}
                className="text-sm text-red-700 hover:text-red-900 font-medium"
              >
                Delete All in Theme
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Videos Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {videos?.map((video, index) => (
          <div key={`${video.link}-${index}`} className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleVideoSelect(video.link, !selectedVideos.has(video.link))}
                    className="text-gray-400 hover:text-blue-600"
                  >
                    {selectedVideos.has(video.link) ? (
                      <CheckSquare className="w-4 h-4" />
                    ) : (
                      <Square className="w-4 h-4" />
                    )}
                  </button>
                  <span className="px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                    {video.theme}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(video.status)}`}>
                    {video.status}
                  </span>
                  <button
                    onClick={() => handleDeleteVideo(video.link)}
                    disabled={deleteMutation.isPending}
                    className="text-red-600 hover:text-red-800 disabled:opacity-50"
                    title="Delete video"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
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
                <select
                  value={fetchData.theme}
                  onChange={(e) => handleThemeChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select theme...</option>
                  {themes.map(theme => (
                    <option key={theme} value={theme}>{theme}</option>
                  ))}
                </select>
              </div>

              {fetchData.theme && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    TikTok Sources *
                  </label>
                  {availableSources && availableSources.length > 0 ? (
                    <div className="max-h-40 overflow-y-auto border border-gray-300 rounded-md">
                      {availableSources.map((source) => (
                        <label key={source.id} className="flex items-center p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0">
                          <input
                            type="checkbox"
                            checked={fetchData.source_usernames.includes(source.tiktok_username)}
                            onChange={(e) => handleSourceToggle(source.tiktok_username, e.target.checked)}
                            className="mr-3 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <div className="flex-1">
                            <span className="text-sm font-medium text-gray-900">@{source.tiktok_username}</span>
                            <div className="text-xs text-gray-500">
                              {source.videos_count} videos fetched
                              {source.last_fetch && ` • Last: ${new Date(source.last_fetch).toLocaleDateString()}`}
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 text-center text-gray-500 border border-gray-300 rounded-md">
                      <p>No TikTok sources found for theme "{fetchData.theme}"</p>
                      <p className="text-xs mt-1">Add sources in the TikTok Sources page first</p>
                    </div>
                  )}

                  {availableSources && availableSources.length > 0 && (
                    <div className="mt-2 flex justify-between text-xs text-gray-500">
                      <span>{fetchData.source_usernames.length} selected</span>
                      <button
                        type="button"
                        onClick={() => {
                          if (fetchData.source_usernames.length === availableSources.length) {
                            setFetchData({ ...fetchData, source_usernames: [] });
                          } else {
                            setFetchData({
                              ...fetchData,
                              source_usernames: availableSources.map(s => s.tiktok_username)
                            });
                          }
                        }}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        {fetchData.source_usernames.length === availableSources.length ? 'Deselect All' : 'Select All'}
                      </button>
                    </div>
                  )}
                </div>
              )}

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
                  disabled={fetchMutation.isPending || fetchData.source_usernames.length === 0}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {fetchMutation.isPending ? 'Fetching...' : `Fetch from ${fetchData.source_usernames.length} Sources`}
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