/**
 * Community Features Type Definitions
 * @version 1.0.0
 * @package @medical-research-platform/web
 */

import { UserProfile } from '../types/auth';

/**
 * Forum interface representing discussion boards
 * Can be general or protocol-specific
 */
export interface Forum {
  /** Unique forum identifier */
  id: string;
  /** Forum name/title */
  name: string;
  /** Forum description */
  description: string;
  /** Whether this is a protocol-specific forum */
  isProtocolSpecific: boolean;
  /** Associated protocol ID if protocol-specific */
  protocolId: string | null;
  /** List of forum moderators */
  moderators: UserProfile[];
  /** Whether the forum is currently active */
  isActive: boolean;
  /** Total number of threads in the forum */
  threadCount: number;
  /** Timestamp of last activity */
  lastActivity: string;
  /** Forum creation timestamp */
  createdAt: string;
  /** Forum last update timestamp */
  updatedAt: string;
}

/**
 * Thread interface representing discussion topics within forums
 */
export interface Thread {
  /** Unique thread identifier */
  id: string;
  /** Parent forum */
  forum: Forum;
  /** Thread author */
  author: UserProfile;
  /** Thread title */
  title: string;
  /** Thread content */
  content: string;
  /** Whether thread is pinned to top */
  isPinned: boolean;
  /** Whether thread is locked for new comments */
  isLocked: boolean;
  /** Whether thread has been moderated */
  isModerated: boolean;
  /** Reason for moderation if applicable */
  moderationReason: string | null;
  /** Number of thread views */
  viewCount: number;
  /** Total number of comments */
  commentCount: number;
  /** Timestamp of last comment */
  lastCommentAt: string | null;
  /** Thread creation timestamp */
  createdAt: string;
  /** Thread last update timestamp */
  updatedAt: string;
}

/**
 * Comment interface for threaded discussions
 * Supports nested comments through parentComment relationship
 */
export interface Comment {
  /** Unique comment identifier */
  id: string;
  /** Parent thread */
  thread: Thread;
  /** Comment author */
  author: UserProfile;
  /** Comment content */
  content: string;
  /** Parent comment if this is a reply */
  parentComment: Comment | null;
  /** Child comments/replies */
  childComments: Comment[];
  /** Whether comment has been edited */
  isEdited: boolean;
  /** Timestamp of last edit */
  lastEditedAt: string | null;
  /** Whether comment has been moderated */
  isModerated: boolean;
  /** Reason for moderation if applicable */
  moderationReason: string | null;
  /** Comment creation timestamp */
  createdAt: string;
  /** Comment last update timestamp */
  updatedAt: string;
}

/**
 * Message interface for direct messaging between users
 */
export interface Message {
  /** Unique message identifier */
  id: string;
  /** Message sender */
  sender: UserProfile;
  /** Message recipient */
  recipient: UserProfile;
  /** Message content */
  content: string;
  /** Whether message has been read */
  isRead: boolean;
  /** Timestamp when message was read */
  readAt: string | null;
  /** Whether message has been moderated */
  isModerated: boolean;
  /** Reason for moderation if applicable */
  moderationReason: string | null;
  /** Message creation timestamp */
  createdAt: string;
}

/**
 * Input type for creating new threads
 */
export interface ThreadCreateInput {
  /** ID of forum to create thread in */
  forumId: string;
  /** Thread title */
  title: string;
  /** Thread content */
  content: string;
}

/**
 * Input type for creating new comments
 */
export interface CommentCreateInput {
  /** ID of thread to comment on */
  threadId: string;
  /** Comment content */
  content: string;
  /** Optional parent comment ID for replies */
  parentCommentId: string | null;
}

/**
 * Input type for sending direct messages
 */
export interface MessageCreateInput {
  /** ID of message recipient */
  recipientId: string;
  /** Message content */
  content: string;
}