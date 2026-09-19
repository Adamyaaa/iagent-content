import { useState, useEffect } from 'react';
import axios from 'axios';
import { Save, Loader2, CheckCircle2, Info } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export default function Settings() {
  const [settings, setSettings] = useState({
    groq_api_key: '',
    gemini_api_key: '',
    supabase_url: '',
    supabase_service_key: ''
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API_URL}/settings/`);
      setSettings(response.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setSettings({ ...settings, [e.target.name]: e.target.value });
    setSaved(false);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await axios.post(`${API_URL}/settings/`, settings);
      setSaved(true);
      fetchSettings(); // Refresh to get masked values
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-8"><Loader2 className="animate-spin text-accent" /></div>;
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-3xl font-light mb-8">System Settings</h2>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
        <form onSubmit={handleSave} className="space-y-6">
          
          <div>
            <h3 className="text-lg font-medium mb-4 pb-2 border-b border-gray-100">AI Intelligence Providers</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Groq API Key (Whisper Transcription)</label>
                <input 
                  type="text" 
                  name="groq_api_key"
                  value={settings.groq_api_key}
                  onChange={handleChange}
                  placeholder="gsk_..."
                  className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Google Gemini API Key (Multimodal Analysis)</label>
                <input 
                  type="text" 
                  name="gemini_api_key"
                  value={settings.gemini_api_key}
                  onChange={handleChange}
                  placeholder="AIza..."
                  className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
                />
              </div>
            </div>
          </div>

          <div className="pt-4">
            <h3 className="text-lg font-medium mb-4 pb-2 border-b border-gray-100 flex items-center justify-between">
              Database Configuration
            </h3>
            
            <div className="bg-blue-50/50 p-4 rounded-lg flex gap-3 border border-blue-100">
              <Info className="text-blue-500 shrink-0" size={20} />
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Supabase credentials are managed via Environment Variables.</p>
                <p>To keep the backend stateless for free deployment, <b>SUPABASE_URL</b> and <b>SUPABASE_SERVICE_KEY</b> must be set in your hosting provider's dashboard (e.g., Render, Koyeb, Vercel). The AI keys above are saved directly to your Supabase database.</p>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-gray-100 flex items-center justify-between">
            {saved ? (
              <span className="flex items-center gap-2 text-green-600 font-medium">
                <CheckCircle2 size={20} /> Settings saved to Database
              </span>
            ) : <span />}
            
            <button 
              type="submit" 
              disabled={saving}
              className="bg-foreground text-background px-6 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              {saving ? <Loader2 className="animate-spin" size={20} /> : <Save size={20} />}
              Save Configuration
            </button>
          </div>
          
        </form>
      </div>
    </div>
  );
}
