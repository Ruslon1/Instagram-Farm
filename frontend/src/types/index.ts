export interface Account {
  username: string;
  theme: string;
  status: string;
  posts_count: number;
  last_login?: string;
}

export interface AccountCreate {
  username: string;
  password: string;
  theme: string;
  two_fa_key?: string;
}

export interface Video {
  link: string;
  theme: string;
  status: string;
  created_at?: string;
}

export interface TikTokSource {
  id: number;
  theme: string;
  tiktok_username: string;
  active: boolean;
  last_fetch?: string;
  videos_count: number;
  created_at: string;
}

export interface TikTokSourceCreate {
  theme: string;
  tiktok_username: string;
  active: boolean;
}

export interface TaskLog {
  id: string;
  task_type: string;
  status: string;
  created_at: string;
  account_username?: string;
  message?: string;
  progress?: number;
  total_items?: number;
  current_item?: string;
  next_action_at?: string;
  cooldown_seconds?: number;
}

export interface TaskProgress {
  task_id: string;
  status: string;
  progress: number;
  total_items: number;
  current_item?: string;
  message?: string;
  account_username?: string;
  remaining_cooldown?: number;
  created_at: string;
}

export interface Stats {
  active_accounts: number;
  pending_videos: number;
  posts_today: number;
  running_tasks: number;
}

export interface FetchRequest {
  theme: string;
  source_usernames: string[];
  videos_per_account: number;
}

export interface UploadRequest {
  account_username: string;
  video_links: string[];
}