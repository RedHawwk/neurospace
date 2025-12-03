import React, { useState, useRef } from 'react';
import { 
  LayoutDashboard, Upload, Eye, ScanLine, Sparkles, FileText, 
  ArrowUpRight, DollarSign, Clock, AlertTriangle, 
  CheckCircle2, Info, Brain, Utensils, Heart, Armchair, Zap, 
  Target, Users, Award, Share2, Download, TrendingUp
} from 'lucide-react';
import { 
  ResponsiveContainer, RadarChart, PolarGrid, 
  PolarAngleAxis, PolarRadiusAxis, Radar, Legend, Tooltip 
} from 'recharts';

// ✅ API base: local in dev, Render in production
const API_BASE = import.meta.env.PROD
  ? "https://neurospace-api.onrender.com" // ← replace with your Render URL
  : "http://127.0.0.1:5000";


// --- ICON & COLOR MAPS FOR DYNAMIC DATA ---
const ICON_MAP = {
  'Utensils': Utensils,
  'Heart': Heart,
  'Sparkles': Sparkles,
  'Armchair': Armchair,
  'Zap': Zap,
  'Target': Target,
  'Users': Users,
  'Award': Award,
  'Share2': Share2,
  'Brain': Brain
};

const COLOR_MAP = {
  1: "bg-orange-500",
  2: "bg-teal-500",
  3: "bg-amber-500",
  4: "bg-indigo-500",
  5: "bg-blue-500",
  6: "bg-purple-500",
  7: "bg-rose-500",
  8: "bg-emerald-500",
  9: "bg-pink-500"
};

const DEFAULT_ICON_MAP = {
  1: Utensils,
  2: Heart,
  3: Sparkles,
  4: Armchair,
  5: Zap,
  6: Target,
  7: Users,
  8: Award,
  9: Share2
};


// --- FALLBACK DATA (used if no analysis yet) ---
const FALLBACK_REPORT_DATA = [
  {
    id: 1,
    title: "Dopamine & Appetite Stimulation",
    score: 9.2,
    drivers: ["3D food wall art", "High color contrast", "Plate-like patterns"],
    neuralImpact: "Strong activation of dopaminergic reward system.",
    businessEffect: "Very high impulse ordering & dessert conversion.",
    tag: "Premium upsell probability: High"
  }
];


// --- REUSABLE COMPONENTS ---
const MetricCard = ({ icon: Icon, title, value, subtext, trend, trendValue, color }) => (
  <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
    <div className="flex justify-between items-start mb-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      {trend && (
        <div className={`flex items-center text-sm font-medium ${trend === 'up' ? 'text-emerald-600' : 'text-rose-600'}`}>
          <ArrowUpRight className={`w-4 h-4 mr-1 ${trend === 'down' ? 'rotate-90' : ''}`} />
          {trendValue}
        </div>
      )}
    </div>
    <h3 className="text-slate-500 text-sm font-medium mb-1">{title}</h3>
    <div className="text-2xl font-bold text-slate-800">{value}</div>
    {subtext && <div className="text-xs text-slate-400 mt-2">{subtext}</div>}
  </div>
);


const ProgressBar = ({ label, value, colorClass, target }) => (
  <div className="mb-4">
    <div className="flex justify-between mb-1">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <span className="text-sm font-medium text-slate-500">
        {value}% <span className="text-xs text-slate-400">(Target: {target}%)</span>
      </span>
    </div>
    <div className="w-full bg-slate-100 rounded-full h-2.5">
      <div className={`h-2.5 rounded-full ${colorClass}`} style={{ width: `${value}%` }}></div>
    </div>
  </div>
);


const ImageComparisonSlider = ({ beforeImage, afterImage }) => {
  const [sliderPosition, setSliderPosition] = useState(50);
  const containerRef = useRef(null);

  const handleDrag = (e) => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      setSliderPosition((x / rect.width) * 100);
    }
  };

  return (
    <div 
      className="relative w-full h-[400px] rounded-xl overflow-hidden cursor-ew-resize group select-none"
      ref={containerRef}
      onMouseMove={handleDrag}
      onTouchMove={(e) => handleDrag(e.touches[0])}
    >
      <img src={afterImage} alt="After" className="absolute top-0 left-0 w-full h-full object-cover" />
      <div className="absolute top-0 left-0 h-full overflow-hidden" style={{ width: `${sliderPosition}%` }}>
        <img src={beforeImage} alt="Before" className="absolute top-0 left-0 h-full object-cover" style={{ width: containerRef.current?.offsetWidth }} />
      </div>
      <div className="absolute top-0 bottom-0 w-1 bg-white shadow-[0_0_10px_rgba(0,0,0,0.5)]" style={{ left: `${sliderPosition}%` }}>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg text-slate-600">
          <ScanLine size={16} />
        </div>
      </div>
      <div className="absolute top-4 left-4 bg-black/50 text-white px-3 py-1 rounded-full text-sm font-medium backdrop-blur-sm">Current State</div>
      <div className="absolute top-4 right-4 bg-emerald-600/80 text-white px-3 py-1 rounded-full text-sm font-medium backdrop-blur-sm">AI Proposal</div>
    </div>
  );
};


const HeatmapOverlay = ({ active }) => {
  if (!active) return null;
  return (
    <div className="absolute inset-0 z-10 opacity-60 pointer-events-none mix-blend-multiply"
      style={{
        background: `radial-gradient(circle at 20% 60%, rgba(255,0,0,0.8) 0%, rgba(255,255,0,0.5) 20%, transparent 40%), 
                     radial-gradient(circle at 70% 50%, rgba(0,255,0,0.6) 0%, transparent 30%), 
                     radial-gradient(circle at 45% 10%, rgba(255,0,0,0.6) 0%, transparent 20%)`
      }}
    />
  );
};


const ObjectBoxes = ({ active, objects }) => {
  if (!active || !objects) return null;
  return (
    <div className="absolute inset-0 z-20 pointer-events-none">
      {objects.map((obj, idx) => (
        <div 
          key={idx}
          className={`absolute border-2 flex items-start ${obj.type === 'negative' ? 'border-rose-500 bg-rose-500/10' : 'border-emerald-500 bg-emerald-500/10'}`}
          style={{ left: `${obj.x}%`, top: `${obj.y}%`, width: `${obj.width}%`, height: `${obj.height}%` }}
        >
          <span className={`text-[10px] px-1.5 py-0.5 text-white font-bold -mt-5 rounded ${obj.type === 'negative' ? 'bg-rose-500' : 'bg-emerald-500'}`}>
            {obj.label}
          </span>
        </div>
      ))}
    </div>
  );
};


// --- NEURO SCORECARD (DYNAMIC DATA) ---
const NeuroScorecard = ({ data }) => {
  const metrics = data?.neuroMetrics || FALLBACK_REPORT_DATA;

  const getIcon = (item) => {
    if (item.icon && ICON_MAP[item.icon]) return ICON_MAP[item.icon];
    return DEFAULT_ICON_MAP[item.id] || Sparkles;
  };

  const getColor = (item) => item.color || COLOR_MAP[item.id] || "bg-slate-500";

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center mb-2">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Neuro-Scorecard Analysis</h2>
          <p className="text-slate-500">Based on visual neuroscience & behavioral economics</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 transition-colors font-medium">
          <Download size={18} /> Export PDF
        </button>
      </div>

      {/* Overall Score */}
      {data?.scores?.overall && (
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 rounded-xl text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-indigo-100 text-sm font-medium">Overall Neuro-Commercial Performance</h3>
              <div className="text-4xl font-bold mt-1">{(data.scores.overall / 10).toFixed(1)} / 10</div>
            </div>
            <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
              {data.scores.overall >= 80 ? '✅ High Optimization' : data.scores.overall >= 60 ? '⚡ Moderate' : '⚠️ Needs Work'}
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {metrics.map((item) => {
          const IconComponent = getIcon(item);
          return (
            <div key={item.id} className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-lg ${getColor(item)} text-white`}>
                    <IconComponent size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800 text-lg leading-tight">{item.title}</h3>
                    <div className="text-sm font-bold text-slate-500 mt-1">{item.score} <span className="text-slate-400 font-normal">/ 10</span></div>
                  </div>
                </div>
                {item.tag && (
                  <span className="text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 px-2 py-1 rounded-full border border-emerald-100">
                    Recommendation
                  </span>
                )}
              </div>

              <div className="space-y-3">
                <div>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Key Drivers</span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {item.drivers?.map((driver, idx) => (
                      <span key={idx} className="text-xs bg-slate-50 text-slate-600 px-2 py-1 rounded border border-slate-100">{driver}</span>
                    ))}
                  </div>
                </div>
                
                <div className="grid grid-cols-1 gap-2 pt-2 border-t border-slate-50">
                  <div>
                    <span className="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 mb-0.5">
                      <Brain size={12} /> Neural Impact
                    </span>
                    <p className="text-sm text-slate-600 leading-relaxed">{item.neuralImpact}</p>
                  </div>
                  <div>
                    <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 mb-0.5">
                      <TrendingUp size={12} /> Business Effect
                    </span>
                    <p className="text-sm text-slate-600 leading-relaxed">{item.businessEffect}</p>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};


// --- MAIN APP ---
export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [appState, setAppState] = useState('idle'); 
  const [progress, setProgress] = useState(0);
  const [analysisData, setAnalysisData] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [activeOverlays, setActiveOverlays] = useState({ heatmap: false, objects: false, compare: false });
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedImage(URL.createObjectURL(file));
      setError(null);
      startAnalysis(file);
    }
  };

  const startAnalysis = async (file) => {
    setAppState('analyzing');
    setProgress(0);

    const interval = setInterval(() => {
      setProgress(prev => (prev >= 90 ? 90 : prev + 5));
    }, 200);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // 🔥 use API_BASE here
      const response = await fetch(`${API_BASE}/analyze`, {
          method: 'POST',
          body: formData,
      });

      const data = await response.json();
      if (data.error) throw new Error(data.error);
      
      clearInterval(interval);
      setProgress(100);
      setTimeout(() => {
        setAnalysisData(data);
        setAppState('complete');
      }, 500);

    } catch (error) {
      console.error("Error:", error);
      setError(error.message);
      setAppState('idle');
      clearInterval(interval);
    }
  };

  const resetAnalysis = () => {
    setAppState('idle');
    setAnalysisData(null);
    setUploadedImage(null);
    setError(null);
    setActiveTab('dashboard');
  };

  const renderContent = () => {
    if (appState === 'idle') {
      return (
        <div className="flex flex-col items-center justify-center h-[600px] border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50/50">
          <div className="w-20 h-20 bg-indigo-50 rounded-full flex items-center justify-center mb-6">
            <Upload className="w-10 h-10 text-indigo-600" />
          </div>
          <h2 className="text-2xl font-bold text-slate-800 mb-2">Upload Restaurant Scan</h2>
          <p className="text-slate-500 mb-8 text-center max-w-md">Upload an interior photo to begin Neuro-Aesthetic analysis.</p>
          
          {error && (
            <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 max-w-md text-center">
              <p className="font-medium">Error: {error}</p>
              <p className="text-sm mt-1">Make sure Python server is running on port 5000</p>
            </div>
          )}
          
          <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept="image/*" />
          <button onClick={() => fileInputRef.current.click()} className="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-lg shadow-indigo-200 transition-all transform hover:scale-105">
            Select Image & Analyze
          </button>
          <div className="mt-8 flex gap-4 text-xs text-slate-400">
            <span className="flex items-center"><CheckCircle2 size={12} className="mr-1"/> Gemini Vision</span>
            <span className="flex items-center"><CheckCircle2 size={12} className="mr-1"/> Neuro-Analysis</span>
          </div>
        </div>
      );
    }

    if (appState === 'analyzing') {
      return (
        <div className="flex flex-col items-center justify-center h-[600px]">
          <div className="w-64 h-2 bg-slate-100 rounded-full mb-8 overflow-hidden">
            <div className="h-full bg-indigo-600 rounded-full transition-all duration-100" style={{ width: `${progress}%` }} />
          </div>
          <h2 className="text-xl font-semibold text-slate-800 animate-pulse">
            {progress < 30 && "Analyzing Visual Elements..."}
            {progress >= 30 && progress < 60 && "Processing Neuro-Aesthetic Features..."}
            {progress >= 60 && progress < 90 && "Generating Business Insights..."}
            {progress >= 90 && "Finalizing Report..."}
          </h2>
        </div>
      );
    }

    if (activeTab === 'reports') {
      return <NeuroScorecard data={analysisData} />;
    }

    if (!analysisData) return null;

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCard icon={Sparkles} title="Neuro-Score" value={`${analysisData.scores?.overall || 0}/100`} subtext={analysisData.scores?.overall >= 70 ? "Well Optimized" : "Needs Optimization"} color="bg-amber-500" />
          <MetricCard icon={Clock} title="Pred. Dwell Time" value={`${analysisData.financials?.currentDwell || 0}m`} trend="up" trendValue={`+${(analysisData.financials?.predictedDwell || 0) - (analysisData.financials?.currentDwell || 0)}m`} color="bg-indigo-500" />
          <MetricCard icon={DollarSign} title="Avg. Spend" value={`$${analysisData.financials?.currentSpend || 0}`} trend="up" trendValue={`Target: $${analysisData.financials?.predictedSpend || 0}`} color="bg-emerald-500" />
          <MetricCard icon={Eye} title="Visual Clutter" value={(analysisData.scores?.clutter || 0) > 70 ? "High" : "Medium"} subtext="Cognitive Load Impact" color="bg-rose-500" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-slate-800 flex items-center gap-2"><ScanLine size={18} /> Deep Visual Analysis</h3>
                <div className="flex bg-slate-100 rounded-lg p-1">
                  <button onClick={() => setActiveOverlays({ heatmap: false, objects: false, compare: false })} className={`px-3 py-1.5 text-xs font-medium rounded-md ${!activeOverlays.heatmap && !activeOverlays.objects && !activeOverlays.compare ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}>Original</button>
                  <button onClick={() => setActiveOverlays({ heatmap: true, objects: false, compare: false })} className={`px-3 py-1.5 text-xs font-medium rounded-md ${activeOverlays.heatmap ? 'bg-white shadow text-rose-600' : 'text-slate-500'}`}>Heatmap</button>
                  <button onClick={() => setActiveOverlays({ heatmap: false, objects: true, compare: false })} className={`px-3 py-1.5 text-xs font-medium rounded-md ${activeOverlays.objects ? 'bg-white shadow text-indigo-600' : 'text-slate-500'}`}>Affordance</button>
                  <button onClick={() => setActiveOverlays({ heatmap: false, objects: false, compare: true })} className={`px-3 py-1.5 text-xs font-medium rounded-md ${activeOverlays.compare ? 'bg-white shadow text-emerald-600' : 'text-slate-500'}`}>AI Proposal</button>
                </div>
              </div>

              <div className="relative rounded-lg overflow-hidden bg-slate-900 min-h-[400px] flex items-center justify-center">
                {activeOverlays.compare ? (
                  <ImageComparisonSlider beforeImage={uploadedImage} afterImage={analysisData.idealImage} />
                ) : (
                  <>
                    <img src={uploadedImage} alt="Restaurant Interior" className="w-full h-[400px] object-cover" />
                    <HeatmapOverlay active={activeOverlays.heatmap} />
                    <ObjectBoxes active={activeOverlays.objects} objects={analysisData.objects} />
                  </>
                )}
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm">
              <h3 className="font-semibold text-slate-800 mb-4">Generative Insights & Recommendations</h3>
              <div className="space-y-3">
                {analysisData.insights?.map((insight, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 rounded-lg border border-slate-50 hover:bg-slate-50">
                    <div className={`mt-1 p-1.5 rounded-full ${insight.type === 'critical' ? 'bg-rose-100 text-rose-600' : insight.type === 'warning' ? 'bg-amber-100 text-amber-600' : 'bg-emerald-100 text-emerald-600'}`}>
                      {insight.type === 'critical' ? <AlertTriangle size={16} /> : insight.type === 'warning' ? <Info size={16} /> : <CheckCircle2 size={16} />}
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between">
                        <h4 className={`text-sm font-semibold ${insight.type === 'critical' ? 'text-rose-700' : 'text-slate-700'}`}>{insight.title}</h4>
                        <span className="text-xs font-bold bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded border border-indigo-100">{insight.impact}</span>
                      </div>
                      <p className="text-sm text-slate-500 mt-1">{insight.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700 mb-4 text-center">Current vs. Ideal Neuro-State</h3>
              <div className="h-[250px] w-full text-xs">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={analysisData.metrics}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} />
                    <Radar name="Current" dataKey="A" stroke="#8884d8" fill="#8884d8" fillOpacity={0.4} />
                    <Radar name="Target" dataKey="B" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.4} />
                    <Legend />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700 mb-4">Detailed Metrics</h3>
              <ProgressBar label="Biophilia Index" value={analysisData.scores?.biophilia || 0} target={45} colorClass="bg-emerald-500" />
              <ProgressBar label="Warmth & Coziness" value={analysisData.scores?.warmth || 0} target={80} colorClass="bg-amber-500" />
              <ProgressBar label="Social Affordance" value={analysisData.scores?.social || 0} target={75} colorClass="bg-indigo-500" />
            </div>
             
            <div className="bg-indigo-600 p-6 rounded-xl shadow-lg text-white">
              <h3 className="text-indigo-100 font-medium text-sm mb-1">Projected Monthly Uplift</h3>
              <div className="text-3xl font-bold mb-4">+${analysisData.financials?.monthlyRevenueUplift || 0}</div>
              <p className="text-xs text-indigo-200">Based on +{(analysisData.financials?.predictedDwell || 0) - (analysisData.financials?.currentDwell || 0)}min Dwell Time increase.</p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 flex">
      <aside className="w-64 bg-slate-900 text-white hidden md:flex flex-col">
        <div className="p-6 border-b border-slate-800">
          <span className="font-bold text-lg tracking-tight flex items-center gap-3"><Sparkles size={18}/> NeuroSpace.ai</span>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <button onClick={() => { setActiveTab('dashboard'); if(appState !== 'idle') setAppState('complete'); }} className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'dashboard' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}>
            <LayoutDashboard size={18} /> Dashboard
          </button>
          <button onClick={() => setActiveTab('reports')} disabled={!analysisData} className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'reports' ? 'bg-indigo-600 text-white' : analysisData ? 'text-slate-400 hover:bg-slate-800 hover:text-white' : 'text-slate-600 cursor-not-allowed'}`}>
            <FileText size={18} /> Reports
          </button>
        </nav>
      </aside>

      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm z-10">
          <span className="font-semibold text-slate-700">{analysisData ? 'Analysis Complete' : 'NeuroSpace Analysis'}</span>
          <button onClick={resetAnalysis} className="px-4 py-2 bg-slate-900 text-white text-sm rounded-lg hover:bg-slate-800">New Analysis</button>
        </header>
        <div className="flex-1 overflow-y-auto p-6">{renderContent()}</div>
      </main>
    </div>
  );
}
