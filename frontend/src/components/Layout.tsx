import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Zap, Wifi, WifiOff } from "lucide-react";
import { useState, useEffect } from "react";

const Header = () => {
  const location = useLocation();
  const [apiConnected, setApiConnected] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch("http://localhost:8000", { method: "GET", signal: AbortSignal.timeout(2000) });
        setApiConnected(res.ok);
      } catch {
        setApiConnected(false);
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { to: "/", label: "Home" },
    { to: "/dashboard", label: "Dashboard" },
  ];

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="fixed top-0 left-0 right-0 z-50 glass-strong"
    >
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="relative">
            <Zap className="h-6 w-6 text-primary" />
            <div className="absolute inset-0 blur-md bg-primary/40 rounded-full" />
          </div>
          <span className="text-lg font-bold tracking-tight text-foreground">
            Campaign<span className="text-primary">X</span>
          </span>
        </Link>

        <nav className="flex items-center gap-1">
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === item.to
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
              }`}
            >
              {item.label}
            </Link>
          ))}

          <div className={`ml-4 flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${
            apiConnected
              ? "border-accent/30 bg-accent/10 text-accent"
              : "border-destructive/30 bg-destructive/10 text-destructive"
          }`}>
            {apiConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            {apiConnected ? "API Connected" : "API Offline"}
          </div>
        </nav>
      </div>
    </motion.header>
  );
};

const Footer = () => (
  <footer className="border-t border-border/50 py-6 mt-auto">
    <div className="container text-center text-sm text-muted-foreground">
      Built with precision by <span className="text-foreground font-medium">Team Four Musketeers</span> for{" "}
      <span className="text-primary font-medium">FrostHack</span>
    </div>
  </footer>
);

interface LayoutProps {
  children: React.ReactNode;
}

const Layout = ({ children }: LayoutProps) => (
  <div className="flex min-h-screen flex-col">
    <Header />
    <main className="flex-1 pt-16">{children}</main>
    <Footer />
  </div>
);

export default Layout;
