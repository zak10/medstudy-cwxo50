/**
 * Community Features Store Module
 * @version 1.0.0
 * @package @medical-research-platform/web
 */

import { defineStore } from 'pinia'; // ^2.1.0
import { ref, computed } from 'vue'; // ^3.3.0
import { useWebSocket } from '@vueuse/core'; // ^10.0.0
import type { Forum, Thread, Comment, Message, ThreadCreateInput, CommentCreateInput, MessageCreateInput } from '../types/community';
import type { UserProfile } from '../types/auth';

// Constants
const DEFAULT_PAGE_SIZE = 20;
const INITIAL_PAGE = 1;
const WEBSOCKET_RETRY_DELAY = 5000;
const MAX_THREAD_DEPTH = 5;

interface PaginationMeta {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  hasNextPage: boolean;
}

interface CommunityState {
  forums: Forum[];
  threads: Map<string, Thread[]>;
  comments: Map<string, Comment[]>;
  messages: Message[];
  activeUsers: Map<string, UserProfile>;
  typingUsers: Set<string>;
  loadingStates: {
    forums: boolean;
    threads: boolean;
    comments: boolean;
    messages: boolean;
  };
  errors: {
    forums: Error | null;
    threads: Error | null;
    comments: Error | null;
    messages: Error | null;
  };
  pagination: {
    forums: PaginationMeta;
    threads: Map<string, PaginationMeta>;
    messages: PaginationMeta;
  };
}

export const useCommunityStore = defineStore('community', () => {
  // State
  const state = ref<CommunityState>({
    forums: [],
    threads: new Map(),
    comments: new Map(),
    messages: [],
    activeUsers: new Map(),
    typingUsers: new Set(),
    loadingStates: {
      forums: false,
      threads: false,
      comments: false,
      messages: false
    },
    errors: {
      forums: null,
      threads: null,
      comments: null,
      messages: null
    },
    pagination: {
      forums: {
        currentPage: INITIAL_PAGE,
        totalPages: 0,
        totalItems: 0,
        hasNextPage: false
      },
      threads: new Map(),
      messages: {
        currentPage: INITIAL_PAGE,
        totalPages: 0,
        totalItems: 0,
        hasNextPage: false
      }
    }
  });

  // WebSocket Setup
  const { status: wsStatus, data: wsData, send: wsSend } = useWebSocket('ws://api/community', {
    autoReconnect: {
      retries: Infinity,
      delay: WEBSOCKET_RETRY_DELAY
    },
    heartbeat: {
      message: 'ping',
      interval: 30000
    }
  });

  // Computed Properties
  const moderatedForums = computed(() => {
    return state.value.forums.filter(forum => forum.isModerated);
  });

  const pinnedThreads = computed(() => {
    const allThreads: Thread[] = [];
    state.value.threads.forEach(threads => {
      allThreads.push(...threads.filter(thread => thread.isPinned));
    });
    return allThreads.sort((a, b) => 
      new Date(b.lastCommentAt || b.createdAt).getTime() - 
      new Date(a.lastCommentAt || a.createdAt).getTime()
    );
  });

  const unreadMessageCount = computed(() => {
    return state.value.messages.filter(msg => !msg.isRead).length;
  });

  // Actions
  async function fetchForums(protocolId: string | null = null, page = INITIAL_PAGE, moderatorId: string | null = null) {
    state.value.loadingStates.forums = true;
    state.value.errors.forums = null;

    try {
      const response = await fetch('/api/forums', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          protocolId,
          moderatorId,
          page,
          pageSize: DEFAULT_PAGE_SIZE
        })
      });

      if (!response.ok) throw new Error('Failed to fetch forums');

      const { data, meta } = await response.json();
      state.value.forums = data;
      state.value.pagination.forums = meta;

      // Subscribe to forum updates via WebSocket
      if (wsStatus.value === 'OPEN') {
        wsSend(JSON.stringify({
          type: 'subscribe',
          entity: 'forums',
          ids: data.map((f: Forum) => f.id)
        }));
      }
    } catch (error) {
      state.value.errors.forums = error as Error;
      throw error;
    } finally {
      state.value.loadingStates.forums = false;
    }
  }

  async function fetchThreads(forumId: string, page = INITIAL_PAGE) {
    state.value.loadingStates.threads = true;
    state.value.errors.threads = null;

    try {
      const response = await fetch(`/api/forums/${forumId}/threads`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          page,
          pageSize: DEFAULT_PAGE_SIZE
        })
      });

      if (!response.ok) throw new Error('Failed to fetch threads');

      const { data, meta } = await response.json();
      state.value.threads.set(forumId, data);
      state.value.pagination.threads.set(forumId, meta);

      // Subscribe to thread updates
      if (wsStatus.value === 'OPEN') {
        wsSend(JSON.stringify({
          type: 'subscribe',
          entity: 'threads',
          forumId,
          ids: data.map((t: Thread) => t.id)
        }));
      }
    } catch (error) {
      state.value.errors.threads = error as Error;
      throw error;
    } finally {
      state.value.loadingStates.threads = false;
    }
  }

  async function createThread(input: ThreadCreateInput) {
    try {
      const response = await fetch('/api/threads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(input)
      });

      if (!response.ok) throw new Error('Failed to create thread');

      const newThread = await response.json();
      const forumThreads = state.value.threads.get(input.forumId) || [];
      state.value.threads.set(input.forumId, [newThread, ...forumThreads]);

      return newThread;
    } catch (error) {
      throw error;
    }
  }

  // WebSocket Message Handler
  function handleWebSocketMessage(event: MessageEvent) {
    const message = JSON.parse(event.data);

    switch (message.type) {
      case 'forum_update':
        updateForum(message.data);
        break;
      case 'thread_update':
        updateThread(message.data);
        break;
      case 'new_message':
        handleNewMessage(message.data);
        break;
      case 'user_typing':
        handleUserTyping(message.data);
        break;
    }
  }

  // Cleanup function
  function cleanup() {
    state.value.forums = [];
    state.value.threads.clear();
    state.value.comments.clear();
    state.value.messages = [];
    state.value.activeUsers.clear();
    state.value.typingUsers.clear();
  }

  return {
    // State
    forums: computed(() => state.value.forums),
    threads: computed(() => state.value.threads),
    comments: computed(() => state.value.comments),
    messages: computed(() => state.value.messages),
    loadingStates: computed(() => state.value.loadingStates),
    errors: computed(() => state.value.errors),
    
    // Computed
    moderatedForums,
    pinnedThreads,
    unreadMessageCount,
    
    // Actions
    fetchForums,
    fetchThreads,
    createThread,
    cleanup,
    
    // WebSocket Status
    wsStatus: computed(() => wsStatus.value)
  };
});