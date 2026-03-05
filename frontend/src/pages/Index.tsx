import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowRight, Brain, Shield, BarChart3, Sparkles, TrendingUp, Users, Mail } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from "recharts";

const features = [
  {
    icon: Brain,
    title: "Dynamic Segmenting",
    description: "AI-driven audience clustering that adapts in real-time to behavioral signals across BFSI verticals.",
  },
  {
    icon: BarChart3,
    title: "Thompson Sampling",
    description: "Bayesian optimization engine that dynamically allocates traffic to highest-performing variants.",
  },
  {
    icon: Shield,
    title: "Human-in-the-Loop",
    description: "Compliance-first approval workflows ensuring every campaign meets regulatory standards before execution.",
  },
];

const performanceData = [
  { day: "Mon", openRate: 28, clickRate: 8 },
  { day: "Tue", openRate: 31, clickRate: 11 },
  { day: "Wed", openRate: 29, clickRate: 10 },
  { day: "Thu", openRate: 35, clickRate: 14 },
  { day: "Fri", openRate: 38, clickRate: 16 },
  { day: "Sat", openRate: 34, clickRate: 13 },
  { day: "Sun", openRate: 42, clickRate: 19 },
];

const variantData = [
  { name: "Variant A", score: 72 },
  { name: "Variant B", score: 65 },
  { name: "Variant C", score: 88 },
  { name: "Variant D", score: 54 },
];

  const containerVariants = {
  visible: { transition: { staggerChildren: 0.15 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] as const } },
};

const Index = () => {
  return (
    <div className="relative overflow-hidden">
      {/* Ambient glow */}
      <div className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-primary/5 rounded-full blur-[120px]" />
      <div className="pointer-events-none absolute top-40 right-0 w-[400px] h-[400px] bg-accent/5 rounded-full blur-[100px]" />

      {/* Hero */}
      <section className="relative min-h-[90vh] flex items-center">
        <div className="container">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={containerVariants}
            className="max-w-3xl mx-auto text-center"
          >
            <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-sm font-medium mb-8">
              <Sparkles className="h-3.5 w-3.5" />
              Agentic AI for BFSI Marketing
            </motion.div>

            <motion.h1 variants={itemVariants} className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1] mb-6">
              Autonomous Marketing.{" "}
              <span className="text-gradient">Human Precision.</span>
            </motion.h1>

            <motion.p variants={itemVariants} className="text-lg sm:text-xl text-muted-foreground max-w-xl mx-auto mb-10 leading-relaxed">
              Optimize BFSI campaigns with agentic AI — from dynamic segmentation to compliance-approved execution, all on autopilot.
            </motion.p>

            <motion.div variants={itemVariants}>
              <Link
                to="/dashboard"
                className="group relative inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-primary text-primary-foreground font-semibold text-base transition-all hover:scale-[1.02] active:scale-[0.98] glow-primary"
              >
                Launch App
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 relative">
        <div className="container">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerVariants}
            className="grid md:grid-cols-3 gap-6"
          >
            {features.map((feature) => (
              <motion.div
                key={feature.title}
                variants={itemVariants}
                className="group relative glass rounded-2xl p-8 transition-all hover:border-primary/30"
              >
                <div className="mb-5 inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 text-primary">
                  <feature.icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-3">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Analytics Showcase */}
      <section className="py-24 relative">
        <div className="pointer-events-none absolute bottom-0 left-0 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[120px]" />
        <div className="container">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerVariants}
          >
            <motion.div variants={itemVariants} className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground mb-4">
                Real-Time <span className="text-gradient">Analytics</span>
              </h2>
              <p className="text-muted-foreground max-w-lg mx-auto">
                Track campaign performance with AI-powered insights and live optimization metrics.
              </p>
            </motion.div>

            {/* KPI Cards */}
            <motion.div variants={itemVariants} className="grid sm:grid-cols-3 gap-4 mb-8">
              {[
                { label: "Avg. Open Rate", value: "34.2%", icon: Mail, change: "+12%" },
                { label: "Active Segments", value: "8", icon: Users, change: "+3" },
                { label: "Conversion Lift", value: "2.4x", icon: TrendingUp, change: "+18%" },
              ].map((kpi) => (
                <div key={kpi.label} className="glass rounded-2xl p-6 flex items-center gap-4">
                  <div className="flex items-center justify-center w-11 h-11 rounded-xl bg-primary/10 text-primary flex-shrink-0">
                    <kpi.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">{kpi.label}</p>
                    <p className="text-2xl font-bold text-foreground">{kpi.value}</p>
                  </div>
                  <span className="ml-auto text-xs font-semibold text-accent">{kpi.change}</span>
                </div>
              ))}
            </motion.div>

            {/* Charts */}
            <motion.div variants={itemVariants} className="grid md:grid-cols-2 gap-6">
              {/* Area Chart - Campaign Performance Over Time */}
              <div className="glass rounded-2xl p-6">
                <h3 className="text-sm font-semibold text-foreground mb-1">Campaign Performance</h3>
                <p className="text-xs text-muted-foreground mb-4">Open & click rates over 7 days</p>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={performanceData}>
                      <defs>
                        <linearGradient id="openGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="clickGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(168, 84%, 50%)" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="hsl(168, 84%, 50%)" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 30%, 16%)" />
                      <XAxis dataKey="day" tick={{ fill: "hsl(215, 20%, 55%)", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: "hsl(215, 20%, 55%)", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "hsl(222, 44%, 9%)",
                          border: "1px solid hsl(222, 30%, 16%)",
                          borderRadius: "0.75rem",
                          fontSize: 12,
                          color: "hsl(210, 40%, 96%)",
                        }}
                      />
                      <Area type="monotone" dataKey="openRate" stroke="hsl(217, 91%, 60%)" fill="url(#openGrad)" strokeWidth={2} name="Open %" />
                      <Area type="monotone" dataKey="clickRate" stroke="hsl(168, 84%, 50%)" fill="url(#clickGrad)" strokeWidth={2} name="Click %" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Bar Chart - Variant Comparison */}
              <div className="glass rounded-2xl p-6">
                <h3 className="text-sm font-semibold text-foreground mb-1">Variant Comparison</h3>
                <p className="text-xs text-muted-foreground mb-4">Composite score by variant</p>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={variantData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 30%, 16%)" />
                      <XAxis dataKey="name" tick={{ fill: "hsl(215, 20%, 55%)", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: "hsl(215, 20%, 55%)", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "hsl(222, 44%, 9%)",
                          border: "1px solid hsl(222, 30%, 16%)",
                          borderRadius: "0.75rem",
                          fontSize: 12,
                          color: "hsl(210, 40%, 96%)",
                        }}
                      />
                      <Bar dataKey="score" radius={[6, 6, 0, 0]} name="Score">
                        {variantData.map((_, i) => (
                          <Cell key={i} fill={i === 2 ? "hsl(168, 84%, 50%)" : "hsl(217, 91%, 60%)"} fillOpacity={0.8} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default Index;
