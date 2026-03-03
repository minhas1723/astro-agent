import { useState, useRef, useEffect } from "react";
import { Sparkles, ArrowRight, ArrowLeft, Clock, MapPin, Calendar, Mail, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ChartReveal } from "@/components/ChartReveal";
import { useUser } from "@/contexts/UserContext";
import type { UserProfile, BirthChart } from "@/contexts/UserContext";
import { API_CONFIG } from "@/lib/api";

// ---------------------------------------------------------------------------
// Step definitions
// ---------------------------------------------------------------------------
type StepConfig = {
  key: keyof Omit<UserProfile, "birthTime"> | "birthTime";
  icon: React.ReactNode;
  prompt: string;
  subtext?: string;
  inputType: string;
  placeholder: string;
  required: boolean;
  skipLabel?: string;
};

const STEPS: StepConfig[] = [
  {
    key: "name",
    icon: <User size={20} />,
    prompt: "What should we call you?",
    inputType: "text",
    placeholder: "Your first name",
    required: true,
  },
  {
    key: "email",
    icon: <Mail size={20} />,
    prompt: "Where can we remember you?",
    subtext: "We use this only to save your chart",
    inputType: "email",
    placeholder: "your@email.com",
    required: true,
  },
  {
    key: "dob",
    icon: <Calendar size={20} />,
    prompt: "When were you born?",
    inputType: "date",
    placeholder: "",
    required: true,
  },
  {
    key: "birthTime",
    icon: <Clock size={20} />,
    prompt: "Do you know your birth time?",
    subtext: "Birth time helps pinpoint your Moon sign and Ascendant",
    inputType: "time",
    placeholder: "",
    required: false,
    skipLabel: "I don't know — skip",
  },
  {
    key: "birthPlace",
    icon: <MapPin size={20} />,
    prompt: "Where were you born?",
    subtext: "City or town name is enough",
    inputType: "text",
    placeholder: "e.g. Mumbai, India",
    required: true,
  },
];

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------
function validate(step: StepConfig, value: string): string | null {
  if (!step.required && !value) return null; // optional step
  if (step.required && !value.trim()) return "This field is required";
  if (step.key === "name" && value.trim().length < 2) return "Please enter at least 2 characters";
  if (step.key === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return "Please enter a valid email";
  if (step.key === "dob") {
    const d = new Date(value);
    if (isNaN(d.getTime()) || d >= new Date()) return "Please enter a valid past date";
  }
  if (step.key === "birthPlace" && value.trim().length < 2) return "Please enter a valid place";
  return null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export function OnboardingWizard() {
  const { setSession } = useUser();
  const [currentStep, setCurrentStep] = useState(0);
  const [values, setValues] = useState<Record<string, string>>({
    name: "",
    email: "",
    dob: "",
    birthTime: "",
    birthPlace: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [direction, setDirection] = useState<"forward" | "backward">("forward");

  // Chart reveal state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [chart, setChart] = useState<BirthChart | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  const step = STEPS[currentStep]!;
  const isLast = currentStep === STEPS.length - 1;
  const progress = ((currentStep + 1) / STEPS.length) * 100;

  // Auto-focus input on step change
  useEffect(() => {
    const timer = setTimeout(() => inputRef.current?.focus(), 300);
    return () => clearTimeout(timer);
  }, [currentStep]);

  const handleNext = () => {
    const err = validate(step, values[step.key] || "");
    if (err) {
      setError(err);
      return;
    }
    setError(null);

    if (isLast) {
      handleSubmit();
    } else {
      setDirection("forward");
      setCurrentStep((s) => s + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setError(null);
      setDirection("backward");
      setCurrentStep((s) => s - 1);
    }
  };

  const handleSkip = () => {
    setError(null);
    setValues((v) => ({ ...v, [step.key]: "" }));
    if (isLast) {
      handleSubmit();
    } else {
      setDirection("forward");
      setCurrentStep((s) => s + 1);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleNext();
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitError(null);

    const profile: UserProfile = {
      name: values.name!,
      email: values.email!,
      dob: values.dob!,
      birthTime: values.birthTime || "",
      birthPlace: values.birthPlace!,
    };

    try {
      const res = await fetch(`${API_CONFIG.BASE_URL}/chart/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: profile.name,
          email: profile.email,
          dob: profile.dob,
          birth_time: profile.birthTime,
          birth_place: profile.birthPlace,
        }),
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const data: BirthChart = await res.json();
      setChart(data);
    } catch (err: any) {
      console.error("Chart calculation failed:", err);
      setSubmitError(err.message || "Something went wrong. Please try again.");
      setIsSubmitting(false);
    }
  };

  const handleRevealComplete = () => {
    if (chart) {
      const profile: UserProfile = {
        name: values.name!,
        email: values.email!,
        dob: values.dob!,
        birthTime: values.birthTime || "",
        birthPlace: values.birthPlace!,
      };
      setSession(profile, chart);
    }
  };

  // ── If chart is loaded, show the reveal ──
  if (chart) {
    return (
      <ChartReveal
        chart={chart}
        userName={values.name!}
        onComplete={handleRevealComplete}
      />
    );
  }

  // ── Loading state ──
  if (isSubmitting) {
    return (
      <div className="h-screen w-full flex flex-col items-center justify-center bg-white dark:bg-zinc-900 gap-6">
        <div className="w-14 h-14 bg-gradient-to-br from-indigo-600 to-violet-700 rounded-full flex items-center justify-center shadow-lg shadow-indigo-200 dark:shadow-indigo-900/50 animate-pulse">
          <Sparkles size={26} className="text-amber-300 animate-spin" style={{ animationDuration: "3s" }} />
        </div>
        <p className="text-lg text-zinc-500 dark:text-zinc-400 animate-pulse">
          Mapping your celestial blueprint...
        </p>
        {submitError && (
          <div className="text-center space-y-3">
            <p className="text-sm text-red-500">{submitError}</p>
            <Button variant="outline" onClick={() => { setIsSubmitting(false); setSubmitError(null); }}>
              Try again
            </Button>
          </div>
        )}
      </div>
    );
  }

  // ── Wizard form ──
  return (
    <div className="h-screen w-full flex flex-col bg-white dark:bg-zinc-900 font-sans selection:bg-zinc-200 dark:selection:bg-zinc-700">
      {/* Progress bar */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-zinc-100 dark:bg-zinc-800 z-20">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 to-violet-600 transition-all duration-500 ease-out rounded-r-full"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Center content */}
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-md space-y-8">

          {/* Logo + branding */}
          <div className="flex flex-col items-center gap-4 animate-in fade-in duration-500">
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-600 to-violet-700 rounded-full flex items-center justify-center shadow-lg shadow-indigo-200 dark:shadow-indigo-900/50">
              <Sparkles size={22} className="text-amber-300" />
            </div>
          </div>

          {/* Step content */}
          <div
            key={currentStep}
            className={cn(
              "space-y-6 animate-in duration-300",
              direction === "forward"
                ? "slide-in-from-right-4 fade-in"
                : "slide-in-from-left-4 fade-in"
            )}
          >
            {/* Icon + prompt */}
            <div className="text-center space-y-2">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 mb-2">
                {step.icon}
              </div>
              <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight">
                {step.prompt}
              </h2>
              {step.subtext && (
                <p className="text-sm text-zinc-400 dark:text-zinc-500">
                  {step.subtext}
                </p>
              )}
            </div>

            {/* Input */}
            <div className="space-y-2">
              <Input
                ref={inputRef}
                type={step.inputType}
                value={values[step.key] || ""}
                onChange={(e) => {
                  setValues((v) => ({ ...v, [step.key]: e.target.value }));
                  if (error) setError(null);
                }}
                onKeyDown={handleKeyDown}
                placeholder={step.placeholder}
                className={cn(
                  "h-12 text-base rounded-xl border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/50 px-4",
                  "focus-visible:ring-indigo-500/30 focus-visible:border-indigo-500 dark:focus-visible:border-indigo-400",
                  error && "border-red-300 dark:border-red-800"
                )}
                autoComplete={step.key === "email" ? "email" : step.key === "name" ? "given-name" : "off"}
              />
              {error && (
                <p className="text-xs text-red-500 pl-1 animate-in fade-in duration-200">{error}</p>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between gap-3">
              <div>
                {currentStep > 0 && (
                  <Button
                    variant="ghost"
                    onClick={handleBack}
                    className="text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100 gap-1"
                  >
                    <ArrowLeft size={16} />
                    Back
                  </Button>
                )}
              </div>

              <div className="flex items-center gap-3">
                {step.skipLabel && (
                  <button
                    onClick={handleSkip}
                    className="text-sm text-zinc-400 hover:text-zinc-600 dark:text-zinc-500 dark:hover:text-zinc-300 transition-colors underline-offset-2 hover:underline"
                  >
                    {step.skipLabel}
                  </button>
                )}
                <Button
                  onClick={handleNext}
                  className="bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 rounded-full px-6 h-10 gap-2 font-medium"
                >
                  {isLast ? "Map my stars" : "Continue"}
                  <ArrowRight size={16} />
                </Button>
              </div>
            </div>
          </div>

          {/* Step dots */}
          <div className="flex items-center justify-center gap-2 pt-4">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={cn(
                  "w-2 h-2 rounded-full transition-all duration-300",
                  i === currentStep
                    ? "bg-indigo-600 dark:bg-indigo-400 w-6"
                    : i < currentStep
                    ? "bg-indigo-300 dark:bg-indigo-700"
                    : "bg-zinc-200 dark:bg-zinc-700"
                )}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
