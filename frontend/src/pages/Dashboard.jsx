import { useState, useEffect } from 'react';
import { ingestUrl, getQueue, deleteQueueItem } from '../services/api';
import { Play, Loader2, Link as LinkIcon, CheckCircle2, AlertCircle, Trash2 } from 'lucide-react';

export default function Dashboard() {
  const [url, setUrl] = useState('');
  const [platform, setPlatform] = useState('youtube');
  const [loading, setLoading] = useState(false);
  const [queue, setQueue] = useState([]);
  const [message, setMessage] = useState('');

  const fetchQueue = async () => {
    try {
      const data = await getQueue();
      setQueue(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url) return;
    setLoading(true);
    setMessage('');
    try {
      await ingestUrl(url, platform);
      setMessage('URL submitted successfully! Pipeline started.');
      setUrl('');
      fetchQueue();
    } catch (error) {
      setMessage('Failed to submit URL.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to remove this item?')) return;
    try {
      await deleteQueueItem(id);
      fetchQueue();
    } catch (e) {
      console.error("Failed to delete", e);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'generated': return <CheckCircle2 className="text-green-500" size={18} />;
      case 'rejected': return <AlertCircle className="text-red-500" size={18} />;
      default: return <Loader2 className="text-accent animate-spin" size={18} />;
    }
  };

  return (
    <div className="max-w-4xl">
      <h2 className="text-3xl font-light mb-8">Process Content</h2>
      
      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 mb-8">
        <form onSubmit={handleSubmit} className="flex gap-4">
          <select 
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="px-4 py-4 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all text-gray-700 font-medium"
          >
            <option value="youtube">YouTube</option>
            <option value="instagram">Instagram Reel</option>
            <option value="linkedin">LinkedIn</option>
          </select>
          
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <LinkIcon className="text-gray-400" size={20} />
            </div>
            <input 
              type="url" 
              placeholder="Paste a YouTube, Instagram, or LinkedIn URL..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full pl-12 pr-4 py-4 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all"
              required
            />
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="bg-foreground text-background px-8 py-4 rounded-lg font-medium hover:bg-gray-800 transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <Play size={20} />}
            Process
          </button>
        </form>
        {message && <p className="mt-4 text-sm text-gray-600">{message}</p>}
      </div>

      <h3 className="text-xl font-medium mb-4">Pipeline Status</h3>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {queue.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No active processes in queue.</div>
        ) : (
          <table className="w-full text-left">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100 text-sm text-gray-500">
                <th className="px-6 py-4 font-medium">Source URL</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Started</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((item) => (
                <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50/50 group">
                  <td className="px-6 py-4 truncate max-w-xs">
                    <a href={item.source_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                      {item.source_url}
                    </a>
                  </td>
                  <td className="px-6 py-4">
                    <span className="flex items-center gap-2 text-sm capitalize">
                      {getStatusIcon(item.status)} {item.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button 
                      onClick={() => handleDelete(item.id)}
                      className="text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                      title="Delete"
                    >
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
