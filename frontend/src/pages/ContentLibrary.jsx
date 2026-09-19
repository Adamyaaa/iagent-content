import { useState, useEffect } from 'react';
import { getConcepts, deleteConcept } from '../services/api';
import { FileText, CheckCircle2, AlertCircle, Video, Briefcase, Camera, MessageCircle, Trash2 } from 'lucide-react';

export default function ContentLibrary() {
  const [concepts, setConcepts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [activeTab, setActiveTab] = useState('core'); // 'core', 'linkedin', 'instagram', 'whatsapp'
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    fetchConcepts();
  }, []);

  const fetchConcepts = async () => {
    try {
      const data = await getConcepts();
      setConcepts(data);
      if (data && data.length > 0) {
        setSelected(prev => {
          if (!prev) return data[0];
          const exists = data.find(c => c.id === prev.id);
          return exists || data[0];
        });
      } else {
        setSelected(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (conceptId, e) => {
    if (e) e.stopPropagation();
    if (!window.confirm('Are you sure you want to remove this concept?')) return;
    
    setDeletingId(conceptId);
    try {
      await deleteConcept(conceptId);
      const remaining = concepts.filter(c => c.id !== conceptId);
      setConcepts(remaining);
      if (selected?.id === conceptId) {
        setSelected(remaining.length > 0 ? remaining[0] : null);
      }
    } catch (err) {
      console.error('Failed to delete concept:', err);
      alert('Failed to delete concept. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex gap-6">
      {/* List View */}
      <div className="w-1/3 flex flex-col bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
          <h2 className="font-medium">Generated Concepts</h2>
          <span className="text-xs text-gray-500 font-medium">{concepts.length} total</span>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {concepts.map((c) => (
            <div 
              key={c.id} 
              onClick={() => { setSelected(c); setActiveTab('core'); }}
              className={`p-4 rounded-lg cursor-pointer border transition-all group relative ${selected?.id === c.id ? 'border-accent bg-orange-50/30' : 'border-gray-100 hover:border-gray-300'}`}
            >
              <div className="flex justify-between items-start gap-2 mb-2">
                <h3 className="font-medium text-sm leading-snug line-clamp-2">{c.title}</h3>
                <button
                  onClick={(e) => handleDelete(c.id, e)}
                  disabled={deletingId === c.id}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded shrink-0"
                  title="Remove Concept"
                >
                  <Trash2 size={14} className={deletingId === c.id ? "animate-spin" : ""} />
                </button>
              </div>
              <div className="flex justify-between items-center text-xs text-gray-500">
                <span>{new Date(c.created_at).toLocaleDateString()}</span>
                {c.approval_status ? (
                  <span className="flex items-center gap-1 text-green-600"><CheckCircle2 size={14}/> Approved</span>
                ) : (
                  <span className="flex items-center gap-1 text-red-500"><AlertCircle size={14}/> Rejected</span>
                )}
              </div>
            </div>
          ))}
          {concepts.length === 0 && <p className="text-sm text-gray-500 text-center py-8">No concepts generated yet.</p>}
        </div>
      </div>

      {/* Detail View */}
      <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
        {selected ? (
          <>
            {/* Header */}
            <div className="p-8 pb-0">
              <div className="flex items-start justify-between gap-4 mb-6">
                <div className="flex items-center gap-3">
                  <FileText className="text-accent shrink-0" size={28} />
                  <h1 className="text-2xl font-semibold">{selected.title}</h1>
                </div>
                <button
                  onClick={() => handleDelete(selected.id)}
                  disabled={deletingId === selected.id}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 hover:text-red-700 hover:bg-red-50 border border-red-200 rounded-lg transition-colors shrink-0"
                  title="Remove this concept"
                >
                  <Trash2 size={14} className={deletingId === selected.id ? "animate-spin" : ""} />
                  Remove
                </button>
              </div>
              
              {/* Tab Navigation */}
              <div className="flex gap-6 border-b border-gray-200">
                <button 
                  onClick={() => setActiveTab('core')}
                  className={`pb-3 font-medium text-sm transition-colors relative flex items-center gap-2 ${activeTab === 'core' ? 'text-accent' : 'text-gray-500 hover:text-gray-900'}`}
                >
                  <Video size={16} />
                  Core Video
                  {activeTab === 'core' && <span className="absolute bottom-0 left-0 w-full h-0.5 bg-accent rounded-t-full"></span>}
                </button>
                <button 
                  onClick={() => setActiveTab('linkedin')}
                  className={`pb-3 font-medium text-sm transition-colors relative flex items-center gap-2 ${activeTab === 'linkedin' ? 'text-accent' : 'text-gray-500 hover:text-gray-900'}`}
                >
                  <Briefcase size={16} />
                  LinkedIn
                  {activeTab === 'linkedin' && <span className="absolute bottom-0 left-0 w-full h-0.5 bg-accent rounded-t-full"></span>}
                </button>
                <button 
                  onClick={() => setActiveTab('instagram')}
                  className={`pb-3 font-medium text-sm transition-colors relative flex items-center gap-2 ${activeTab === 'instagram' ? 'text-accent' : 'text-gray-500 hover:text-gray-900'}`}
                >
                  <Camera size={16} />
                  Instagram
                  {activeTab === 'instagram' && <span className="absolute bottom-0 left-0 w-full h-0.5 bg-accent rounded-t-full"></span>}
                </button>
                <button 
                  onClick={() => setActiveTab('whatsapp')}
                  className={`pb-3 font-medium text-sm transition-colors relative flex items-center gap-2 ${activeTab === 'whatsapp' ? 'text-accent' : 'text-gray-500 hover:text-gray-900'}`}
                >
                  <MessageCircle size={16} />
                  WhatsApp
                  {activeTab === 'whatsapp' && <span className="absolute bottom-0 left-0 w-full h-0.5 bg-accent rounded-t-full"></span>}
                </button>
              </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-8 pt-6">
              
              {activeTab === 'core' && (
                <div className="max-w-2xl space-y-6 animate-in fade-in">
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Target Audience</p>
                      <p className="font-medium">{selected.generated_concept.target_audience}</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">QA Score</p>
                      <p className="font-medium text-lg text-accent">{selected.qa_scores?.overall_score || 'N/A'}/100</p>
                    </div>
                  </div>

                  <section>
                    <h3 className="text-sm font-semibold uppercase text-gray-400 mb-2">The Hook</h3>
                    <p className="text-lg italic text-gray-800">"{selected.generated_concept.hook}"</p>
                  </section>
                  <section>
                    <h3 className="text-sm font-semibold uppercase text-gray-400 mb-2">Body / Core Problem</h3>
                    <p className="text-gray-700 whitespace-pre-wrap">{selected.generated_concept.body}</p>
                  </section>
                  <section>
                    <h3 className="text-sm font-semibold uppercase text-gray-400 mb-2">Insight & CTA</h3>
                    <p className="text-gray-700 mb-2">{selected.generated_concept.insight}</p>
                    <p className="font-medium text-accent">{selected.generated_concept.cta}</p>
                  </section>
                  
                  <hr className="my-8 border-gray-100" />
                  
                  <section>
                    <h3 className="text-sm font-semibold uppercase text-gray-400 mb-4">Scene Breakdown</h3>
                    <div className="space-y-4">
                      {selected.scene_breakdowns?.map((scene, i) => (
                        <div key={i} className="flex gap-4 p-4 border border-gray-100 rounded-lg">
                          <div className="font-bold text-gray-300 text-xl">{scene.scene_number}</div>
                          <div>
                            <p className="text-sm text-gray-500 mb-1">{scene.duration_seconds}s • {scene.camera_direction}</p>
                            <p className="font-medium mb-1">{scene.voiceover}</p>
                            <p className="text-sm text-gray-600 bg-gray-50 inline-block px-2 py-1 rounded">Text: {scene.on_screen_text}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>
              )}

              {activeTab === 'linkedin' && (
                <div className="max-w-2xl space-y-8 animate-in fade-in">
                  {!selected.linkedin_ideation ? (
                    <p className="text-gray-500 italic">No LinkedIn ideation available for this concept.</p>
                  ) : (
                    <>
                      <section className="bg-[#f0f6fc] border border-[#d1e4f9] rounded-xl p-6">
                        <h3 className="text-sm font-semibold text-[#0a66c2] uppercase tracking-wider mb-4 flex items-center gap-2">
                          The Text Post
                        </h3>
                        <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{selected.linkedin_ideation.text_post}</p>
                      </section>
                      
                      <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                        <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wider mb-4">
                          PDF Carousel Outline (5 Slides)
                        </h3>
                        <div className="space-y-4">
                          {selected.linkedin_ideation.carousel_outline?.map((slide, i) => (
                            <div key={i} className="flex gap-4">
                              <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-gray-100 text-gray-600 rounded-full font-medium text-sm">
                                {i + 1}
                              </span>
                              <p className="text-gray-700 pt-1">{slide}</p>
                            </div>
                          ))}
                        </div>
                      </section>
                    </>
                  )}
                </div>
              )}

              {activeTab === 'instagram' && (
                <div className="max-w-2xl space-y-8 animate-in fade-in">
                  {!selected.instagram_ideation ? (
                    <p className="text-gray-500 italic">No Instagram ideation available for this concept.</p>
                  ) : (
                    <>
                      <section className="bg-gradient-to-br from-pink-50 to-orange-50 border border-orange-100 rounded-xl p-6">
                        <h3 className="text-sm font-semibold text-pink-600 uppercase tracking-wider mb-4">
                          Infographic Caption
                        </h3>
                        <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{selected.instagram_ideation.infographic_caption}</p>
                      </section>
                      
                      <section className="bg-gray-900 text-white rounded-xl p-6">
                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
                          IG Story Interactive Idea
                        </h3>
                        <p className="text-gray-100 leading-relaxed text-lg">{selected.instagram_ideation.story_idea}</p>
                      </section>
                    </>
                  )}
                </div>
              )}

              {activeTab === 'whatsapp' && (
                <div className="max-w-2xl space-y-8 animate-in fade-in">
                  {!selected.whatsapp_ideation ? (
                    <p className="text-gray-500 italic">No WhatsApp ideation available for this concept.</p>
                  ) : (
                    <>
                      <section className="bg-[#e8fce8] border border-[#a6f0af] rounded-xl p-6 relative">
                        <div className="absolute top-4 right-4 bg-green-500 text-white text-[10px] font-bold px-2 py-1 rounded uppercase tracking-widest">Broadcast</div>
                        <h3 className="text-sm font-semibold text-green-800 uppercase tracking-wider mb-4">
                          WhatsApp Broadcast
                        </h3>
                        <p className="text-gray-900 whitespace-pre-wrap leading-relaxed">{selected.whatsapp_ideation.broadcast_message}</p>
                      </section>
                      
                      <section className="bg-white border-2 border-gray-100 rounded-xl p-6">
                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
                          Community Poll
                        </h3>
                        <p className="text-gray-800 leading-relaxed font-medium text-lg">{selected.whatsapp_ideation.community_poll}</p>
                      </section>
                    </>
                  )}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400">
            Select a concept to view details.
          </div>
        )}
      </div>
    </div>
  );
}
