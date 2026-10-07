import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL || "https://fflyccwcydbcqdzlmwjw.supabase.co").trim();
const supabaseAnonKey = (import.meta.env.VITE_SUPABASE_ANON_KEY || "").trim();

export const isSupabaseConfigured = Boolean(
  supabaseUrl && 
  supabaseAnonKey && 
  supabaseAnonKey.length > 10 &&
  !supabaseAnonKey.includes("YOUR_")
);

export const supabase: SupabaseClient | null = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    })
  : null;

export const BIS_DOMAIN = "@bis.local";
export const BIS_ROLE = "PROCUREMENT_OFFICER";

export interface OfficerProfile {
  id: string;
  user_id: string;
  username: string;
  role: string;
  created_at?: string;
  updated_at?: string;
}
