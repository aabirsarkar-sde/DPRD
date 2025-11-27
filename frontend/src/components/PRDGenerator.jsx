import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { FileText, ChevronRight, Copy, Check, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PRDGenerator = () => {
  const [step, setStep] = useState(1);
  const [idea, setIdea] = useState("");
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [prd, setPrd] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

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
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(prd);
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error("Failed to copy");
    }
  };

  const handleReset = () => {
    setStep(1);
    setIdea("");
    setQuestions([]);
    setAnswers({});
    setPrd("");
    setCopied(false);
  };

  const getCategoryLabel = (category) => {
    const labels = {
      auth: "Authentication",
      data_complexity: "Data Architecture",
      edge_cases: "Edge Cases",
    };
    return labels[category] || category;
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
              <span className={step >= 3 ? "text-[#fafafa]" : ""}>PRD</span>
            </div>
          </div>
        </div>
        <Progress 
          value={step === 1 ? 33 : step === 2 ? 66 : 100} 
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
                Be as messy as you want. Describe your app idea, features, target users — anything.
              </p>
            </div>

            <div className="space-y-6">
              <Textarea
                data-testid="idea-input"
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                placeholder="I want to build an app that..."
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
              <p className="text-[#52525b] text-sm">
                Your idea will be analyzed to identify key decisions needed before generating a complete PRD.
              </p>
            </div>
          </div>
        )}

        {/* Step 2: Clarifying Questions */}
        {step === 2 && (
          <div className="animate-fade-in">
            <div className="mb-10">
              <button
                onClick={() => setStep(1)}
                className="flex items-center gap-1 text-[#71717a] hover:text-[#a1a1aa] text-sm mb-6"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to idea
              </button>
              <h1 className="text-3xl font-semibold text-[#fafafa] mb-3 tracking-tight">
                A few clarifications
              </h1>
              <p className="text-[#71717a] text-base">
                Answer these questions to help generate a precise, implementation-ready PRD.
              </p>
            </div>

            <div className="space-y-8">
              {questions.map((q, index) => (
                <div
                  key={q.id}
                  data-testid={`question-${index}`}
                  className="bg-[#111113] border border-[#1f1f23] rounded-lg p-6"
                >
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-xs font-medium text-[#52525b] uppercase tracking-wider">
                      {getCategoryLabel(q.category)}
                    </span>
                  </div>
                  <p className="text-[#fafafa] font-medium mb-5">{q.question}</p>
                  <RadioGroup
                    value={answers[q.id] || ""}
                    onValueChange={(value) =>
                      setAnswers((prev) => ({ ...prev, [q.id]: value }))
                    }
                    className="space-y-3"
                  >
                    {q.options.map((opt) => (
                      <div
                        key={opt.value}
                        className="flex items-start space-x-3 p-3 rounded-md hover:bg-[#18181b] cursor-pointer group"
                      >
                        <RadioGroupItem
                          value={opt.value}
                          id={`${q.id}-${opt.value}`}
                          data-testid={`option-${q.id}-${opt.value}`}
                          className="border-[#3f3f46] text-[#fafafa] mt-0.5"
                        />
                        <Label
                          htmlFor={`${q.id}-${opt.value}`}
                          className="text-[#a1a1aa] group-hover:text-[#fafafa] cursor-pointer leading-relaxed"
                        >
                          {opt.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>
              ))}

              <div className="flex justify-end pt-4">
                <Button
                  data-testid="generate-prd-btn"
                  onClick={handleGeneratePRD}
                  disabled={loading || Object.keys(answers).length < questions.length}
                  className="bg-[#fafafa] text-[#0a0a0b] hover:bg-[#e4e4e7] font-medium px-6 h-11 rounded-lg"
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
