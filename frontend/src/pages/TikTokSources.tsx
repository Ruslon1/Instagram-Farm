import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit2, Trash2, ExternalLink, Filter, UserCheck } from 'lucide-react';
import toast from 'react-hot-toast';
import { tikTokSourcesApi } from '../services/api';
import type { TikTokSourceCreate } from '../types';

const TikTokSources = () => {
  const [showForm, setShowForm] = useState(false);
  const [editingSource, setEditingSource] = useState<any>(null);
  const [selectedTheme, setSelectedTheme] = useState<string>('');
  const [formData, setFormData] = useState<TikTokSourceCreate>({
    theme: '',
    tiktok_username: '',
    active: true,
  });

  const queryClient = useQueryClient();

  const { data: sources, isLoading } = useQuery({
    queryKey: ['tiktok-sources', selectedTheme],
    queryFn: () => tikTokSourcesApi.getAll(selectedTheme || undefined),
  });

  const { data: themesData } = useQuery({
    queryKey: ['themes'],
    queryFn: tikTokSourcesApi.getThemes,
  });

  const createMutation = useMutation({
    mutationFn: tikTokSourcesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tiktok-sources'] });
      toast.success('TikTok source added successfully!');
      resetForm();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add TikTok source');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => tikTokSourcesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tiktok-sources'] });
      toast.success('TikTok source updated successfully!');
      resetForm();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update TikTok source');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: tikTokSourcesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tiktok-sources'] });
      toast.success('TikTok source deleted successfully!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete TikTok source');
    },
  });

  const resetForm = () => {
    setFormData({ theme: '', tiktok_username: '', active: true });
    setShowForm(false);
    setEditingSource(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.theme || !formData.tiktok_username) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (editingSource) {
      updateMutation.mutate({ id: editingSource.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleEdit = (source: any) => {
    setEditingSource(source);
    setFormData({
      theme: source.theme,
      tiktok_username: source.tiktok_username,
      active: source.active,
    });
    setShowForm(true);
  };

  const handleDelete = (sourceId: number) => {
    if (confirm('Are you sure you want to delete this TikTok source?')) {
      deleteMutation.mutate(sourceId);
    }
  };

  const toggleActive = (source: any) => {
    updateMutation.mutate({
      id: source.id,
      data: { active: !source.active }
    });
  };

  const themes = themesData?.themes || [];
  const groupedSources = sources?.reduce((acc: any, source: any) => {
    if (!acc[source.theme]) {
      acc[source.theme] = [];
    }
    acc[source.theme].push(source);
    return acc;
  }, {}) || {};

  if (isLoading) {
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
          <h1 className="text-2xl font-bold text-gray-900">TikTok Sources</h1>
          <p className="text-gray-600">Manage TikTok accounts to fetch videos from</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Source
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
            {sources?.length || 0} sources
          </span>
        </div>
      </div>

      {/* Sources by Theme */}
      <div className="space-y-6">
        {Object.keys(groupedSources).map(theme => (
          <div key={theme} className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 capitalize">{theme}</h2>
              <p className="text-sm text-gray-600">{groupedSources[theme].length} sources</p>
            </div>

            <div className="divide-y divide-gray-200">
              {groupedSources[theme].map((source: any) => (
                <div key={source.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <div className={`w-3 h-3 rounded-full ${source.active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-medium text-gray-900">@{source.tiktok_username}</span>
                          <a
                            href={`https://tiktok.com/@${source.tiktok_username}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>Videos fetched: {source.videos_count}</span>
                          {source.last_fetch && (
                            <span>Last fetch: {new Date(source.last_fetch).toLocaleDateString()}</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => toggleActive(source)}
                        className={`p-2 rounded-lg ${
                          source.active 
                            ? 'text-green-600 hover:bg-green-50' 
                            : 'text-gray-400 hover:bg-gray-50'
                        }`}
                        title={source.active ? 'Deactivate' : 'Activate'}
                      >
                        <UserCheck className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleEdit(source)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                        title="Edit"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(source.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {Object.keys(groupedSources).length === 0 && (
        <div className="text-center py-12">
          <UserCheck className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No TikTok sources</h3>
          <p className="mt-1 text-sm text-gray-500">
            Add TikTok accounts to start fetching videos from them.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowForm(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Add First Source
            </button>
          </div>
        </div>
      )}

      {/* Add/Edit Source Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {editingSource ? 'Edit TikTok Source' : 'Add TikTok Source'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Theme *
                </label>
                <input
                  type="text"
                  value={formData.theme}
                  onChange={(e) => setFormData({ ...formData, theme: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., ishowspeed, gaming, funny"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  TikTok Username *
                </label>
                <div className="flex">
                  <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500 text-sm">
                    @
                  </span>
                  <input
                    type="text"
                    value={formData.tiktok_username}
                    onChange={(e) => setFormData({ ...formData, tiktok_username: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-r-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="username"
                    required
                  />
                </div>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.active}
                  onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                  className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label className="text-sm text-gray-700">Active</label>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? 'Saving...'
                    : editingSource
                    ? 'Update Source'
                    : 'Add Source'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TikTokSources;