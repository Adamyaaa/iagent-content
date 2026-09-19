import { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, ExternalLink } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export default function Settings() {
  const [settings, setSettings] = useState({
    groq_api_key: '',
    gemini_api_key: ''
  });
  
  const [inputValues, setInputValues] = useState({
    groq_api_key: '',
    gemini_api_key: ''
  });

  const [loading, setLoading] = useState(true);
  const [savingState, setSavingState] = useState({});

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API_URL}/settings/`);
      setSettings(response.data);
      setInputValues({
        groq_api_key: '',
        gemini_api_key: ''
      });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (id, value) => {
    setInputValues(prev => ({ ...prev, [id]: value }));
  };

  const handleAction = async (id, action) => {
    setSavingState(prev => ({ ...prev, [id]: action }));
    
    try {
      const payload = { ...settings };
      
      if (action === 'save') {
        payload[id] = inputValues[id];
      } else if (action === 'remove') {
        payload[id] = '';
      }
      
      // We send the whole object but only the updated fields are processed backend
      await axios.post(`${API_URL}/settings/`, payload);
      await fetchSettings();
    } catch (e) {
      console.error(e);
    } finally {
      setSavingState(prev => ({ ...prev, [id]: null }));
    }
  };

  const providers = [
    {
      id: 'groq_api_key',
      name: 'Groq',
      description: 'Speech to text — extremely fast Whisper models · free tier available',
      url: 'https://console.groq.com/keys'
    },
    {
      id: 'gemini_api_key',
      name: 'Gemini',
      description: 'Multimodal visual analysis & script generation · generous free tier',
      url: 'https://aistudio.google.com/app/apikey'
    }
  ];

  if (loading) {
    return <div className="p-8"><Loader2 className="animate-spin text-accent" /></div>;
  }

  return (
    <div className="max-w-4xl pb-12">
      <h2 className="text-3xl font-light mb-8">System Settings</h2>
      
      <div className="bg-[#fdfcfaf0] rounded-xl shadow-sm border border-gray-100 p-8 space-y-8">
        
        {providers.map((provider, index) => {
          const isConnected = !!settings[provider.id];
          const maskedKey = settings[provider.id];
          const isProcessingSave = savingState[provider.id] === 'save';
          const isProcessingRemove = savingState[provider.id] === 'remove';
          
          return (
            <div key={provider.id} className={index !== 0 ? "pt-8 border-t border-gray-200/60" : ""}>
              
              <div className="flex justify-between items-start mb-1">
                <div className="flex items-center gap-3">
                  <h3 className="text-xl font-bold text-gray-900">{provider.name}</h3>
                  
                  {isConnected ? (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100/60 text-green-700 border border-green-200/50">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-600"></span>
                      connected · {maskedKey.substring(0, 4)}...{maskedKey.substring(maskedKey.length - 4)}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100/50 text-orange-800 border border-orange-200/50">
                      not connected
                    </span>
                  )}
                </div>
                
                <a 
                  href={provider.url} 
                  target="_blank" 
                  rel="noreferrer"
                  className="text-sm font-medium text-gray-600 hover:text-gray-900 flex items-center gap-1 transition-colors"
                >
                  Get a key <ExternalLink size={14} />
                </a>
              </div>
              
              <p className="text-sm text-gray-500 mb-4">{provider.description}</p>
              
              <div className="flex gap-3">
                <input 
                  type="text" 
                  placeholder={isConnected ? "replace the key" : "paste your key"}
                  value={inputValues[provider.id]}
                  onChange={(e) => handleInputChange(provider.id, e.target.value)}
                  className="flex-1 px-4 py-2.5 bg-[#f5f4ef] border border-gray-200/80 rounded-lg text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-200 focus:border-gray-300 transition-all"
                />
                
                <button 
                  onClick={() => handleAction(provider.id, 'save')}
                  disabled={isProcessingSave || !inputValues[provider.id]}
                  className="px-6 py-2.5 bg-white border border-gray-200/80 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:hover:bg-white transition-colors min-w-[80px] flex justify-center items-center"
                >
                  {isProcessingSave ? <Loader2 size={16} className="animate-spin" /> : "Save"}
                </button>
                
                <button 
                  onClick={() => alert("Test functionality coming soon")}
                  className="px-6 py-2.5 bg-white border border-gray-200/80 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Test
                </button>
                
                <button 
                  onClick={() => handleAction(provider.id, 'remove')}
                  disabled={!isConnected || isProcessingRemove}
                  className="px-6 py-2.5 bg-white border border-gray-200/80 rounded-lg text-sm font-medium text-gray-700 hover:bg-red-50 hover:text-red-600 hover:border-red-200 disabled:opacity-50 transition-colors min-w-[90px] flex justify-center items-center"
                >
                  {isProcessingRemove ? <Loader2 size={16} className="animate-spin" /> : "Remove"}
                </button>
              </div>
              
            </div>
          );
        })}
        
      </div>
    </div>
  );
}
