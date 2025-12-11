import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Trash2, FileText, Calendar, ArrowLeft, ChevronRight, Loader2, Edit2, Check, X, Save, FileMinus } from "lucide-react";
import { format } from "date-fns";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const History = ({ onBack, onSelectPrd }) => {
    const [prds, setPrds] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editingId, setEditingId] = useState(null);
    const [editIdea, setEditIdea] = useState("");
    const [editingContentId, setEditingContentId] = useState(null);
    const [editContent, setEditContent] = useState("");

    useEffect(() => {
        fetchPrds();
    }, []);

    const fetchPrds = async () => {
        try {
            const response = await axios.get(`${API}/prds`);
            setPrds(response.data);
        } catch (error) {
            console.error(error);
            toast.error("Failed to load history");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (e, id) => {
        e.stopPropagation();
        if (!window.confirm("Are you sure you want to delete this PRD?")) return;

        try {
            await axios.delete(`${API}/prds/${id}`);
            setPrds(prds.filter(p => p.id !== id));
            toast.success("PRD deleted");
        } catch (error) {
            console.error(error);
            toast.error("Failed to delete PRD");
        }
    };

    const startEditing = (e, prd) => {
        e.stopPropagation();
        setEditingId(prd.id);
        setEditIdea(prd.idea);
    };

    const cancelEditing = () => {
        setEditingId(null);
        setEditIdea("");
    };

    const saveEditing = async (e, id) => {
        e.stopPropagation();
        if (!editIdea.trim()) {
            toast.error("PRD idea cannot be empty.");
            return;
        }
        try {
            const response = await axios.patch(`${API}/prds/${id}/idea`, { idea: editIdea });
            setPrds(prds.map(p => p.id === id ? { ...p, idea: response.data.idea } : p));
            toast.success("PRD idea updated");
            cancelEditing();
        } catch (error) {
            console.error(error);
            toast.error("Failed to update PRD idea");
        }
    };

    const startEditingContent = (e, prd) => {
        e.stopPropagation();
        setEditingContentId(prd.id);
        setEditContent(prd.content);
    };

    const cancelContentEditing = () => {
        setEditingContentId(null);
        setEditContent("");
    };

    const saveContentEditing = async (e, id) => {
        e.stopPropagation();
        if (!editContent.trim()) {
            toast.error("PRD content cannot be empty.");
            return;
        }
        try {
            const response = await axios.put(`${API}/prds/${id}/content`, { content: editContent });
            setPrds(prds.map(p => p.id === id ? { ...p, content: response.data.content } : p));
            toast.success("PRD content updated");
            cancelContentEditing();
        } catch (error) {
            console.error(error);
            toast.error("Failed to update PRD content");
        }
    };

    const clearContent = async (e, id) => {
        e.stopPropagation();
        if (!window.confirm("Are you sure you want to clear the content? This cannot be undone.")) return;

        try {
            const response = await axios.delete(`${API}/prds/${id}/content`);
            setPrds(prds.map(p => p.id === id ? { ...p, content: response.data.content } : p));
            setEditContent("");
            toast.success("PRD content cleared");
        } catch (error) {
            console.error(error);
            toast.error("Failed to clear content");
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="w-8 h-8 text-[#fafafa] animate-spin" />
            </div>
        );
    }

    return (
        <div className="animate-fade-in max-w-4xl mx-auto px-6 py-12">
            <div className="mb-10 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-semibold text-[#fafafa] mb-3 tracking-tight">
                        Your PRD Library
                    </h1>
                    <p className="text-[#71717a] text-base">
                        Manage your generated requirements documents.
                    </p>
                </div>
                <Button
                    variant="outline"
                    onClick={onBack}
                    className="border-[#27272a] bg-transparent hover:bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa]"
                >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Generator
                </Button>
            </div>

            {prds.length === 0 ? (
                <div className="text-center py-20 bg-[#111113] border border-[#1f1f23] rounded-lg">
                    <FileText className="w-12 h-12 text-[#3f3f46] mx-auto mb-4" />
                    <h3 className="text-[#fafafa] font-medium mb-2">No saved PRDs yet</h3>
                    <p className="text-[#71717a] mb-6">Generate your first PRD to see it here.</p>
                    <Button
                        onClick={onBack}
                        className="bg-[#fafafa] text-[#0a0a0b] hover:bg-[#e4e4e7]"
                    >
                        Create New PRD
                    </Button>
                </div>
            ) : (
                <div className="grid gap-4">
                    {prds.map((prd) => (
                        <div
                            key={prd.id}
                            onClick={() => onSelectPrd(prd)}
                            className="group bg-[#111113] border border-[#1f1f23] hover:border-[#3f3f46] p-6 rounded-lg cursor-pointer transition-all hover:bg-[#18181b]/50"
                        >
                            <div className="flex flex-col gap-4">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0 mr-4">
                                        {editingId === prd.id ? (
                                            <div className="flex items-center gap-2 mb-2" onClick={(e) => e.stopPropagation()}>
                                                <Input
                                                    value={editIdea}
                                                    onChange={(e) => setEditIdea(e.target.value)}
                                                    className="bg-[#1f1f23] border-[#3f3f46] text-[#fafafa] h-8"
                                                />
                                                <Button size="icon" variant="ghost" className="h-8 w-8 text-emerald-500 hover:bg-emerald-500/10" onClick={(e) => saveEditing(e, prd.id)}>
                                                    <Check className="w-4 h-4" />
                                                </Button>
                                                <Button size="icon" variant="ghost" className="h-8 w-8 text-red-500 hover:bg-red-500/10" onClick={cancelEditing}>
                                                    <X className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        ) : (
                                            <div className="flex items-center gap-2 mb-2 group/title">
                                                <h3 className="text-[#fafafa] font-medium text-lg truncate group-hover:text-white transition-colors">
                                                    {prd.idea.substring(0, 80)}{prd.idea.length > 80 ? "..." : ""}
                                                </h3>
                                                <Button
                                                    size="icon"
                                                    variant="ghost"
                                                    className="h-6 w-6 text-[#52525b] hover:text-[#a1a1aa] opacity-0 group-hover/title:opacity-100"
                                                    onClick={(e) => startEditing(e, prd)}
                                                >
                                                    <Edit2 className="w-3 h-3" />
                                                </Button>
                                            </div>
                                        )}

                                        <div className="flex items-center gap-4 text-sm text-[#52525b]">
                                            <div className="flex items-center gap-1.5">
                                                <Calendar className="w-3.5 h-3.5" />
                                                {format(new Date(prd.created_at), "MMM d, yyyy • h:mm a")}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={(e) => startEditingContent(e, prd)}
                                            className="text-[#52525b] hover:text-[#fafafa] hover:bg-[#1f1f23] opacity-0 group-hover:opacity-100"
                                        >
                                            <FileText className="w-4 h-4 mr-2" />
                                            Edit Content
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={(e) => handleDelete(e, prd.id)}
                                            className="text-[#52525b] hover:text-red-400 hover:bg-red-400/10 opacity-0 group-hover:opacity-100 transition-all"
                                            title="Delete PRD"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </Button>
                                        <ChevronRight className="w-5 h-5 text-[#3f3f46] group-hover:text-[#a1a1aa] transition-colors" />
                                    </div>
                                </div>

                                {editingContentId === prd.id && (
                                    <div className="mt-4 pt-4 border-t border-[#1f1f23]" onClick={(e) => e.stopPropagation()}>
                                        <Textarea
                                            value={editContent}
                                            onChange={(e) => setEditContent(e.target.value)}
                                            className="min-h-[300px] bg-[#0a0a0b] border-[#27272a] text-[#fafafa] font-mono text-sm mb-4"
                                        />
                                        <div className="flex justify-between items-center">
                                            <Button
                                                variant="ghost"
                                                onClick={(e) => clearContent(e, prd.id)}
                                                className="text-red-400 hover:text-red-300 hover:bg-red-400/10"
                                            >
                                                <FileMinus className="w-4 h-4 mr-2" />
                                                Clear Content
                                            </Button>
                                            <div className="flex gap-2">
                                                <Button variant="ghost" onClick={cancelContentEditing} className="text-[#a1a1aa] hover:text-[#fafafa]">
                                                    Cancel
                                                </Button>
                                                <Button onClick={(e) => saveContentEditing(e, prd.id)} className="bg-[#fafafa] text-[#0a0a0b] hover:bg-[#e4e4e7]">
                                                    <Save className="w-4 h-4 mr-2" />
                                                    Save Changes
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default History;
