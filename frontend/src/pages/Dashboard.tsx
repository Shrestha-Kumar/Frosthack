import { useToast } from "@/hooks/use-toast";
import { AnimatePresence, motion } from "framer-motion";
import {
    Activity,
    BarChart3,
    Brain,
    CheckCircle2,
    FileText,
    Loader2,
    Mail,
    RefreshCw,
    Send,
    Sparkles,
    TrendingUp,
    Users,
    XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const API = "http://localhost:8000";

type DashState = "brief" | "polling" | "approval" | "approved-polling" | "analytics";

interface EmailVariant {
    variant_id?: string;
    segment_id?: string;
    subject: string;
    tone?: string;
    body_html: string;
}

interface PerformanceReport {
    variant_id?: string;
    segment_id?: string;
    open_rate?: number;
    click_rate?: number;
    composite_score?: number;
}

interface Segment {
    segment_id: string;
    name: string;
    customer_ids?: string[];
}

interface OptimizationEntry {
    insight?: string;
    action_taken?: string;
    timestamp?: string;
    iteration?: number;
    winning_tones?: string[];
    losing_tones?: string[];
    winning_elements?: string[];
}

interface CampaignState {
    status: string;
    iteration_count?: number;
    email_variants?: EmailVariant[];
    segments?: Segment[];
    performance_reports?: PerformanceReport[];
    optimization_history?: OptimizationEntry[];
}

const SkeletonCard = () => (
    <div className="glass rounded-2xl p-6 space-y-4 animate-pulse">
        <div className="h-4 bg-muted rounded w-3/4" />
        <div className="h-3 bg-muted rounded w-1/2" />
        <div className="h-20 bg-muted rounded" />
    </div>
);

const Dashboard = () => {
    const { toast } = useToast();
    const [state, setState] = useState<DashState>("brief");
    const [brief, setBrief] = useState("");
    const [threadId, setThreadId] = useState("");
    const [campaignData, setCampaignData] = useState<CampaignState | null>(null);
    const [feedback, setFeedback] = useState("");
    const [loading, setLoading] = useState(false);
    const [iteration, setIteration] = useState(1);

    const showError = useCallback(
        (msg: string) => {
            toast({ title: "Error", description: msg, variant: "destructive" });
        },
        [toast],
    );

    const startCampaign = async () => {
        if (!brief.trim()) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/campaign/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ brief }),
            });
            if (!res.ok) throw new Error("Failed to start campaign");
            const data = await res.json();
            setThreadId(data.thread_id);
            setState("polling");
        } catch {
            showError("Could not reach the AI backend. Is the server running?");
        } finally {
            setLoading(false);
        }
    };

    const approve = async () => {
        setLoading(true);
        try {
            await fetch(`${API}/campaign/${threadId}/approve`, { method: "POST" });
            setState("approved-polling");
        } catch {
            showError("Failed to approve campaign.");
        } finally {
            setLoading(false);
        }
    };

    const reject = async () => {
        if (!feedback.trim()) return;
        setLoading(true);
        try {
            await fetch(`${API}/campaign/${threadId}/reject`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ feedback }),
            });
            setState("polling");
            setFeedback("");
        } catch {
            showError("Failed to reject campaign.");
        } finally {
            setLoading(false);
        }
    };

    // Polling
    useEffect(() => {
        if (state !== "polling" && state !== "approved-polling") return;
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`${API}/campaign/${threadId}/state`);
                if (!res.ok) return;
                const raw = await res.json();
                const data: CampaignState = {
                    ...raw,
                    email_variants: raw?.data?.current_variants || raw?.email_variants || [],
                    segments: raw?.data?.active_segments || raw?.segments || [],
                    performance_reports: raw?.data?.performance_reports || raw?.performance_reports || [],
                    optimization_history: raw?.data?.optimization_history || raw?.optimization_history || [],
                    iteration_count: raw?.iteration_count ?? 0,
                };
                setCampaignData(data);
                if (data.status === "awaiting_approval" && (state === "polling" || state === "approved-polling")) {
                    setState("approval");
                    if (data.iteration_count !== undefined) setIteration(data.iteration_count + 1);
                }
                if (data.status === "completed" || data.status === "executed") {
                    setState("analytics");
                }
            } catch {
                /* keep polling */
            }
        }, 3000);
        return () => clearInterval(interval);
    }, [state, threadId]);

    const pageVariants = {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0, transition: { duration: 0.5 } },
        exit: { opacity: 0, y: -20, transition: { duration: 0.3 } },
    };

    return (
        <div className="min-h-[85vh] py-12">
            <div className="container max-w-5xl">
                {/* Iteration badge */}
                {state !== "brief" && (
                    <div className="flex justify-center mb-4">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                            <RefreshCw className="h-3 w-3" />
                            Iteration: {iteration}
                        </span>
                    </div>
                )}

                {/* Steps indicator */}
                <div className="flex items-center justify-center gap-3 mb-12">
                    {[
                        { label: "Brief", icon: FileText, active: state === "brief" },
                        { label: "Review", icon: Mail, active: state === "approval" || state === "polling" },
                        {
                            label: "Analytics",
                            icon: BarChart3,
                            active: state === "analytics" || state === "approved-polling",
                        },
                    ].map((step, i) => (
                        <div key={step.label} className="flex items-center gap-3">
                            {i > 0 && (
                                <div
                                    className={`w-12 h-px ${step.active || state === "analytics" ? "bg-primary" : "bg-border"}`}
                                />
                            )}
                            <div
                                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                                    step.active
                                        ? "bg-primary/10 text-primary border border-primary/30"
                                        : "text-muted-foreground border border-border/50"
                                }`}
                            >
                                <step.icon className="h-4 w-4" />
                                {step.label}
                            </div>
                        </div>
                    ))}
                </div>

                <AnimatePresence mode="wait">
                    {/* STATE A: Brief Input */}
                    {state === "brief" && (
                        <motion.div key="brief" {...pageVariants} className="max-w-2xl mx-auto">
                            <div className="text-center mb-8">
                                <h2 className="text-3xl font-bold text-foreground mb-2">Campaign Brief</h2>
                                <p className="text-muted-foreground">
                                    Describe your BFSI marketing campaign and let the AI take over.
                                </p>
                            </div>
                            <div className="glass rounded-2xl p-8">
                                <textarea
                                    value={brief}
                                    onChange={e => setBrief(e.target.value)}
                                    placeholder="e.g. Launch a credit card rewards campaign targeting millennials with high spending habits..."
                                    rows={6}
                                    className="w-full bg-secondary/50 border border-border/50 rounded-xl p-4 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none text-sm leading-relaxed"
                                />
                                <button
                                    onClick={startCampaign}
                                    disabled={loading || !brief.trim()}
                                    className="mt-4 w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-primary text-primary-foreground font-semibold transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:pointer-events-none glow-primary-sm"
                                >
                                    {loading ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                        <Send className="h-4 w-4" />
                                    )}
                                    Generate Campaign
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {/* Polling state (AI Working) */}
                    {state === "polling" && (
                        <motion.div key="polling" {...pageVariants} className="max-w-2xl mx-auto">
                            <div className="text-center mb-8">
                                <h2 className="text-3xl font-bold text-foreground mb-2">AI is Working</h2>
                                <p className="text-muted-foreground">
                                    Generating segments, crafting emails, and optimizing variants...
                                </p>
                            </div>
                            <div className="grid gap-4">
                                <SkeletonCard />
                                <SkeletonCard />
                            </div>
                            <div className="flex flex-col items-center justify-center gap-4 mt-8">
                                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                <p className="text-sm text-muted-foreground animate-pulse">
                                    AI Agents are analyzing the brief and generating variants...
                                </p>
                            </div>
                        </motion.div>
                    )}

                    {/* STATE B: HITL Approval */}
                    {state === "approval" && campaignData && (
                        <motion.div key="approval" {...pageVariants}>
                            <div className="text-center mb-8">
                                <h2 className="text-3xl font-bold text-foreground mb-2">Review & Approve</h2>
                                <p className="text-muted-foreground">
                                    The AI has generated the following campaign variants for your review.
                                </p>
                            </div>

                            {/* Segments */}
                            {campaignData.segments && campaignData.segments.length > 0 && (
                                <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
                                    <Users className="h-4 w-4 text-primary" />
                                    {campaignData.segments.map(seg => (
                                        <span
                                            key={seg.segment_id}
                                            className="px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary border border-primary/20"
                                        >
                                            {seg.name} ({seg.customer_ids?.length ?? 0})
                                        </span>
                                    ))}
                                </div>
                            )}

                            {/* Email variants */}
                            <div className="grid md:grid-cols-2 gap-6 mb-8">
                                {(campaignData.email_variants || []).map((variant, i) => {
                                    const seg = campaignData.segments?.find(s => s.segment_id === variant.segment_id);
                                    return (
                                    <div key={i} className="glass rounded-2xl overflow-hidden">
                                        <div className="p-5 border-b border-border/50">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                                    {variant.variant_id || `Variant ${String.fromCharCode(65 + i)}`}
                                                </span>
                                                {variant.tone && (
                                                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-accent/10 text-accent">
                                                        {variant.tone}
                                                    </span>
                                                )}
                                            </div>
                                            {seg && (
                                                <p className="text-xs text-primary/70 mb-1 flex items-center gap-1">
                                                    <Users className="h-3 w-3" />
                                                    {seg.name}
                                                </p>
                                            )}
                                            <h4 className="font-semibold text-foreground">{variant.subject}</h4>
                                        </div>
                                        <div className="p-5 bg-secondary/20">
                                            <div
                                                className="prose prose-sm prose-invert max-w-none text-sm text-muted-foreground"
                                                dangerouslySetInnerHTML={{ __html: variant.body_html }}
                                            />
                                        </div>
                                    </div>
                                    );
                                })}
                            </div>

                            {/* Actions */}
                            <div className="flex flex-col sm:flex-row gap-4 max-w-xl mx-auto">
                                <button
                                    onClick={approve}
                                    disabled={loading}
                                    className="flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-xl bg-accent text-accent-foreground font-bold text-base transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 glow-accent"
                                >
                                    {loading ? (
                                        <Loader2 className="h-5 w-5 animate-spin" />
                                    ) : (
                                        <CheckCircle2 className="h-5 w-5" />
                                    )}
                                    Approve & Execute
                                </button>
                                <div className="flex-1 space-y-2">
                                    <input
                                        type="text"
                                        placeholder="Feedback for regeneration..."
                                        value={feedback}
                                        onChange={e => setFeedback(e.target.value)}
                                        className="w-full bg-secondary/50 border border-border/50 rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-destructive/50"
                                    />
                                    <button
                                        onClick={reject}
                                        disabled={loading || !feedback.trim()}
                                        className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-destructive/30 text-destructive font-semibold text-sm transition-all hover:bg-destructive/10 disabled:opacity-50"
                                    >
                                        <XCircle className="h-4 w-4" />
                                        Reject & Regenerate
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Approved polling */}
                    {state === "approved-polling" && (
                        <motion.div key="approved-polling" {...pageVariants} className="max-w-2xl mx-auto text-center">
                            <div className="mb-8">
                                <h2 className="text-3xl font-bold text-foreground mb-2">Executing Campaign</h2>
                                <p className="text-muted-foreground">
                                    Running A/B tests and gathering performance data...
                                </p>
                            </div>
                            <div className="inline-flex flex-col items-center gap-4">
                                <div className="inline-flex items-center gap-3 px-6 py-3 rounded-full glass text-sm text-primary font-medium">
                                    <RefreshCw className="h-4 w-4 animate-spin" />
                                    Waiting for results...
                                </div>
                                <p className="text-xs text-muted-foreground animate-pulse">
                                    Unleashing execution agents and collecting real-time metrics...
                                </p>
                            </div>
                        </motion.div>
                    )}

                    {/* STATE C: Analytics */}
                    {state === "analytics" && campaignData && (
                        <motion.div key="analytics" {...pageVariants}>
                            <div className="text-center mb-10">
                                <h2 className="text-3xl font-bold text-foreground mb-2">Campaign Performance</h2>
                                <p className="text-muted-foreground">
                                    A/B test results and AI-driven optimization insights.
                                </p>
                            </div>

                            {/* Optimization Trajectory Chart */}
                            {campaignData.optimization_history && campaignData.optimization_history.length > 0 && (
                                <div className="p-8 mb-8 border rounded-2xl border-white/10 bg-card/50 glass gradient-border">
                                    <h3 className="mb-6 text-lg font-semibold text-white flex items-center gap-2">
                                        <TrendingUp className="h-5 w-5 text-primary" />
                                        Optimization Trajectory (Thompson Sampling)
                                    </h3>
                                    <div className="h-[300px] w-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart
                                                data={campaignData.optimization_history.map((h, i) => {
                                                    // Compute actual avg composite from performance reports for this iteration's data
                                                    // Each optimization_history entry corresponds to one iteration
                                                    const iterNum = h.iteration ?? i;
                                                    // Get all reports — use the best composite per iteration as a proxy
                                                    const allReports = campaignData.performance_reports || [];
                                                    // Use average composite score across all reports as a fallback metric
                                                    const avgComposite = allReports.length > 0
                                                        ? allReports.reduce((sum, r) => sum + (r.composite_score || 0), 0) / allReports.length
                                                        : 0;
                                                    return {
                                                        iteration: `Iter ${iterNum + 1}`,
                                                        composite: Number(avgComposite.toFixed(4)),
                                                    };
                                                })}
                                            >
                                                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                                <XAxis
                                                    dataKey="iteration"
                                                    stroke="#888"
                                                    fontSize={12}
                                                    tickLine={false}
                                                    axisLine={false}
                                                />
                                                <YAxis
                                                    stroke="#888"
                                                    fontSize={12}
                                                    tickLine={false}
                                                    axisLine={false}
                                                    domain={[0, 1]}
                                                />
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: "#111",
                                                        borderColor: "#333",
                                                        borderRadius: "12px",
                                                    }}
                                                    itemStyle={{ color: "#fff" }}
                                                />
                                                <Line
                                                    type="monotone"
                                                    dataKey="composite"
                                                    name="Avg Score"
                                                    stroke="#3b82f6"
                                                    strokeWidth={3}
                                                    dot={{ r: 5, fill: "#3b82f6", strokeWidth: 0 }}
                                                    activeDot={{ r: 8, fill: "#60a5fa" }}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                            )}

                            {/* Metrics Empty State */}
                            {(!campaignData.performance_reports || campaignData.performance_reports.length === 0) && (
                                <div className="flex flex-col items-center justify-center p-16 text-center border border-dashed rounded-2xl border-white/10 bg-black/20 mb-8">
                                    <Activity className="w-12 h-12 mb-4 opacity-50 text-muted-foreground" />
                                    <h3 className="text-xl font-medium text-white">No Metrics Available Yet</h3>
                                    <p className="max-w-md mt-2 text-sm text-muted-foreground">
                                        Metrics will populate once the execution cycle completes. Thompson sampling
                                        updates real-time.
                                    </p>
                                </div>
                            )}

                            {/* Metrics Cards — Grouped by Segment */}
                            {campaignData.performance_reports && campaignData.performance_reports.length > 0 && (
                                <div className="space-y-6 mb-8">
                                    {Object.entries(
                                        (campaignData.performance_reports || []).reduce<Record<string, PerformanceReport[]>>((acc, r) => {
                                            const key = r.segment_id || "unknown";
                                            (acc[key] = acc[key] || []).push(r);
                                            return acc;
                                        }, {})
                                    ).map(([segId, reports]) => {
                                        const segName = campaignData.segments?.find(s => s.segment_id === segId)?.name || segId;
                                        const bestReport = reports.reduce((a, b) => ((a.composite_score || 0) >= (b.composite_score || 0) ? a : b));
                                        return (
                                            <div key={segId}>
                                                <h4 className="text-sm font-semibold text-primary mb-3 flex items-center gap-2">
                                                    <Users className="h-4 w-4" />
                                                    {segName}
                                                </h4>
                                                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                                    {reports.map((report, i) => {
                                                        const isWinner = report === bestReport && reports.length > 1;
                                                        return (
                                                        <div key={i} className={`glass rounded-2xl p-6 gradient-border ${isWinner ? "ring-1 ring-accent/50" : ""}`}>
                                                            <div className="flex items-center justify-between mb-4">
                                                                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                                                    {report.variant_id || `Variant ${String.fromCharCode(65 + i)}`}
                                                                </span>
                                                                {isWinner && (
                                                                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-accent/20 text-accent">
                                                                        Winner
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <div className="space-y-4">
                                                                <div>
                                                                    <div className="flex items-center justify-between text-sm mb-1">
                                                                        <span className="text-muted-foreground">Open Rate</span>
                                                                        <span className="font-semibold text-foreground">
                                                                            {((report.open_rate || 0) * 100).toFixed(1)}%
                                                                        </span>
                                                                    </div>
                                                                    <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                                                                        <div
                                                                            className="h-full bg-primary rounded-full"
                                                                            style={{ width: `${(report.open_rate || 0) * 100}%` }}
                                                                        />
                                                                    </div>
                                                                </div>
                                                                <div>
                                                                    <div className="flex items-center justify-between text-sm mb-1">
                                                                        <span className="text-muted-foreground">Click Rate</span>
                                                                        <span className="font-semibold text-foreground">
                                                                            {((report.click_rate || 0) * 100).toFixed(1)}%
                                                                        </span>
                                                                    </div>
                                                                    <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                                                                        <div
                                                                            className="h-full bg-accent rounded-full"
                                                                            style={{ width: `${(report.click_rate || 0) * 100}%` }}
                                                                        />
                                                                    </div>
                                                                </div>
                                                                <div className="pt-2 border-t border-border/50 flex items-center justify-between">
                                                                    <span className="text-sm text-muted-foreground">
                                                                        Composite Score
                                                                    </span>
                                                                    <span className="text-xl font-bold text-gradient">
                                                                        {((report.composite_score || 0) * 100).toFixed(1)}
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {/* AI Reasoning */}
                            {campaignData.optimization_history && campaignData.optimization_history.length > 0 && (
                                <div className="glass rounded-2xl p-8 gradient-border">
                                    <div className="flex items-center gap-3 mb-6">
                                        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary/10 text-primary">
                                            <Brain className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-foreground">AI Reasoning</h3>
                                            <p className="text-xs text-muted-foreground">
                                                Strategic optimization insights
                                            </p>
                                        </div>
                                    </div>
                                    <div className="space-y-4">
                                        {campaignData.optimization_history.map((entry, i) => (
                                            <div
                                                key={i}
                                                className="flex gap-4 p-4 rounded-xl bg-secondary/30 border border-border/30"
                                            >
                                                <div className="flex-shrink-0 mt-0.5">
                                                    <TrendingUp className="h-4 w-4 text-accent" />
                                                </div>
                                                <div className="space-y-2 flex-1">
                                                    {entry.action_taken && (
                                                        <p className="text-sm font-medium text-foreground">
                                                            Iteration {(entry.iteration ?? i) + 1}: {entry.action_taken}
                                                        </p>
                                                    )}
                                                    {entry.insight && (
                                                        <p className="text-sm text-muted-foreground">{entry.insight}</p>
                                                    )}
                                                    {/* Structured optimization data */}
                                                    <div className="flex flex-wrap gap-1.5 mt-1">
                                                        {(entry.winning_tones || []).map(t => (
                                                            <span key={`w-${t}`} className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-accent/15 text-accent border border-accent/20">
                                                                <CheckCircle2 className="h-2.5 w-2.5 mr-1" /> {t}
                                                            </span>
                                                        ))}
                                                        {(entry.losing_tones || []).map(t => (
                                                            <span key={`l-${t}`} className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-destructive/15 text-destructive border border-destructive/20">
                                                                <XCircle className="h-2.5 w-2.5 mr-1" /> {t}
                                                            </span>
                                                        ))}
                                                    </div>
                                                    {(entry.winning_elements || []).length > 0 && (
                                                        <p className="text-xs text-muted-foreground/70 mt-1">
                                                            Key elements: {entry.winning_elements?.join(", ")}
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* New campaign */}
                            <div className="text-center mt-10">
                                <button
                                    onClick={() => {
                                        setState("brief");
                                        setBrief("");
                                        setCampaignData(null);
                                        setThreadId("");
                                        setIteration(1);
                                    }}
                                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl border border-border/50 text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors text-sm font-medium"
                                >
                                    <Sparkles className="h-4 w-4" />
                                    Start New Campaign
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default Dashboard;
1