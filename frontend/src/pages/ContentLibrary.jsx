import { useState, useEffect } from 'react';
import { getConcepts } from '../services/api';
import { FileText, CheckCircle2, AlertCircle } from 'lucide-react';

export default function ContentLibrary() {
  const [concepts, setConcepts] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetchConcepts();
  }, []);

  const fetchConcepts = async () => {
    try {
      const data = await getConcepts();
      setConcepts(data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex gap-6">
      {/* List View */}
      <div className="w-1/3 flex flex-col bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100 bg-gray-50">
          <h2 className="font-medium">Generated Concepts</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {concepts.map((c) => (
            <div 
              key={c.id} 
              onClick={() => setSelected(c)}
              className={`p-4 rounded-lg cursor-pointer border transition-colors ${selected?.id === c.id ? 'border-accent bg-orange-50/30' : 'border-gray-100 hover:border-gray-300'}`}
            >
              <h3 className="font-medium text-sm mb-2">{c.title}</h3>
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
      <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 overflow-y-auto p-8">
        {selected ? (
          <div className="max-w-2xl">
            <div className="flex items-center gap-3 mb-6">
              <FileText className="text-accent" size={28} />
              <h1 className="text-2xl font-semibold">{selected.title}</h1>
            </div>
            
            <div className="mb-8 grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Target Audience</p>
                <p className="font-medium">{selected.generated_concept.target_audience}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">QA Score</p>
                <p className="font-medium text-lg text-accent">{selected.qa_scores?.overall_score || 'N/A'}/100</p>
              </div>
            </div>

            <div className="space-y-6">
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
                  {selected.scene_breakdowns.map((scene, i) => (
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
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400">
            Select a concept to view details.
          </div>
        )}
      </div>
    </div>
  );
}
