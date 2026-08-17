import { BadgeCheck, CircleAlert, CircleX, ShieldAlert, ShieldCheck, ShieldX, TriangleAlert } from "lucide-react";
import type { Confidence, GateDecision, ThresholdDecision } from "@/types/api";

export interface StatusVisual {
  label: string;
  icon: typeof ShieldCheck;
  badgeClass: string;
  textClass: string;
}

export const gateVisuals: Record<GateDecision["verdict"], StatusVisual> = {
  ALLOW: {
    label: "Allowed",
    icon: ShieldCheck,
    badgeClass: "bg-success/10 text-success border-success/30",
    textClass: "text-success",
  },
  CAUTION: {
    label: "Caution",
    icon: ShieldAlert,
    badgeClass: "bg-warning/10 text-warning border-warning/30",
    textClass: "text-warning",
  },
  REFUSE: {
    label: "Refused",
    icon: ShieldX,
    badgeClass: "bg-destructive/10 text-destructive border-destructive/30",
    textClass: "text-destructive",
  },
};

export const confidenceVisuals: Record<Confidence, StatusVisual> = {
  High: {
    label: "High",
    icon: BadgeCheck,
    badgeClass: "bg-success/10 text-success border-success/30",
    textClass: "text-success",
  },
  Medium: {
    label: "Medium",
    icon: CircleAlert,
    badgeClass: "bg-warning/10 text-warning border-warning/30",
    textClass: "text-warning",
  },
  Low: {
    label: "Low",
    icon: TriangleAlert,
    badgeClass: "bg-warning/10 text-warning border-warning/30",
    textClass: "text-warning",
  },
  "Insufficient Evidence": {
    label: "Insufficient Evidence",
    icon: CircleX,
    badgeClass: "bg-destructive/10 text-destructive border-destructive/30",
    textClass: "text-destructive",
  },
};

export const thresholdVisuals: Record<ThresholdDecision["action"], StatusVisual> = {
  PROCEED: gateVisuals.ALLOW,
  DOWNGRADE: {
    label: "Downgraded",
    icon: TriangleAlert,
    badgeClass: "bg-warning/10 text-warning border-warning/30",
    textClass: "text-warning",
  },
  HALT: {
    label: "Halted",
    icon: ShieldX,
    badgeClass: "bg-destructive/10 text-destructive border-destructive/30",
    textClass: "text-destructive",
  },
};
