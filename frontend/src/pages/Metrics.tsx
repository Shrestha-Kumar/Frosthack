import { Button } from "@/components/ui/button";
import { Dialog, DialogClose, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
    Activity,
    BarChart3,
    Brain,
    CheckCircle2,
    RefreshCw,
    Sparkles,
    TrendingUp,
    Users,
    XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const API = "http://localhost:8000";

interface MetricsProps {
    data?: any;
    onRestart?: () => void;
}

const Metrics = ({ data: propData, onRestart }: MetricsProps) => {
    const [fetchedData, setFetchedData] = useState<any>(null);
    const [loading, setLoading] = useState(!propData);
    const [error, setError] = useState<string | null>(null);
    const [selectedVariantForModal, setSelectedVariantForModal] = useState<string | null>(null);

    useEffect(() => {
        if (propData) {
            setFetchedData(propData);
            setLoading(false);
            return;
        }

        const id = localStorage.getItem("lastThreadId");
        if (!id) {
            setError("No recent campaign found. Open the dashboard and run a campaign first.");
            setLoading(false);
            return;
        }
        (async () => {
            try {
                const res = await fetch(`${API}/campaign/${id}/state`);
                if (!res.ok) throw new Error("Failed to fetch campaign state");
                const raw = await res.json();
                setFetchedData({
                    ...raw,
                    segments: raw?.data?.segments || raw?.segments || [],
                    email_variants:
                        raw?.data?.email_variants || raw?.data?.current_variants || raw?.email_variants || [],
                    performance_reports: raw?.data?.performance_reports || raw?.performance_reports || [],
                    optimization_history: raw?.data?.optimization_history || raw?.optimization_history || [],
                });
            } catch (e: any) {
                setError(e.message || "Unknown error");
            } finally {
                setLoading(false);
            }
        })();
    }, [propData]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
                <RefreshCw className="h-8 w-8 text-primary animate-spin" />
                <p className="text-muted-foreground animate-pulse">Loading campaign metrics...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center p-16 text-center border border-dashed rounded-2xl border-destructive/30 bg-destructive/10">
                <XCircle className="w-12 h-12 mb-4 opacity-50 text-destructive" />
                <h3 className="text-xl font-medium text-destructive">Error Loading Metrics</h3>
                <p className="max-w-md mt-2 text-sm text-muted-foreground">{error}</p>
            </div>
        );
    }

    const campaignData = propData || fetchedData;
    const selectedVariant = selectedVariantForModal
        ? campaignData?.email_variants?.find((v: any) => v.variant_id === selectedVariantForModal)
        : null;

    return (
        <div className="w-full">
            <Dialog open={!!selectedVariantForModal} onOpenChange={open => !open && setSelectedVariantForModal(null)}>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col bg-background/95 backdrop-blur-xl border-primary/20">
                    <DialogHeader className="shrink-0 mb-4 pb-4 border-b border-border/50">
                        <DialogTitle className="text-xl font-bold flex items-center gap-2">
                            <span className="bg-secondary/50 px-2 py-1 rounded text-xs tracking-widest uppercase text-muted-foreground">
                                {selectedVariant?.variant_id}
                            </span>
                            {selectedVariant?.subject}
                        </DialogTitle>
                    </DialogHeader>
                    {selectedVariant && (
                        <div className="flex-1 overflow-y-auto no-scrollbar pb-4">
                            <div
                                className="prose prose-sm prose-invert max-w-none text-foreground font-sans leading-relaxed bg-secondary/10 p-5 rounded-2xl border border-secondary/30"
                                dangerouslySetInnerHTML={{
                                    __html: selectedVariant.body_html.replace(
                                        /<a /g,
                                        '<a target="_blank" rel="noopener noreferrer" ',
                                    ),
                                }}
                            />
                        </div>
                    )}
                    <div className="pt-4 border-t border-border/50 flex justify-end shrink-0 mt-auto">
                        <DialogClose asChild>
                            <Button variant="outline" className="font-semibold px-8 cursor-pointer">
                                Close Preview
                            </Button>
                        </DialogClose>
                    </div>
                </DialogContent>
            </Dialog>

            <div className="text-center mb-10">
                <h2 className="text-3xl font-bold text-foreground mb-2 flex items-center justify-center gap-3">
                    <BarChart3 className="h-8 w-8 text-primary" />
                    Campaign Performance
                </h2>
                <p className="text-muted-foreground">A/B test results and AI-driven optimization insights.</p>
            </div>

            {/* Optimization Trajectory Chart */}
            {campaignData?.optimization_history && campaignData.optimization_history.length > 0 && (
                <div className="p-8 mb-8 border rounded-2xl border-white/10 bg-card/50 glass gradient-border shadow-xl">
                    <h3 className="mb-6 text-xl font-bold text-white flex items-center gap-2">
                        <TrendingUp className="h-6 w-6 text-primary" />
                        Optimization Trajectory (Thompson Sampling)
                    </h3>
                    <div className="h-[350px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart
                                data={campaignData.optimization_history.map((h: any, i: number) => {
                                    const iterNum = h.iteration ?? i;
                                    const allReports = campaignData.performance_reports || [];
                                    const avgComposite =
                                        allReports.length > 0
                                            ? allReports.reduce(
                                                  (sum: number, r: any) => sum + (r.composite_score || 0),
                                                  0,
                                              ) / allReports.length
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
                                <YAxis stroke="#888" fontSize={12} tickLine={false} axisLine={false} domain={[0, 1]} />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: "#111",
                                        borderColor: "#333",
                                        borderRadius: "12px",
                                        boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
                                    }}
                                    itemStyle={{ color: "#fff", fontWeight: "bold" }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="composite"
                                    name="Avg Score"
                                    stroke="#3b82f6"
                                    strokeWidth={4}
                                    dot={{ r: 6, fill: "#3b82f6", strokeWidth: 0 }}
                                    activeDot={{ r: 9, fill: "#60a5fa", strokeWidth: 2, stroke: "#fff" }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            {/* Metrics Empty State */}
            {(!campaignData?.performance_reports || campaignData.performance_reports.length === 0) && (
                <div className="flex flex-col items-center justify-center p-16 text-center border border-dashed rounded-2xl border-white/10 bg-black/20 mb-8 mx-auto max-w-2xl shadow-inner">
                    <Activity className="w-16 h-16 mb-4 opacity-50 text-muted-foreground animate-pulse" />
                    <h3 className="text-2xl font-bold text-white">No Metrics Available Yet</h3>
                    <p className="mt-3 text-base text-muted-foreground">
                        Metrics will populate once the execution cycle completes. Real-time insights will appear here.
                    </p>
                </div>
            )}

            {/* Metrics Cards — Grouped by Segment */}
            {campaignData?.performance_reports && campaignData.performance_reports.length > 0 && (
                <div className="space-y-8 mb-10">
                    {Object.entries(
                        (campaignData.performance_reports || []).reduce((acc: any, r: any) => {
                            const key = r.segment_id || "unknown";
                            (acc[key] = acc[key] || []).push(r);
                            return acc;
                        }, {}),
                    ).map(([segId, reports]: [string, any]) => {
                        const segName = campaignData.segments?.find((s: any) => s.segment_id === segId)?.name || segId;
                        const bestReport = reports.reduce((a: any, b: any) =>
                            (a.composite_score || 0) >= (b.composite_score || 0) ? a : b,
                        );
                        return (
                            <div key={segId} className="w-full overflow-hidden">
                                <h4 className="text-lg font-bold text-primary mb-4 flex items-center gap-2 bg-primary/10 w-fit max-w-full px-4 py-2 rounded-lg border border-primary/20">
                                    <Users className="h-5 w-5 shrink-0" />
                                    <span className="truncate whitespace-normal break-words">{segName}</span>
                                </h4>
                                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {reports.map((report: any, i: number) => {
                                        const isWinner = report === bestReport && reports.length > 1;
                                        return (
                                            <div
                                                key={i}
                                                onClick={() => setSelectedVariantForModal(report.variant_id)}
                                                className={`glass rounded-2xl p-6 transition-all duration-300 cursor-pointer ${isWinner ? "ring-2 ring-accent shadow-lg shadow-accent/20 scale-[1.02] bg-accent/5 hover:scale-[1.04]" : "border border-border/40 hover:border-primary/50 hover:scale-[1.02]"}`}
                                            >
                                                <div className="flex flex-col sm:flex-row items-center justify-between mb-5 gap-3">
                                                    <span className="text-sm font-bold text-muted-foreground uppercase tracking-widest bg-secondary/80 px-3 py-1.5 rounded-md truncate max-w-full">
                                                        {report.variant_id || `Variant ${String.fromCharCode(65 + i)}`}
                                                    </span>
                                                    {isWinner && (
                                                        <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-accent text-accent-foreground shadow-sm flex items-center gap-1.5 whitespace-nowrap shrink-0">
                                                            <Sparkles className="w-3 h-3" /> Winner
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="space-y-5">
                                                    <div className="bg-background/40 p-4 rounded-xl border border-border/30">
                                                        <div className="flex items-end justify-between text-sm mb-2">
                                                            <span className="text-muted-foreground font-medium">
                                                                Open Rate
                                                            </span>
                                                            <span className="text-xl font-bold text-foreground">
                                                                {((report.open_rate || 0) * 100).toFixed(1)}%
                                                            </span>
                                                        </div>
                                                        <div className="h-2.5 bg-secondary rounded-full overflow-hidden shadow-inner">
                                                            <div
                                                                className="h-full bg-primary rounded-full transition-all duration-1000"
                                                                style={{ width: `${(report.open_rate || 0) * 100}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                    <div className="bg-background/40 p-4 rounded-xl border border-border/30">
                                                        <div className="flex items-end justify-between text-sm mb-2">
                                                            <span className="text-muted-foreground font-medium">
                                                                Click Rate
                                                            </span>
                                                            <span className="text-xl font-bold text-foreground">
                                                                {((report.click_rate || 0) * 100).toFixed(1)}%
                                                            </span>
                                                        </div>
                                                        <div className="h-2.5 bg-secondary rounded-full overflow-hidden shadow-inner">
                                                            <div
                                                                className="h-full bg-accent rounded-full transition-all duration-1000"
                                                                style={{ width: `${(report.click_rate || 0) * 100}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                    <div className="pt-4 border-t border-border/50 flex items-center justify-between">
                                                        <span className="text-base font-semibold text-muted-foreground">
                                                            Composite Score
                                                        </span>
                                                        <span className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
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
            {campaignData?.optimization_history && campaignData.optimization_history.length > 0 && (
                <div className="glass rounded-3xl p-8 shadow-2xl border border-primary/20 backdrop-blur-xl bg-background/60">
                    <div className="flex items-center gap-4 mb-8">
                        <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/30 text-primary shadow-inner">
                            <Brain className="h-8 w-8" />
                        </div>
                        <div>
                            <h3 className="text-2xl font-bold text-foreground leading-tight">
                                AI Reasoning & Insights
                            </h3>
                            <p className="text-base text-muted-foreground font-medium">
                                Strategic optimization analysis across iterations
                            </p>
                        </div>
                    </div>
                    <div className="space-y-5">
                        {campaignData.optimization_history.map((entry: any, i: number) => (
                            <div
                                key={i}
                                className="flex flex-col sm:flex-row gap-5 p-6 rounded-2xl bg-secondary/20 border border-border/50 hover:bg-secondary/30 transition-colors shadow-sm"
                            >
                                <div className="flex-shrink-0">
                                    <div className="w-10 h-10 rounded-full bg-accent/20 text-accent flex items-center justify-center font-bold shadow-sm ring-1 ring-accent/30">
                                        #{entry.iteration ?? i + 1}
                                    </div>
                                </div>
                                <div className="space-y-3 flex-1">
                                    {entry.action_taken && (
                                        <h4 className="text-xl font-bold text-foreground tracking-tight">
                                            {entry.action_taken}
                                        </h4>
                                    )}
                                    {entry.insight && (
                                        <p className="text-base text-muted-foreground leading-relaxed border-l-2 border-primary/40 pl-4 py-1">
                                            {entry.insight}
                                        </p>
                                    )}

                                    <div className="flex flex-wrap gap-2 pt-2">
                                        {(entry.winning_tones || []).map((t: string) => (
                                            <span
                                                key={`w-${t}`}
                                                className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-semibold bg-accent/15 text-accent border border-accent/30 shadow-sm"
                                            >
                                                <CheckCircle2 className="h-4 w-4 mr-1.5" /> Best Tone: {t}
                                            </span>
                                        ))}
                                        {(entry.losing_tones || []).map((t: string) => (
                                            <span
                                                key={`l-${t}`}
                                                className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-semibold bg-destructive/10 text-destructive border border-destructive/20 shadow-sm"
                                            >
                                                <XCircle className="h-4 w-4 mr-1.5" /> Drop: {t}
                                            </span>
                                        ))}
                                    </div>

                                    {(entry.winning_elements || []).length > 0 && (
                                        <div className="pt-3 flex gap-2 items-start opacity-90">
                                            <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                                            <p className="text-sm font-medium text-foreground">
                                                <span className="text-muted-foreground mr-1">Successful Elements:</span>
                                                {entry.winning_elements?.join(", ")}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Restart Campaign Action */}
            {onRestart && (
                <div className="text-center mt-12 mb-8">
                    <button
                        onClick={onRestart}
                        className="inline-flex flex-col items-center justify-center gap-3 px-10 py-5 rounded-3xl bg-secondary/50 border border-border hover:border-primary/50 text-foreground hover:bg-secondary transition-all hover:-translate-y-1 hover:shadow-xl group"
                    >
                        <div className="p-3 bg-primary/20 rounded-full group-hover:bg-primary/30 transition-colors">
                            <Sparkles className="h-6 w-6 text-primary" />
                        </div>
                        <span className="font-bold text-lg">Start New Campaign</span>
                    </button>
                </div>
            )}
        </div>
    );
};

export default Metrics;
