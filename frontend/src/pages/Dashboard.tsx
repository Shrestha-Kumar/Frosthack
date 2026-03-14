import { useToast } from "@/hooks/use-toast";
import { AnimatePresence, motion } from "framer-motion";
import { BarChart3, CheckCircle2, FileText, Loader2, Mail, RefreshCw, Send, Users, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import Metrics from "./Metrics";

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
    const [hoveredVariant, setHoveredVariant] = useState<number | null>(null);
    const [selectedVariant, setSelectedVariant] = useState<number | null>(null);

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
            localStorage.setItem("lastThreadId", data.thread_id);
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

    // Resume existing thread if exists
    useEffect(() => {
        const id = localStorage.getItem("lastThreadId");
        if (id && state === "brief") {
            setThreadId(id);
            fetch(`${API}/campaign/${id}/state`)
                .then(res => res.json())
                .then(raw => {
                    if (raw.status === "failed") return; // Let it start fresh if failed
                    const data: CampaignState = {
                        ...raw,
                        email_variants:
                            raw?.data?.email_variants || raw?.data?.current_variants || raw?.email_variants || [],
                        segments: raw?.data?.active_segments || raw?.segments || [],
                        performance_reports: raw?.data?.performance_reports || raw?.performance_reports || [],
                        optimization_history: raw?.data?.optimization_history || raw?.optimization_history || [],
                        iteration_count: raw?.iteration_count ?? 0,
                    };
                    setCampaignData(data);
                    if (data.iteration_count !== undefined && data.iteration_count > 0) {
                        setIteration(data.iteration_count);
                    }

                    if (data.status === "awaiting_approval") setState("approval");
                    else if (data.status === "completed" || data.status === "executed") setState("analytics");
                    else if (data.status === "running") setState("polling");
                    else if (data.status === "executing") setState("approved-polling");
                })
                .catch(console.error);
        }
    }, []);

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
                    email_variants:
                        raw?.data?.email_variants || raw?.data?.current_variants || raw?.email_variants || [],
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
                        <motion.div key="brief" {...pageVariants} className="max-w-4xl mx-auto">
                            <div className="text-center mb-8">
                                <h2 className="text-3xl font-bold text-foreground mb-2">Campaign Brief</h2>
                                <p className="text-muted-foreground text-lg">
                                    Describe your BFSI marketing campaign and let the AI take over.
                                </p>
                            </div>
                            <div className="glass rounded-2xl p-8">
                                <textarea
                                    value={brief}
                                    onChange={e => setBrief(e.target.value)}
                                    placeholder="e.g. Launch a credit card rewards campaign targeting millennials with high spending habits..."
                                    rows={12}
                                    className="w-full bg-secondary/40 border border-border/50 rounded-xl p-6 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y text-lg font-medium font-sans leading-relaxed shadow-inner"
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
                        <motion.div key="approval" {...pageVariants} className="w-full max-w-7xl mx-auto">
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

                            <div className="flex flex-col lg:flex-row gap-8 mb-8">
                                {/* Left Side: Squares Grid */}
                                <div className="flex-1">
                                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-2 gap-6">
                                        {(campaignData.email_variants || []).map((variant, i) => {
                                            const seg = campaignData.segments?.find(
                                                s => s.segment_id === variant.segment_id,
                                            );
                                            const isSelected = selectedVariant === i;
                                            const isHovered = hoveredVariant === i;
                                            const isActive = isSelected || (selectedVariant === null && isHovered);

                                            return (
                                                <div
                                                    key={i}
                                                    onMouseEnter={() => setHoveredVariant(i)}
                                                    onMouseLeave={() => setHoveredVariant(null)}
                                                    onClick={() => setSelectedVariant(isSelected ? null : i)}
                                                    className={`glass rounded-2xl overflow-hidden flex flex-col min-h-[320px] cursor-pointer transition-all duration-200 border-2 ${
                                                        isActive
                                                            ? "border-primary ring-2 ring-primary/20 scale-[1.02] shadow-lg shadow-primary/10"
                                                            : "border-border/50 hover:border-primary/50 hover:scale-[1.01]"
                                                    }`}
                                                >
                                                    <div className="p-5 border-b border-border/50 bg-card/60 shrink-0">
                                                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                                                            <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest bg-secondary/70 px-2 py-1 rounded">
                                                                {variant.variant_id ||
                                                                    `Variant ${String.fromCharCode(65 + i)}`}
                                                            </span>
                                                            {variant.tone && (
                                                                <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-accent/20 text-accent ring-1 ring-accent/30 shadow-inner max-w-fit leading-none">
                                                                    {variant.tone}
                                                                </span>
                                                            )}
                                                        </div>
                                                        {seg && (
                                                            <p className="text-sm text-primary/90 mb-2.5 flex items-start gap-1.5 font-medium leading-tight">
                                                                <Users className="h-4 w-4 shrink-0 mt-0.5" />
                                                                <span className="line-clamp-2">{seg.name}</span>
                                                            </p>
                                                        )}
                                                        <h4
                                                            className="font-bold text-foreground text-base line-clamp-2 leading-snug"
                                                            title={variant.subject}
                                                        >
                                                            {variant.subject}
                                                        </h4>
                                                    </div>
                                                    <div className="p-5 bg-secondary/10 flex-1 overflow-hidden relative">
                                                        <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-background via-background/80 to-transparent pointer-events-none" />
                                                        <div
                                                            className="prose prose-sm prose-invert max-w-none text-sm text-muted-foreground line-clamp-4 font-sans leading-relaxed"
                                                            dangerouslySetInnerHTML={{
                                                                __html: variant.body_html.replace(
                                                                    /<a /g,
                                                                    '<a target="_blank" rel="noopener noreferrer" ',
                                                                ),
                                                            }}
                                                        />
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                {/* Right Side: Fixed Preview Window */}
                                <div className="w-full lg:w-[450px] xl:w-[500px] shrink-0">
                                    <div className="sticky top-24 glass rounded-3xl overflow-hidden flex flex-col h-[650px] shadow-2xl border border-primary/20 bg-background/95 backdrop-blur-xl">
                                        <div className="p-4 bg-secondary/30 border-b border-border text-center flex items-center justify-between">
                                            <h3 className="font-bold text-lg text-foreground flex items-center gap-2">
                                                <Mail className="h-5 w-5 text-primary" />
                                                Email Preview
                                            </h3>
                                            {(selectedVariant !== null || hoveredVariant !== null) && (
                                                <span className="text-xs font-medium text-muted-foreground px-2 py-1 rounded bg-secondary/50">
                                                    {selectedVariant !== null ? "Pinned" : "Previewing"}
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
                                            {(() => {
                                                const displayIndex =
                                                    selectedVariant !== null ? selectedVariant : hoveredVariant;
                                                if (
                                                    displayIndex === null ||
                                                    !campaignData.email_variants ||
                                                    !campaignData.email_variants[displayIndex]
                                                ) {
                                                    return (
                                                        <div className="h-full flex flex-col items-center justify-center text-muted-foreground space-y-4 opacity-50 transition-opacity hover:opacity-100">
                                                            <div className="p-4 bg-secondary/20 rounded-full">
                                                                <Mail className="h-16 w-16 mb-2 text-primary/60" />
                                                            </div>
                                                            <p className="text-xl font-bold tracking-tight text-foreground">
                                                                Hover over a card to peek
                                                            </p>
                                                            <p className="text-sm font-medium">
                                                                Click a card to lock the preview
                                                            </p>
                                                        </div>
                                                    );
                                                }
                                                const variant = campaignData.email_variants[displayIndex];
                                                const seg = campaignData.segments?.find(
                                                    s => s.segment_id === variant.segment_id,
                                                );

                                                return (
                                                    <div className="space-y-6 animate-in fade-in zoom-in-95 duration-200">
                                                        <div className="space-y-4 pb-6 border-b border-border/40">
                                                            <div className="flex items-center justify-between gap-4">
                                                                <div className="space-y-1">
                                                                    <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest bg-secondary/50 px-2 py-1 rounded-md">
                                                                        {variant.variant_id ||
                                                                            `Variant ${String.fromCharCode(65 + displayIndex)}`}
                                                                    </span>
                                                                    {seg && (
                                                                        <div className="text-sm text-primary flex items-center gap-2 font-medium mt-2">
                                                                            <Users className="h-4 w-4" />
                                                                            {seg.name}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                                {variant.tone && (
                                                                    <div className="px-3 py-1.5 rounded-full text-xs font-bold bg-accent/20 text-accent ring-1 ring-accent/30 shadow-inner">
                                                                        {variant.tone}
                                                                    </div>
                                                                )}
                                                            </div>
                                                            <div>
                                                                <p className="text-xs text-muted-foreground mb-1 font-semibold uppercase">
                                                                    Subject Line
                                                                </p>
                                                                <h4 className="text-xl font-bold text-foreground leading-snug">
                                                                    {variant.subject}
                                                                </h4>
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs text-muted-foreground mb-3 font-semibold uppercase">
                                                                Body Content
                                                            </p>
                                                            <div
                                                                className="prose prose-base prose-invert max-w-none text-foreground leading-relaxed font-sans bg-secondary/10 p-5 rounded-2xl border border-secondary/30"
                                                                dangerouslySetInnerHTML={{
                                                                    __html: variant.body_html.replace(
                                                                        /<a /g,
                                                                        '<a target="_blank" rel="noopener noreferrer" ',
                                                                    ),
                                                                }}
                                                            />
                                                        </div>
                                                    </div>
                                                );
                                            })()}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Actions Container */}
                            <div className="glass p-6 rounded-3xl mx-auto shadow-xl border-t border-primary/20 bg-background/50 backdrop-blur-md mt-6">
                                <div className="flex flex-col md:flex-row gap-6 items-stretch">
                                    <button
                                        onClick={approve}
                                        disabled={loading}
                                        className="flex-1 flex items-center justify-center gap-3 px-8 py-5 rounded-2xl bg-accent text-accent-foreground font-extrabold text-lg shadow-lg hover:shadow-accent/25 hover:-translate-y-0.5 transition-all active:scale-[0.98] disabled:opacity-50 glow-accent"
                                    >
                                        {loading ? (
                                            <Loader2 className="h-6 w-6 animate-spin" />
                                        ) : (
                                            <CheckCircle2 className="h-6 w-6" />
                                        )}
                                        Approve & Launch Campaign
                                    </button>

                                    <div className="flex-[1.5] flex flex-col sm:flex-row gap-4">
                                        <div className="flex-1 relative">
                                            <textarea
                                                placeholder="Need changes? Provide feedback for the AI to regenerate..."
                                                value={feedback}
                                                onChange={e => setFeedback(e.target.value)}
                                                rows={2}
                                                className="w-full h-full bg-secondary/30 border border-border/50 rounded-2xl px-5 py-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-destructive/50 resize-none font-medium transition-colors hover:bg-secondary/40"
                                            />
                                        </div>
                                        <button
                                            onClick={reject}
                                            disabled={loading || !feedback.trim()}
                                            className="sm:w-48 flex flex-col items-center justify-center gap-2 px-4 py-4 rounded-2xl border-2 border-destructive/40 text-destructive font-bold text-sm transition-all hover:bg-destructive/10 hover:border-destructive/60 hover:-translate-y-0.5 active:scale-[0.98] disabled:opacity-50 disabled:hover:translate-y-0 shadow-sm"
                                        >
                                            <XCircle className="h-5 w-5 mb-1" />
                                            Reject & Retry
                                        </button>
                                    </div>
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
                            <Metrics
                                data={campaignData}
                                onRestart={() => {
                                    setState("brief");
                                    setBrief("");
                                    setCampaignData(null);
                                    setThreadId("");
                                    setIteration(1);
                                }}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default Dashboard;
