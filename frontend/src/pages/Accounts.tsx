import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, User, Calendar, TrendingUp, Globe, CheckCircle, XCircle, Clock, Settings, Shield, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { accountsApi } from '../services/api';
import ProxyModal from '../components/ProxyModal';
import type { AccountCreate } from '../types';

const Accounts = () => {
  const [showForm, setShowForm] = useState(false);
  const [showProxyModal, setShowProxyModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<string>('');
  const [isVerifying, setIsVerifying] = useState<string>(''); // Track which account is being verified
  const [formData, setFormData] = useState<AccountCreate>({
    username: '',
    password: '',
    theme: '',
    two_fa_key: '',
  });

  const queryClient = useQueryClient();

  const { data: accounts, isLoading, error } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.getAll,
  });

  const createMutation = useMutation({
    mutationFn: accountsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast.success('Account created and verified successfully!');
      setShowForm(false);
      setFormData({ username: '', password: '', theme: '', two_fa_key: '' });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create account');
    },
  });

  const verifyMutation = useMutation({
    mutationFn: accountsApi.verify,
    onSuccess: (_data, username) => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast.success(`Account @${username} verified successfully!`);
      setIsVerifying('');
    },
    onError: (error: any, username) => {
      toast.error(error.response?.data?.detail || `Failed to verify @${username}`);
      setIsVerifying('');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.username || !formData.password || !formData.theme) {
      toast.error('Please fill in all required fields');
      return;
    }
    createMutation.mutate(formData);
  };

  const handleVerifyAccount = (username: string) => {
    if (confirm(`Verify login for @${username}? This will refresh the session and may take a moment.`)) {
      setIsVerifying(username);
      verifyMutation.mutate(username);
    }
  };

  const handleProxyClick = (username: string) => {
    setSelectedAccount(username);
    setShowProxyModal(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'blocked':
        return 'bg-red-100 text-red-800';
      case 'error':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getProxyStatusIcon = (account: any) => {
    if (!account.proxy_host) {
      return <Globe className="w-4 h-4 text-gray-300" />;
    }

    if (!account.proxy_active) {
      return <Globe className="w-4 h-4 text-gray-400" />;
    }

    switch (account.proxy_status) {
      case 'working':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-600" />;
    }
  };

  const getProxyTooltip = (account: any) => {
    if (!account.proxy_host) return 'No proxy configured';
    if (!account.proxy_active) return 'Proxy disabled';

    const status = account.proxy_status || 'unchecked';
    const host = account.proxy_host;
    const port = account.proxy_port;

    return `${host}:${port} - ${status}`;
  };

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
        <p className="text-red-800">Failed to load accounts</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Instagram Accounts</h1>
          <p className="text-gray-600">Manage your Instagram accounts and proxy settings</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="bg-pink-600 text-white px-4 py-2 rounded-lg hover:bg-pink-700 flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Account
        </button>
      </div>

      {/* Accounts Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Account
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Theme
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Proxy
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Posts
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Login
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {accounts?.map((account) => (
              <tr key={account.username} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-pink-100 flex items-center justify-center">
                        <User className="w-5 h-5 text-pink-600" />
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        @{account.username}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                    {account.theme}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(account.status)}`}>
                    {account.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    <div title={getProxyTooltip(account)}>
                      {getProxyStatusIcon(account)}
                    </div>
                    {account.proxy_host && (
                      <div className="text-xs text-gray-500">
                        {account.proxy_host}:{account.proxy_port}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div className="flex items-center">
                    <TrendingUp className="w-4 h-4 text-gray-400 mr-1" />
                    {account.posts_count}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 text-gray-400 mr-1" />
                    {account.last_login ? new Date(account.last_login).toLocaleDateString() : 'Never'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleVerifyAccount(account.username)}
                      disabled={isVerifying === account.username || verifyMutation.isPending}
                      className="text-green-600 hover:text-green-800 flex items-center space-x-1 disabled:opacity-50"
                      title="Verify login and refresh session"
                    >
                      {isVerifying === account.username ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <Shield className="w-4 h-4" />
                      )}
                      <span>{isVerifying === account.username ? 'Verifying...' : 'Verify'}</span>
                    </button>
                    <button
                      onClick={() => handleProxyClick(account.username)}
                      className="text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                    >
                      <Settings className="w-4 h-4" />
                      <span>Proxy</span>
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {accounts?.length === 0 && (
          <div className="text-center py-12">
            <User className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No accounts</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by adding your first Instagram account.</p>
            <div className="mt-6">
              <button
                onClick={() => setShowForm(true)}
                className="bg-pink-600 text-white px-4 py-2 rounded-lg hover:bg-pink-700"
              >
                Add Account
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add Account Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Add Instagram Account</h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username *
                </label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500"
                  placeholder="Enter Instagram username"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password *
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500"
                  placeholder="Enter password"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Theme *
                </label>
                <input
                  type="text"
                  value={formData.theme}
                  onChange={(e) => setFormData({ ...formData, theme: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500"
                  placeholder="e.g., ishowspeed, gaming, funny"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  2FA Key (Optional)
                </label>
                <input
                  type="text"
                  value={formData.two_fa_key || ''}
                  onChange={(e) => setFormData({ ...formData, two_fa_key: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500"
                  placeholder="2FA key if enabled"
                />
              </div>

              {/* Verification Notice */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <Shield className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-800">Account Verification</span>
                </div>
                <p className="text-xs text-blue-700 mt-1">
                  Your Instagram credentials will be verified during account creation to ensure they work correctly and create a session file.
                </p>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-pink-600 text-white rounded-md hover:bg-pink-700 disabled:opacity-50 flex items-center"
                >
                  {createMutation.isPending ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    <>
                      <Shield className="w-4 h-4 mr-2" />
                      Create & Verify Account
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Proxy Modal */}
      <ProxyModal
        isOpen={showProxyModal}
        onClose={() => setShowProxyModal(false)}
        username={selectedAccount}
      />
    </div>
  );
};

export default Accounts;