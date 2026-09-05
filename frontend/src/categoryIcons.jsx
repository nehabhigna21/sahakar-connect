import { Zap, Wrench, Sparkles, HeartPulse, Hammer, Paintbrush, Bug, Wind, ShieldCheck } from "lucide-react";

const ICON_MAP = [
  [/electric/i, Zap],
  [/plumb/i, Wrench],
  [/clean/i, Sparkles],
  [/care|nurse|nanny/i, HeartPulse],
  [/carpen/i, Hammer],
  [/paint/i, Paintbrush],
  [/pest/i, Bug],
  [/ac|appliance/i, Wind],
];

export function CategoryIcon({ name, size = 26 }) {
  const match = ICON_MAP.find(([pattern]) => pattern.test(name));
  const Icon = match ? match[1] : ShieldCheck;
  return <Icon size={size} strokeWidth={1.75} />;
}
