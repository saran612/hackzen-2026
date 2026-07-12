import React from "react";
import { Shield, ShieldAlert, ShieldOff, AlertTriangle, Info } from "lucide-react";

export default function ResultsDisplay({ scores, quality, warnings }) {
  if (!scores) return null;

  // Helper to extract numeric score (handles both structured and flat formats)
  const getScore = (val) => {
    if (typeof val === "object" && val !== null) return val.score ?? 0;
    return val ?? 0;
  };

  const getConfidence = (val) => {
    if (typeof val === "object" && val !== null) return val.confidence ?? "high";
    return "high";
  };

  // Helper to color code concern intensity
  const getScoreColor = (score) => {
    if (score < 30) return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    if (score < 60) return "text-amber-400 bg-amber-500/10 border-amber-500/20";
    return "text-rose-400 bg-rose-500/10 border-rose-500/20";
  };

  const getBarColor = (score) => {
    if (score < 30) return "bg-emerald-500";
    if (score < 60) return "bg-amber-500";
    return "bg-rose-500";
  };

  // Human-friendly description of severity
  const getSeverityLabel = (score) => {
    if (score < 15) return "Minimal";
    if (score < 30) return "Mild";
    if (score < 60) return "Moderate";
    return "Elevated";
  };

  // Confidence badge styling
  const getConfidenceBadge = (confidence) => {
    switch (confidence) {
      case "high":
        return {
          icon: <Shield className="w-3 h-3" />,
          label: "High Confidence",
          className: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
        };
      case "medium":
        return {
          icon: <ShieldAlert className="w-3 h-3" />,
          label: "Medium Confidence",
          className: "text-amber-400 bg-amber-500/10 border-amber-500/20",
        };
      case "low":
        return {
          icon: <ShieldOff className="w-3 h-3" />,
          label: "Low Confidence",
          className: "text-rose-400 bg-rose-500/10 border-rose-500/20",
        };
      default:
        return {
          icon: <Shield className="w-3 h-3" />,
          label: "Confidence N/A",
          className: "text-slate-400 bg-slate-500/10 border-slate-500/20",
        };
    }
  };

  // Human-friendly concern labels (renamed dark_circles → under-eye contrast)
  const concernLabels = {
    acne: "Acne & Blemishes",
    under_eye_contrast: "Under-Eye Contrast",
    dark_circles: "Under-Eye Contrast",
    pigmentation: "Pigmentation",
    oiliness: "Oiliness",
    dryness: "Dryness",
    wrinkles: "Fine Lines",
  };

  return (
    <div className="w-full max-w-xl p-6 bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800 flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100 mb-1">Zone Analysis Results</h2>
        <p className="text-xs text-slate-400">
          Concern scores graded 0–100 using relative optical heuristics. Each score includes a confidence level based on image quality.
        </p>
      </div>

      {/* Quality warnings banner */}
      {warnings && warnings.length > 0 && (
        <div className="flex flex-col gap-2 p-4 bg-amber-950/30 border border-amber-900/40 rounded-xl">
          <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold">
            <AlertTriangle className="w-4 h-4" />
            Image Quality Notices
          </div>
          {warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-300/80 pl-6 leading-relaxed">{w}</p>
          ))}
        </div>
      )}

      {/* Quality metadata summary */}
      {quality && (
        <div className="flex flex-wrap gap-2">
          {quality.faces_detected > 1 && (
            <span className="text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-0.5 rounded-full font-medium">
              {quality.faces_detected} faces → largest selected
            </span>
          )}
          {quality.exposure !== "normal" && (
            <span className="text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-0.5 rounded-full font-medium">
              {quality.exposure}
            </span>
          )}
          {quality.flash_detected && (
            <span className="text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-0.5 rounded-full font-medium">
              Flash detected
            </span>
          )}
          {quality.lighting_uniformity === "uneven" && (
            <span className="text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-0.5 rounded-full font-medium">
              Uneven lighting
            </span>
          )}
          {quality.preprocessing_applied && quality.preprocessing_applied.length > 0 && (
            <span className="text-[10px] bg-slate-800 text-slate-400 border border-slate-700 px-2.5 py-0.5 rounded-full font-medium">
              Auto-corrected: {quality.preprocessing_applied.join(", ")}
            </span>
          )}
        </div>
      )}

      <div className="grid gap-4">
        {Object.entries(scores).map(([concern, value]) => {
          const score = getScore(value);
          const confidence = getConfidence(value);
          const badge = getConfidenceBadge(confidence);
          const label = concernLabels[concern] || concern.replace(/_/g, " ");

          return (
            <div key={concern} className="flex flex-col gap-2 p-4 bg-slate-950/40 rounded-xl border border-slate-850">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-slate-200">
                  {label}
                </span>
                <div className="flex items-center gap-2">
                  {/* Confidence badge */}
                  <span
                    className={`flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border font-medium ${badge.className}`}
                    title={badge.label}
                  >
                    {badge.icon}
                    {confidence}
                  </span>
                  {/* Severity label */}
                  <span className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold ${getScoreColor(score)}`}>
                    {getSeverityLabel(score)}
                  </span>
                  <span className="text-sm font-bold text-slate-100">{score}/100</span>
                </div>
              </div>
              {/* Progress bar */}
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-1000 ${getBarColor(score)}`}
                  style={{ width: `${Math.max(3, score)}%` }}
                />
              </div>
              {/* Low confidence disclaimer */}
              {confidence === "low" && (
                <p className="text-[10px] text-amber-400/70 italic mt-0.5 flex items-center gap-1">
                  <Info className="w-3 h-3" />
                  This score may be less accurate due to image quality conditions.
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-3 p-4 bg-slate-950/80 rounded-xl border border-slate-850 text-xs text-slate-400">
        <Info className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Not a clinical diagnosis.</strong> Scores reflect relative heuristic indicators, not dermatological assessments. Facial redness from sunburn, rosacea, or exertion may inflate acne scores. Under-eye contrast measures relative luminance difference, not fatigue.
        </p>
      </div>
    </div>
  );
}
