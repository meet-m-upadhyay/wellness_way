import React, { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { 
    History, 
    ChevronRight, 
    ChevronDown, 
    ChevronUp, 
    Sparkles, 
    Utensils, 
    Calendar,
    MessageCircle,
    User,
    Bot,
    Loader2,
    AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import apiClient, { Chat, Message } from '../services/api';

const HistoryView: React.FC = () => {
    const { user } = useAuth();
    const [chats, setChats] = useState<Chat[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedChatId, setExpandedChatId] = useState<string | null>(null);
    const [detailedChats, setDetailedChats] = useState<Record<string, Message[]>>({});

    useEffect(() => {
        if (user?.id) {
            fetchChats(user.id);
        }
    }, [user?.id]);

    const fetchChats = async (userId: string) => {
        setLoading(true);
        const response = await apiClient.getChats(userId);
        if (response.data) {
            setChats(response.data);
        } else {
            setError(response.error || 'Failed to fetch history');
        }
        setLoading(false);
    };

    const handleExpandChat = async (chatId: string) => {
        if (!user?.id) return;
        
        if (expandedChatId === chatId) {
            setExpandedChatId(null);
            return;
        }

        setExpandedChatId(chatId);
        
        // Fetch details if not already loaded
        if (!detailedChats[chatId]) {
            const response = await apiClient.getChatDetail(chatId, user.id);
            if (response.data && response.data.messages) {
                setDetailedChats(prev => ({
                    ...prev,
                    [chatId]: response.data!.messages || []
                }));
            }
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getIconForMetadata = (metadata: any) => {
        if (!metadata) return null;
        if (metadata.scope === 'meal') return <Utensils size={14} className="text-emerald-500" />;
        if (metadata.scope === 'day') return <Calendar size={14} className="text-blue-500" />;
        if (metadata.scope === 'full_plan') return <Sparkles size={14} className="text-purple-500" />;
        return null;
    };

    if (loading && chats.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <Loader2 className="animate-spin text-emerald-600 mb-4" size={48} />
                <p className="text-neutral-500 font-medium">Loading your journey...</p>
            </div>
        );
    }

    return (
        <div className="max-w-5xl mx-auto px-4 py-8 animate-page-enter">
            {/* Breadcrumbs */}
            <nav className="flex items-center gap-2 text-sm text-neutral-500 mb-8">
                <RouterLink to="/" className="hover:text-emerald-600 transition-colors">Dashboard</RouterLink>
                <ChevronRight size={14} />
                <span className="text-neutral-900 dark:text-white font-medium">Conversation History</span>
            </nav>

            {/* Header */}
            <div className="flex items-center gap-4 mb-10">
                <div className="h-14 w-14 rounded-2xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center text-emerald-600">
                    <History size={32} />
                </div>
                <div>
                    <h1 className="text-3xl font-bold text-neutral-900 dark:text-white tracking-tight">Your Journey</h1>
                    <p className="text-neutral-500 dark:text-neutral-400">Review your past diet consultations and refinements</p>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-4 flex items-center gap-3 text-red-700 dark:text-red-400 mb-6">
                    <AlertCircle size={20} />
                    <p className="font-medium">{error}</p>
                </div>
            )}

            {chats.length === 0 ? (
                <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-[32px] p-12 text-center shadow-sm">
                    <div className="h-20 w-20 bg-neutral-50 dark:bg-neutral-800 rounded-full flex items-center justify-center text-neutral-300 dark:text-neutral-600 mx-auto mb-6">
                        <MessageCircle size={40} />
                    </div>
                    <h3 className="text-xl font-bold text-neutral-900 dark:text-white mb-2">No history yet</h3>
                    <p className="text-neutral-500 max-w-md mx-auto mb-8">
                        Start generating personalized diet plans or refining your current meals to see your conversation history here.
                    </p>
                    <RouterLink 
                        to="/diet-plans" 
                        className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-2xl transition-all hover:scale-105 active:scale-95"
                    >
                        Generate Your First Plan
                    </RouterLink>
                </div>
            ) : (
                <div className="space-y-4">
                    {chats.map((chat) => (
                        <div 
                            key={chat.id} 
                            className={`bg-white dark:bg-neutral-900 border transition-all duration-300 rounded-[24px] overflow-hidden ${
                                expandedChatId === chat.id 
                                ? 'border-emerald-500/30 ring-1 ring-emerald-500/10 shadow-xl' 
                                : 'border-neutral-200 dark:border-neutral-800 shadow-sm hover:border-emerald-500/20 hover:shadow-md'
                            }`}
                        >
                            <button 
                                onClick={() => handleExpandChat(chat.id)}
                                className="w-full text-left px-8 py-6 flex items-center justify-between group"
                            >
                                <div className="space-y-1">
                                    <h3 className="text-lg font-bold text-neutral-900 dark:text-white group-hover:text-emerald-600 transition-colors">
                                        {chat.title || 'Diet Consultation'}
                                    </h3>
                                    <div className="flex items-center gap-3 text-sm text-neutral-500">
                                        <span>{formatDate(chat.created_at)}</span>
                                        <span className="h-1 w-1 rounded-full bg-neutral-300"></span>
                                        <span className="font-medium text-neutral-700 dark:text-neutral-400">
                                            {detailedChats[chat.id]?.length || '?'} interaction(s)
                                        </span>
                                    </div>
                                </div>
                                <div className={`h-10 w-10 rounded-xl flex items-center justify-center transition-all ${
                                    expandedChatId === chat.id 
                                    ? 'bg-emerald-500 text-white rotate-0' 
                                    : 'bg-neutral-50 dark:bg-neutral-800 text-neutral-400 rotate-0'
                                }`}>
                                    {expandedChatId === chat.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                                </div>
                            </button>
                            
                            {expandedChatId === chat.id && (
                                <div className="px-8 pb-10 border-t border-neutral-100 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-950/20">
                                    <div className="pt-8 space-y-8">
                                        {(detailedChats[chat.id] || []).map((msg, idx) => (
                                            <div 
                                                key={msg.id} 
                                                className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                                            >
                                                {/* Avatar */}
                                                <div className={`h-10 w-10 rounded-2xl flex-shrink-0 flex items-center justify-center ${
                                                    msg.role === 'user' 
                                                    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600' 
                                                    : 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600'
                                                }`}>
                                                    {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                                                </div>

                                                {/* Message content */}
                                                <div className={`space-y-2 max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                                    <div className={`px-5 py-4 rounded-[20px] shadow-sm flex flex-col gap-2 ${
                                                        msg.role === 'user' 
                                                        ? 'bg-emerald-600 text-white rounded-tr-none' 
                                                        : 'bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white rounded-tl-none'
                                                    }`}>
                                                        <div className="flex items-center justify-between gap-4">
                                                            <div className="flex items-center gap-2">
                                                                {getIconForMetadata(msg.metadata_json)}
                                                                <span className="text-[10px] font-black uppercase tracking-widest opacity-70">
                                                                    {msg.role === 'user' ? 'Patient' : 'AI Dietitian'}
                                                                </span>
                                                            </div>
                                                            <span className="text-[10px] opacity-50 font-medium">
                                                                {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                            </span>
                                                        </div>
                                                        <p className="text-sm leading-relaxed whitespace-pre-wrap font-medium">
                                                            {msg.content}
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default HistoryView;
