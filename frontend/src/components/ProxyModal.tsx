import { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { X, Globe, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { accountsApi } from '../services/api';
import type { ProxySettings } from '../types';

interface ProxyModalProps {
  isOpen: boolean;
  onClose: () => void;
  username: string;
}

const ProxyModal = ({ isOpen, onClose, username }: ProxyModalProps) => {
  const [formData, setFormData] = useState<ProxySettings>({
    proxy_type: 'HTTP',
    proxy_host: '',
    proxy_port: 8080,
    proxy_username: '',
    proxy_password: '',
    proxy_active: true,
  });

  const [isTestingProxy, setIsTestingProxy] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const queryClient = useQueryClient();

  // Load existing proxy settings
  const { data: existingProxy } = useQuery({
    queryKey: ['proxy', username],
    queryFn: () => accountsApi.getProxy(username),
    enabled: isOpen && !!username,
  });

  // Update form when proxy data loads
  useEffect(() => {
    if (existingProxy?.proxy_configured) {
      setFormData({
        proxy_type: existingProxy.proxy_type || 'HTTP',
        proxy_host: existingProxy.proxy_host || '',
        proxy_port: existingProxy.proxy_port || 8080,
        proxy_username: existingProxy.proxy_username || '',
        proxy_password: '',
        proxy_active: existingProxy.proxy_active || false,
      });
    } else {
      setFormData({
        proxy_type: 'HTTP',
        proxy_host: '',
        proxy_port: 8080,
        proxy_username: '',
        proxy_password: '',
        proxy_active: true,
      });
    }
    setTestResult(null);
  }, [existingProxy, isOpen]);

  const updateProxyMutation = useMutation({
    mutationFn: (proxySettings: ProxySettings) => accountsApi.updateProxy(username, proxySettings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['proxy', username] });
      toast.success('Proxy settings saved successfully!');
      onClose();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to save proxy settings');
    },
  });

  const removeProxyMutation = useMutation({
    mutationFn: () => accountsApi.removeProxy(username),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['proxy', username] });
      toast.success('Proxy removed successfully!');
      onClose();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to remove proxy');
    },
  });

  const testProxy = async () => {
    if (!formData.proxy_host || !formData.proxy_port) {
      toast.error('Please fill in host and port before testing');
      return;
    }

    setIsTestingProxy(true);
    setTestResult(null);

    try {
      // First save the proxy settings
      await accountsApi.updateProxy(username, formData);

      // Then test it
      const result = await accountsApi.testProxy(username);
      setTestResult(result);

      if (result.success) {
        toast.success('Proxy is working correctly!');
      } else {
        toast.error(`Proxy test failed: ${result.message}`);
      }

      // Refresh accounts to show updated status
      queryClient.invalidateQueries({ queryKey: ['accounts'] });

    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to test proxy');
      setTestResult({
        success: false,
        message: error.response?.data?.detail || 'Test failed'
      });
    } finally {
      setIsTestingProxy(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.proxy_host || !formData.proxy_port) {
      toast.error('Please fill in all required fields');
      return;
    }

    updateProxyMutation.mutate(formData);
  };

  const handleRemoveProxy = () => {
    if (confirm('Are you sure you want to remove proxy settings for this account?')) {
      removeProxyMutation.mutate();
    }
  };

  if (!isOpen) return null;

  const getProxyStatusIcon = () => {
    if (!existingProxy?.proxy_configured) return null;

    switch (existingProxy.proxy_status) {
      case 'working':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-screen overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center space-x-2">
            <Globe className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">
              Proxy Settings - @{username}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Current Status */}
        {existingProxy?.proxy_configured && (
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Current Status:</span>
              <div className="flex items-center space-x-2">
                {getProxyStatusIcon()}
                <span className="text-sm capitalize">
                  {existingProxy.proxy_status || 'unchecked'}
                </span>
              </div>
            </div>
            {existingProxy.proxy_last_check && (
              <div className="text-xs text-gray-500 mt-1">
                Last checked: {new Date(existingProxy.proxy_last_check).toLocaleString()}
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Proxy Type *
            </label>
            <select
              value={formData.proxy_type}
              onChange={(e) => setFormData({ ...formData, proxy_type: e.target.value as 'HTTP' | 'SOCKS5' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="HTTP">HTTP</option>
              <option value="SOCKS5">SOCKS5</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Host/IP *
              </label>
              <input
                type="text"
                value={formData.proxy_host}
                onChange={(e) => setFormData({ ...formData, proxy_host: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="1.2.3.4"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Port *
              </label>
              <input
                type="number"
                value={formData.proxy_port}
                onChange={(e) => setFormData({ ...formData, proxy_port: parseInt(e.target.value) || 8080 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="8080"
                min="1"
                max="65535"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username (Optional)
            </label>
            <input
              type="text"
              value={formData.proxy_username}
              onChange={(e) => setFormData({ ...formData, proxy_username: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="proxy username"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password (Optional)
            </label>
            <input
              type="password"
              value={formData.proxy_password}
              onChange={(e) => setFormData({ ...formData, proxy_password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="proxy password"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              checked={formData.proxy_active}
              onChange={(e) => setFormData({ ...formData, proxy_active: e.target.checked })}
              className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label className="text-sm text-gray-700">Enable proxy for this account</label>
          </div>

          {/* Test Results */}
          {testResult && (
            <div className={`p-3 rounded-lg ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <div className="flex items-center space-x-2">
                {testResult.success ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-600" />
                )}
                <span className={`text-sm font-medium ${testResult.success ? 'text-green-800' : 'text-red-800'}`}>
                  {testResult.success ? 'Proxy Working' : 'Proxy Failed'}
                </span>
              </div>
              <p className={`text-xs mt-1 ${testResult.success ? 'text-green-700' : 'text-red-700'}`}>
                {testResult.message}
              </p>
              {testResult.success && testResult.external_ip && (
                <div className="text-xs text-green-600 mt-1">
                  External IP: {testResult.external_ip}
                  {testResult.response_time && ` • Response: ${testResult.response_time}s`}
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-between pt-4">
            <div className="space-x-2">
              <button
                type="button"
                onClick={testProxy}
                disabled={isTestingProxy || !formData.proxy_host || !formData.proxy_port}
                className="px-3 py-2 text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 disabled:opacity-50 flex items-center"
              >
                {isTestingProxy ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Globe className="w-4 h-4 mr-2" />
                )}
                {isTestingProxy ? 'Testing...' : 'Test Proxy'}
              </button>

              {existingProxy?.proxy_configured && (
                <button
                  type="button"
                  onClick={handleRemoveProxy}
                  disabled={removeProxyMutation.isPending}
                  className="px-3 py-2 text-red-600 border border-red-300 rounded-md hover:bg-red-50 disabled:opacity-50"
                >
                  Remove Proxy
                </button>
              )}
            </div>

            <div className="space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updateProxyMutation.isPending || !formData.proxy_host || !formData.proxy_port}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {updateProxyMutation.isPending ? 'Saving...' : 'Save Proxy'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProxyModal;