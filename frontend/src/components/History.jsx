import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Trash2, FileText, Calendar, ArrowLeft, ChevronRight, ChevronLeft, Loader2, Edit2, Check, X, Save, FileMinus, Search, Filter, Tag, ArrowUpDown } from "lucide-react";
import { format } from "date-fns";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuCheckboxItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const History = () => {
    const navigate = useNavigate();
    const [prds, setPrds] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editingId, setEditingId] = useState(null);
    const [editIdea, setEditIdea] = useState("");
    const [editingContentId, setEditingContentId] = useState(null);
    const [editContent, setEditContent] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedTags, setSelectedTags] = useState([]);
    const [availableTags, setAvailableTags] = useState([]);
    const [sortOption, setSortOption] = useState("newest");
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        const timer = setTimeout(() => {
            fetchPrds(searchQuery, selectedTags, sortOption, currentPage);
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery, selectedTags, sortOption, currentPage]);

    const fetchPrds = async (query = "", tags = [], sort = "newest", page = 1) => {
        try {
            const params = { search: query };
            if (tags.length > 0) {
                params.tags = tags.join(",");
            }

            // Add sorting params
            if (sort === "newest") {
                params.sort_by = "created_at";
                params.order = "desc";
            } else if (sort === "oldest") {
                params.sort_by = "created_at";
                params.order = "asc";
            } else if (sort === "alphabetical") {
                params.sort_by = "idea";
                params.order = "asc";
            } else if (sort === "reverse-alphabetical") {
                params.sort_by = "idea";
                params.order = "desc";
            }

            params.page = page;
            params.page_size = 4;

            const response = await axios.get(`${API}/prds`, { params });
            setPrds(response.data.items || []);
            setTotalPages(response.data.pages || 1);

            // Extract unique tags from all loaded PRDs to populate filter
            // (In a real app, you might want a separate endpoint for this)
            const allTags = new Set();
            if (response.data.items) {
                response.data.items.forEach(prd => {
                    if (prd.tags && Array.isArray(prd.tags)) {
                        prd.tags.forEach(tag => allTags.add(tag));
                    }
                });
            }
            setAvailableTags(Array.from(allTags).sort());

        } catch (error) {
            console.error(error);
            toast.error("Failed to load history");
        } finally {
            setLoading(false);
        }
    };

    const toggleTag = (tag) => {
        setCurrentPage(1);
        setSelectedTags(prev =>
            prev.includes(tag)
                ? prev.filter(t => t !== tag)
                : [...prev, tag]
        );
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
                    onClick={() => navigate("/")}
                    className="border-[#27272a] bg-transparent hover:bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa]"
                >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Generator
                </Button>
            </div>

            <div className="flex items-center gap-4 mb-6">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[#71717a] w-4 h-4" />
                    <Input
                        placeholder="Search ideas..."
                        className="pl-9 bg-[#111113] border-[#27272a] text-[#fafafa] placeholder:text-[#52525b] focus:border-[#fafafa] transition-colors"
                        value={searchQuery}
                        onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
                    />
                </div>

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="outline" className="border-[#27272a] bg-[#111113] text-[#a1a1aa] hover:text-[#fafafa] hover:bg-[#1f1f23]">
                            <Filter className="w-4 h-4 mr-2" />
                            Filter
                            {selectedTags.length > 0 && (
                                <Badge variant="secondary" className="ml-2 h-5 px-1.5 bg-[#fafafa] text-[#0a0a0b]">
                                    {selectedTags.length}
                                </Badge>
                            )}
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="w-56 bg-[#18181b] border-[#27272a]">
                        <DropdownMenuLabel className="text-[#fafafa]">Filter by Tag</DropdownMenuLabel>
                        <DropdownMenuSeparator className="bg-[#27272a]" />
                        {availableTags.length === 0 ? (
                            <div className="px-2 py-2 text-sm text-[#71717a]">No tags available</div>
                        ) : (
                            availableTags.map(tag => (
                                <DropdownMenuCheckboxItem
                                    key={tag}
                                    checked={selectedTags.includes(tag)}
                                    onCheckedChange={() => toggleTag(tag)}
                                    className="text-[#a1a1aa] focus:text-[#fafafa] focus:bg-[#27272a]"
                                >
                                    {tag}
                                </DropdownMenuCheckboxItem>
                            ))
                        )}
                        {selectedTags.length > 0 && (
                            <>
                                <DropdownMenuSeparator className="bg-[#27272a]" />
                                <DropdownMenuCheckboxItem
                                    checked={false}
                                    onSelect={() => { setSelectedTags([]); setCurrentPage(1); }}
                                    className="text-red-400 focus:text-red-400 focus:bg-red-400/10 justify-center"
                                >
                                    Clear Filters
                                </DropdownMenuCheckboxItem>
                            </>
                        )}
                    </DropdownMenuContent>
                </DropdownMenu>

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="outline" className="border-[#27272a] bg-[#111113] text-[#a1a1aa] hover:text-[#fafafa] hover:bg-[#1f1f23]">
                            <ArrowUpDown className="w-4 h-4 mr-2" />
                            Sort
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="w-56 bg-[#18181b] border-[#27272a]">
                        <DropdownMenuLabel className="text-[#fafafa]">Sort by</DropdownMenuLabel>
                        <DropdownMenuSeparator className="bg-[#27272a]" />
                        <DropdownMenuCheckboxItem
                            checked={sortOption === "newest"}
                            onCheckedChange={() => { setSortOption("newest"); setCurrentPage(1); }}
                            className="text-[#a1a1aa] focus:text-[#fafafa] focus:bg-[#27272a]"
                        >
                            Newest First
                        </DropdownMenuCheckboxItem>
                        <DropdownMenuCheckboxItem
                            checked={sortOption === "oldest"}
                            onCheckedChange={() => { setSortOption("oldest"); setCurrentPage(1); }}
                            className="text-[#a1a1aa] focus:text-[#fafafa] focus:bg-[#27272a]"
                        >
                            Oldest First
                        </DropdownMenuCheckboxItem>
                        <DropdownMenuCheckboxItem
                            checked={sortOption === "alphabetical"}
                            onCheckedChange={() => { setSortOption("alphabetical"); setCurrentPage(1); }}
                            className="text-[#a1a1aa] focus:text-[#fafafa] focus:bg-[#27272a]"
                        >
                            A-Z
                        </DropdownMenuCheckboxItem>
                        <DropdownMenuCheckboxItem
                            checked={sortOption === "reverse-alphabetical"}
                            onCheckedChange={() => { setSortOption("reverse-alphabetical"); setCurrentPage(1); }}
                            className="text-[#a1a1aa] focus:text-[#fafafa] focus:bg-[#27272a]"
                        >
                            Z-A
                        </DropdownMenuCheckboxItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>

            {
                prds.length === 0 ? (
                    <div className="text-center py-20 bg-[#111113] border border-[#1f1f23] rounded-lg">
                        <FileText className="w-12 h-12 text-[#3f3f46] mx-auto mb-4" />
                        <h3 className="text-[#fafafa] font-medium mb-2">No saved PRDs yet</h3>
                        <p className="text-[#71717a] mb-6">Generate your first PRD to see it here.</p>
                        <Button
                            onClick={() => navigate("/")}
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
                                onClick={() => navigate(`/prd/${prd.id}`)}
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
                                                    <Button size="icon" variant="ghost" className="h-8 w-8 text-red-500 hover:bg-red-500/10" onClick={(e) => { e.stopPropagation(); cancelEditing(); }}>
                                                        <X className="w-4 h-4" />
                                                    </Button>
                                                </div>
                                            ) : (
                                                <div className="flex flex-col gap-2 mb-2 group/title">
                                                    <div className="flex items-center gap-2">
                                                        <h3 className="text-[#fafafa] font-medium text-lg truncate group-hover:text-white transition-colors">
                                                            {prd.idea}
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
                                                    {prd.tags && prd.tags.length > 0 && (
                                                        <div className="flex flex-wrap gap-2">
                                                            {prd.tags.map(tag => (
                                                                <Badge key={tag} variant="secondary" className="bg-[#27272a] text-[#a1a1aa] hover:bg-[#3f3f46] border-none text-[10px] h-5 px-1.5">
                                                                    {tag}
                                                                </Badge>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>

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
                                    </div>

                                    {editingContentId === prd.id && (
                                        <div className="mt-4 pt-4 border-t border-[#1f1f23]" onClick={(e) => e.stopPropagation()}>
                                            <Textarea
                                                value={editContent}
                                                onChange={(e) => setEditContent(e.target.value)}
                                                className="min-h-[200px] mb-4 bg-[#1f1f23] border-[#3f3f46] text-[#fafafa] font-mono text-sm"
                                            />
                                            <div className="flex justify-between">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => clearContent(prd.id)}
                                                    className="text-red-400 border-red-400/20 hover:bg-red-400/10 hover:text-red-300"
                                                >
                                                    <FileMinus className="w-4 h-4 mr-2" />
                                                    Clear Content
                                                </Button>
                                                <div className="flex gap-2">
                                                    <Button size="sm" variant="ghost" onClick={cancelContentEditing} className="text-[#a1a1aa] hover:text-[#fafafa]">
                                                        Cancel
                                                    </Button>
                                                    <Button size="sm" onClick={(e) => saveContentEditing(e, prd.id)} className="bg-[#fafafa] text-[#0a0a0b] hover:bg-[#e4e4e7]">
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

            {/* Pagination Controls */}
            {prds.length > 0 && (
                <div className="flex items-center justify-between mt-8 pt-4 border-t border-[#1f1f23]">
                    <Button
                        variant="outline"
                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                        disabled={currentPage === 1}
                        className="border-[#27272a] bg-transparent hover:bg-[#1f1f23] text-[#a1a1aa] hover:text-[#fafafa]"
                    >
                        <ChevronLeft className="w-4 h-4 mr-2" />
                        Previous
                    </Button>
                    <span className="text-sm text-[#71717a]">
                        Page <span className="text-[#fafafa] font-medium">{currentPage}</span> of <span className="text-[#fafafa] font-medium">{totalPages}</span>
                    </span>
                    <Button
                        variant="outline"
                        onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                        disabled={currentPage === totalPages}
                        className="border-[#27272a] bg-transparent hover:bg-[#1f1f23] text-[#a1a1aa] hover:text-[#fafafa]"
                    >
                        Next
                        <ChevronRight className="w-4 h-4 ml-2" />
                    </Button>
                </div>
            )}
        </div>
    );
};

export default History;
