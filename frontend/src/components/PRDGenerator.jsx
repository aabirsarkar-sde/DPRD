import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { toast } from "sonner";
import { FileText, ChevronRight, Copy, Check, Loader2, ArrowLeft, Clock, Lightbulb } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PRD_TIPS = [
  {
    title: "Be Specific with Tech Stack",
    description: "Name exact libraries and versions (e.g., 'TanStack Query v5' not just 'data fetching library')"
  },
  {
    title: "Define Edge Cases Early",
    description: "Every feature should have error states, empty states, and loading states documented"
  },
  {
    title: "Include UI Specifications",
    description: "Specify colors (hex), spacing, typography, and component behaviors for consistent implementation"
  },
  {
    title: "Write User Flows Step-by-Step",
    description: "Break down each feature into numbered steps: User does X → System responds Y → User sees Z"
  },
  {
    title: "Document API Contracts",
    description: "Include request/response shapes for every endpoint to avoid backend/frontend mismatches"
  },
  {
    title: "Prioritize with Phases",
    description: "Split features into MVP, Enhanced, and Scale phases to focus development efforts"
  },
  {
    title: "Think About Authentication First",
    description: "Auth decisions affect data models, API design, and UI flows throughout the entire app"
  },
  {
    title: "Consider Mobile Responsiveness",
    description: "Define breakpoints and layout changes for different screen sizes upfront"
  }
];

const PRDGenerator = () => {
  const [step, setStep] = useState(1);
  const [idea, setIdea] = useState("");
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [prd, setPrd] = useState("");
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [timeLeft, setTimeLeft] = useState(60);
  const [timerActive, setTimerActive] = useState(false);
  const [currentTipIndex, setCurrentTipIndex] = useState(0);
  const timerRef = useRef(null);
  const tipIntervalRef = useRef(null);

  // Timer effect
  useEffect(() => {
    if (timerActive && timeLeft > 0) {
      timerRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [timerActive]);

  // Rotate tips while generating
  useEffect(() => {
    if (generating) {
      setCurrentTipIndex(0);
      tipIntervalRef.current = setInterval(() => {
        setCurrentTipIndex((prev) => (prev + 1) % PRD_TIPS.length);
      }, 4000);
    }
    return () => {
      if (tipIntervalRef.current) clearInterval(tipIntervalRef.current);
    };
  }, [generating]);

  // Start timer when entering step 2
  useEffect(() => {
    if (step === 2 && !timerActive) {
      setTimeLeft(60);
      setTimerActive(true);
    }
    if (step !== 2) {
      setTimerActive(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  }, [step]);

  const handleAnalyze = async () => {
    if (!idea.trim()) {
      toast.error("Please describe your app idea");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/analyze`, { idea });
      setQuestions(response.data.questions);
      setStep(2);
      toast.success("Analyzing complete");
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Failed to analyze idea");
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePRD = async () => {
    if (Object.keys(answers).length < questions.length) {
      toast.error("Please answer all questions");
      return;
    }

    setLoading(true);
    setGenerating(true);
    setStep(2.5); // Intermediate step for generating view
    try {
      const response = await axios.post(`${API}/generate-prd`, {
        idea,
        answers,
      });
      setPrd(response.data.prd);
      setStep(3);
      toast.success("PRD generated successfully");
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Failed to generate PRD");
      setStep(2); // Go back to questions on error
    } finally {
      setLoading(false);
      setGenerating(false);
    }
  };

  const handleCopy = async () => {
    try {
      // Try modern clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(prd);
      } else {
        // Fallback for older browsers or restricted contexts
        const textArea = document.createElement("textarea");
        textArea.value = prd;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
      }
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Copy failed:", error);
      toast.error("Failed to copy - please select and copy manually");
    }
  };

  const handleReset = () => {
    setStep(1);
    setIdea("");
    setQuestions([]);
    setAnswers({});
    setPrd("");
    setCopied(false);
    setTimeLeft(60);
    setTimerActive(false);
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTimerColor = () => {
    if (timeLeft <= 10) return 'text-red-500';
    if (timeLeft <= 20) return 'text-amber-500';
    return 'text-[#fafafa]';
  };

  const getCategoryLabel = (category) => {
    const labels = {
      auth: "Authentication",
      data_complexity: "Data Architecture",
      edge_cases: "Edge Cases",
      ui_layout: "UI Layout",
      ui_components: "UI Components",
      features: "Feature Scope",
      integrations: "Integrations",
      styling: "Visual Design",
    };
    return labels[category] || category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getCategoryIcon = (category) => {
    const icons = {
      auth: "🔐",
      data_complexity: "🗄️",
      edge_cases: "⚠️",
      ui_layout: "📐",
      ui_components: "🧩",
      features: "✨",
      integrations: "🔗",
      styling: "🎨",
    };
    return icons[category] || "📋";
  };

  const renderMarkdown = (text) => {
    // Simple markdown rendering
    return text
      .split("\n")
      .map((line, i) => {
        // Headers
        if (line.startsWith("# ")) {
          return <h1 key={i}>{line.slice(2)}</h1>;
        }
        if (line.startsWith("## ")) {
          return <h2 key={i}>{line.slice(3)}</h2>;
        }
        if (line.startsWith("### ")) {
          return <h3 key={i}>{line.slice(4)}</h3>;
        }
        // Code blocks
        if (line.startsWith("```")) {
          return null;
        }
        // Horizontal rule
        if (line === "---") {
          return <hr key={i} />;
        }
        // List items
        if (line.startsWith("- ")) {
          return <li key={i}>{formatInlineStyles(line.slice(2))}</li>;
        }
        // Empty lines
        if (!line.trim()) {
          return <br key={i} />;
        }
        // Regular paragraphs
        return <p key={i}>{formatInlineStyles(line)}</p>;
      });
  };

  const formatInlineStyles = (text) => {
    // Bold text
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      // Inline code
      const codeParts = part.split(/(`[^`]+`)/g);
      return codeParts.map((codePart, j) => {
        if (codePart.startsWith("`") && codePart.endsWith("`")) {
          return <code key={`${i}-${j}`}>{codePart.slice(1, -1)}</code>;
        }
        return codePart;
      });
    });
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b]">
      {/* Header */}
      <header className="border-b border-[#1f1f23] bg-[#0a0a0b]/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#18181b] rounded-md flex items-center justify-center border border-[#27272a]">
              <FileText className="w-4 h-4 text-[#a1a1aa]" />
            </div>
            <span className="font-semibold text-[#fafafa] tracking-tight">Deep PRD</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 text-xs text-[#71717a]">
              <span className={step >= 1 ? "text-[#fafafa]" : ""}>Idea</span>
              <ChevronRight className="w-3 h-3" />
              <span className={step >= 2 ? "text-[#fafafa]" : ""}>Clarify</span>
              <ChevronRight className="w-3 h-3" />
              <span className={step >= 2.5 ? "text-[#fafafa]" : ""}>Generate</span>
              <ChevronRight className="w-3 h-3" />
              <span className={step >= 3 ? "text-[#fafafa]" : ""}>PRD</span>
            </div>
          </div>
        </div>
        <Progress 
          value={step === 1 ? 25 : step === 2 ? 50 : step === 2.5 ? 75 : 100} 
          className="h-0.5 bg-[#1f1f23]" 
        />
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        {/* Step 1: Brain Dump */}
        {step === 1 && (
          <div className="animate-fade-in">
            <div className="mb-10">
              <h1 className="text-3xl font-semibold text-[#fafafa] mb-3 tracking-tight">
                What do you want to build?
              </h1>
              <p className="text-[#71717a] text-base">
                Describe your app idea in detail. The more context you provide, the better your PRD will be.
              </p>
            </div>

            <div className="space-y-6">
              <Textarea
                data-testid="idea-input"
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                placeholder="I want to build an app that... (describe features, target users, key functionality, any specific requirements)"
                className="min-h-[240px] bg-[#111113] border-[#27272a] text-[#fafafa] placeholder:text-[#52525b] focus:border-[#3f3f46] focus:ring-0 text-base resize-none rounded-lg"
              />

              <div className="flex justify-end">
                <Button
                  data-testid="analyze-btn"
                  onClick={handleAnalyze}
                  disabled={loading || !idea.trim()}
                  className="bg-[#fafafa] text-[#0a0a0b] hover:bg-[#e4e4e7] font-medium px-6 h-11 rounded-lg"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      Analyze
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </>
                  )}
                </Button>
              </div>
            </div>

            <div className="mt-16 pt-8 border-t border-[#1f1f23]">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
                <div className="space-y-2">
                  <div className="text-[#fafafa] font-medium flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    60-Second Challenge
                  </div>
                  <p className="text-[#52525b]">Answer quick MCQs about auth, UI, data & features</p>
                </div>
                <div className="space-y-2">
                  <div className="text-[#fafafa] font-medium">AI-Optimized Output</div>
                  <p className="text-[#52525b]">PRDs designed to work perfectly with Cursor, Lovable, Bolt</p>
                </div>
                <div className="space-y-2">
                  <div className="text-[#fafafa] font-medium">Save Credits</div>
                  <p className="text-[#52525b]">Detailed specs mean fewer AI iterations and rewrites</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Clarifying Questions */}
        {step === 2 && (
          <div className="animate-fade-in">
            {/* Sticky Timer Overlay */}
            <div className="fixed top-20 right-6 z-50">
              <div className={`flex items-center gap-2 px-4 py-2 rounded-lg bg-[#111113]/95 backdrop-blur-sm border shadow-lg ${timeLeft <= 10 ? 'border-red-500/50' : timeLeft <= 20 ? 'border-amber-500/50' : 'border-[#27272a]'}`}>
                <Clock className={`w-4 h-4 ${getTimerColor()}`} />
                <span className={`font-mono text-lg font-semibold ${getTimerColor()}`}>
                  {formatTime(timeLeft)}
                </span>
              </div>
            </div>

            <div className="mb-10">
              <div className="flex items-center justify-between mb-6">
                <button
                  onClick={() => setStep(1)}
                  className="flex items-center gap-1 text-[#71717a] hover:text-[#a1a1aa] text-sm"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to idea
                </button>
              </div>
              
              <h1 className="text-3xl font-semibold text-[#fafafa] mb-3 tracking-tight">
                60-Second Challenge
              </h1>
              <p className="text-[#71717a] text-base">
                Answer these {questions.length} questions quickly to generate your AI-optimized PRD.
              </p>
              <div className="mt-4 flex items-center gap-2 text-sm text-[#52525b]">
                <span>{Object.keys(answers).length} of {questions.length} answered</span>
                <div className="flex-1 h-1 bg-[#1f1f23] rounded-full max-w-[200px]">
                  <div 
                    className="h-1 bg-[#fafafa] rounded-full transition-all duration-300"
                    style={{ width: `${(Object.keys(answers).length / questions.length) * 100}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="space-y-6">
              {questions.map((q, index) => (
                <div
                  key={q.id}
                  data-testid={`question-${index}`}
                  className={`bg-[#111113] border rounded-lg p-6 transition-colors ${
                    answers[q.id] ? 'border-[#27272a]' : 'border-[#1f1f23]'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-sm">{getCategoryIcon(q.category)}</span>
                    <span className="text-xs font-medium text-[#52525b] uppercase tracking-wider">
                      {getCategoryLabel(q.category)}
                    </span>
                    <span className="text-xs text-[#3f3f46] ml-auto">
                      {index + 1}/{questions.length}
                    </span>
                  </div>
                  <p className="text-[#fafafa] font-medium mb-5">{q.question}</p>
                  <RadioGroup
                    value={answers[q.id] || ""}
                    onValueChange={(value) =>
                      setAnswers((prev) => ({ ...prev, [q.id]: value }))
                    }
                    className="space-y-2"
                  >
                    {q.options.map((opt) => (
                      <label
                        key={opt.value}
                        htmlFor={`${q.id}-${opt.value}`}
                        className={`flex items-start space-x-3 p-3 rounded-md cursor-pointer group transition-colors ${
                          answers[q.id] === opt.value 
                            ? 'bg-[#1f1f23] border border-[#3f3f46]' 
                            : 'hover:bg-[#18181b] border border-transparent'
                        }`}
                        onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: opt.value }))}
                      >
                        <RadioGroupItem
                          value={opt.value}
                          id={`${q.id}-${opt.value}`}
                          data-testid={`option-${q.id}-${opt.value}`}
                          className="border-[#3f3f46] text-[#fafafa] mt-0.5 shrink-0"
                        />
                        <span
                          className={`leading-relaxed text-sm ${
                            answers[q.id] === opt.value 
                              ? 'text-[#fafafa]' 
                              : 'text-[#a1a1aa] group-hover:text-[#fafafa]'
                          }`}
                        >
                          {opt.label}
                        </span>
                      </label>
                    ))}
                  </RadioGroup>
                </div>
              ))}

              <div className="flex justify-between items-center pt-6 border-t border-[#1f1f23]">
                <p className="text-sm text-[#52525b]">
                  {timeLeft === 0 
                    ? "Time's up! Generate your PRD now."
                    : Object.keys(answers).length === questions.length 
                      ? "All done! Generate your PRD." 
                      : `${questions.length - Object.keys(answers).length} more to go`}
                </p>
                <Button
                  data-testid="generate-prd-btn"
                  onClick={handleGeneratePRD}
                  disabled={loading || Object.keys(answers).length < questions.length}
                  className="bg-[#fafafa] text-[#0a0a0b] hover:bg-[#e4e4e7] font-medium px-6 h-11 rounded-lg disabled:opacity-40"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating PRD...
                    </>
                  ) : (
                    <>
                      Generate Perfect PRD
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Step 2.5: Generating PRD with Tips */}
        {step === 2.5 && (
          <div className="animate-fade-in">
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
              <div className="mb-8">
                <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[#111113] border border-[#27272a] flex items-center justify-center">
                  <Loader2 className="w-8 h-8 text-[#fafafa] animate-spin" />
                </div>
                <h1 className="text-3xl font-semibold text-[#fafafa] mb-3 tracking-tight">
                  Crafting Your PRD
                </h1>
                <p className="text-[#71717a] text-base max-w-md">
                  Our AI is generating a detailed, implementation-ready PRD based on your inputs...
                </p>
              </div>

              {/* Tips Section */}
              <div className="w-full max-w-lg">
                <div className="bg-[#111113] border border-[#1f1f23] rounded-lg p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Lightbulb className="w-5 h-5 text-amber-500" />
                    <span className="text-sm font-medium text-[#a1a1aa] uppercase tracking-wider">
                      PRD Tip {currentTipIndex + 1}/{PRD_TIPS.length}
                    </span>
                  </div>
                  <div className="min-h-[80px]">
                    <h3 className="text-[#fafafa] font-semibold mb-2">
                      {PRD_TIPS[currentTipIndex].title}
                    </h3>
                    <p className="text-[#71717a] text-sm leading-relaxed">
                      {PRD_TIPS[currentTipIndex].description}
                    </p>
                  </div>
                  {/* Progress dots */}
                  <div className="flex justify-center gap-1.5 mt-6">
                    {PRD_TIPS.map((_, i) => (
                      <div
                        key={i}
                        className={`w-1.5 h-1.5 rounded-full transition-colors ${
                          i === currentTipIndex ? 'bg-[#fafafa]' : 'bg-[#3f3f46]'
                        }`}
                      />
                    ))}
                  </div>
                </div>

                <p className="text-[#52525b] text-xs mt-4">
                  This usually takes 30-60 seconds for a comprehensive PRD
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: PRD Output */}
        {step === 3 && (
          <div className="animate-fade-in">
            <div className="mb-8 flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-semibold text-[#fafafa] mb-3 tracking-tight">
                  Your PRD is ready
                </h1>
                <p className="text-[#71717a] text-base">
                  Copy and paste this into Cursor, Lovable, or your preferred AI builder.
                </p>
              </div>
              <div className="flex gap-3">
                <Button
                  data-testid="copy-btn"
                  onClick={handleCopy}
                  variant="outline"
                  className="border-[#27272a] bg-transparent hover:bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa] h-10 px-4 rounded-lg"
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4 mr-2 text-emerald-500" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4 mr-2" />
                      Copy
                    </>
                  )}
                </Button>
                <Button
                  data-testid="new-prd-btn"
                  onClick={handleReset}
                  variant="outline"
                  className="border-[#27272a] bg-transparent hover:bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa] h-10 px-4 rounded-lg"
                >
                  New PRD
                </Button>
              </div>
            </div>

            <div 
              data-testid="prd-output"
              className="bg-[#111113] border border-[#1f1f23] rounded-lg p-8 markdown-content"
            >
              {renderMarkdown(prd)}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default PRDGenerator;
