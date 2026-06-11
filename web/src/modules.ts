import { Calendar, Grid3X3, Package, Scale, Search, TrendingUp } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface ModuleDef {
  path: string;
  name: string;
  decision: string; // the question this module answers, in plain language
  icon: LucideIcon;
  ready: boolean; // false = still only in the legacy Streamlit app
  exampleSearch?: string; // query string that loads a preset
}

export const MODULES: ModuleDef[] = [
  { path: "/line-balancing", name: "Line Balancing", decision: "How do I split assembly work into balanced stations?", icon: Scale, ready: false },
  { path: "/process-analysis", name: "Process Analysis", decision: "Where is my bottleneck, and what is it costing me?", icon: Search, ready: false },
  { path: "/scheduling", name: "Scheduling", decision: "What order should I run these jobs in?", icon: Calendar, ready: true, exampleSearch: "?j=A,6,8;B,2,6;C,8,18;D,3,15;E,9,23" },
  { path: "/lot-sizing", name: "Lot Sizing", decision: "How much should I order, and when?", icon: Package, ready: true, exampleSearch: "?d=50,60,90,70,30,100&s=150&h=1" },
  { path: "/cellular", name: "Cellular", decision: "Which machines belong together in cells?", icon: Grid3X3, ready: false },
  { path: "/productivity", name: "Productivity", decision: "Did we actually get more productive?", icon: TrendingUp, ready: false },
];
