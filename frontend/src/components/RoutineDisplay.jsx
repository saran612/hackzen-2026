import React from "react";
import { Check, Info } from "lucide-react";

export default function RoutineDisplay({ routine }) {
  if (!routine || routine.length === 0) return null;

  return (
    <div className="w-full max-w-xl p-6 bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800 flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100 mb-1">Recommended Routine</h2>
        <p className="text-xs text-slate-400">
          A personalized, gender-neutral skincare regimen matching your current skin concern scores.
        </p>
      </div>

      <div className="flex flex-col gap-5">
        {routine.map((step, idx) => (
          <div 
            key={idx}
            className="flex gap-4 p-5 bg-slate-950/40 border border-slate-850 rounded-xl hover:border-emerald-500/30 transition duration-300 relative overflow-hidden"
          >
            {/* Step badge */}
            <div className="absolute top-0 right-0 px-3 py-1 bg-emerald-500/10 border-l border-b border-emerald-500/20 text-[10px] text-emerald-400 font-bold tracking-widest uppercase">
              {step.step}
            </div>

            {/* Step Index Circle */}
            <div className="w-8 h-8 rounded-full bg-slate-850 border border-slate-700 flex items-center justify-center font-bold text-sm text-slate-300 flex-shrink-0">
              {idx + 1}
            </div>

            <div className="flex flex-col gap-2">
              <h3 className="text-base font-semibold text-slate-100 mt-1">{step.title}</h3>
              <p className="text-sm text-slate-300 leading-relaxed">{step.description}</p>
              
              {/* Ingredient list */}
              <div className="flex flex-wrap gap-1.5 mt-2">
                {step.ingredients.map((ing) => (
                  <span 
                    key={ing} 
                    className="text-[10px] bg-slate-800 text-slate-300 px-2.5 py-0.5 rounded-full border border-slate-700 font-medium"
                  >
                    {ing}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Note about gender-neutral and limitations */}
      <div className="flex items-start gap-3 p-4 bg-slate-950/80 rounded-xl border border-slate-850 text-xs text-slate-400">
        <Info className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Gender-Neutral Formulation</strong>: This routine focuses purely on active biochemical ingredients suited to skin physiology. All recommendations are framed neutrally, avoiding gendered marketing copy.
        </p>
      </div>
    </div>
  );
}
