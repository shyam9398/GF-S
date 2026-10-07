import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import type { User } from "@supabase/supabase-js";
import { supabase, isSupabaseConfigured, OfficerProfile } from "../services/supabase";

export interface AuthContextType {
  user: User | null;
  profile: OfficerProfile | null;
  loading: boolean;
  isAuthenticated: boolean;
  isSupabaseActive: boolean;
  signIn: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signUp: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper to normalize username: guarantees .bis suffix
export function normalizeBisUsername(raw: string): string {
  let cleaned = (raw || "").trim().toLowerCase();
  if (!cleaned) return "";
  if (cleaned.endsWith(".bis")) {
    return cleaned;
  }
  return `${cleaned}.bis`;
}

// Helper to validate username according to government .bis requirements
export function validateBisUsername(raw: string): { isValid: boolean; error?: string; normalized: string } {
  const trimmed = (raw || "").trim();
  if (!trimmed) {
    return { isValid: false, error: "Username is required.", normalized: "" };
  }

  const normalized = normalizeBisUsername(trimmed);
  // Allowed characters: lowercase letters, numbers, dot, underscore, hyphen
  const validRegex = /^[a-z0-9._-]+$/;
  if (!validRegex.test(normalized)) {
    return {
      isValid: false,
      error: "Username can only contain letters, numbers, dots, hyphens, and underscores.",
      normalized,
    };
  }

  const prefix = normalized.slice(0, -4); // remove '.bis'
  if (!prefix || prefix.length < 3) {
    return {
      isValid: false,
      error: "Username prefix must be at least 3 characters (e.g., officer01.bis).",
      normalized,
    };
  }

  return { isValid: true, normalized };
}

// Convert .bis username into internal email for Supabase Auth
export function bisUsernameToEmail(normalizedUsername: string): string {
  return `${normalizedUsername}@bis.local`;
}

// Local mock fallback for resilience when Supabase anon key is not yet configured
interface LocalMockUser {
  id: string;
  username: string;
  email: string;
  passwordHash: string;
  role: string;
  created_at: string;
}

const LOCAL_STORAGE_USERS_KEY = "bis_mock_officers_v1";
const LOCAL_STORAGE_SESSION_KEY = "bis_mock_session_v1";

function getLocalUsers(): LocalMockUser[] {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_USERS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveLocalUsers(users: LocalMockUser[]) {
  try {
    localStorage.setItem(LOCAL_STORAGE_USERS_KEY, JSON.stringify(users));
  } catch (e) {
    console.error("Failed to save local mock users:", e);
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<OfficerProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Load profile from Supabase procurement_officers table
  const fetchProfile = async (userId: string, defaultUsername?: string): Promise<OfficerProfile | null> => {
    if (!supabase) return null;
    try {
      const { data, error } = await supabase
        .from("procurement_officers")
        .select("*")
        .eq("user_id", userId)
        .maybeSingle();

      if (error) {
        console.warn("Could not query procurement_officers table:", error.message);
      }

      if (data) {
        return data as OfficerProfile;
      }

      // If user profile does not exist yet (e.g. freshly registered), create it
      if (defaultUsername) {
        const newProfile: Partial<OfficerProfile> = {
          user_id: userId,
          username: defaultUsername,
          role: "PROCUREMENT_OFFICER",
        };
        const { data: inserted, error: insertError } = await supabase
          .from("procurement_officers")
          .insert([newProfile])
          .select()
          .maybeSingle();

        if (inserted && !insertError) {
          return inserted as OfficerProfile;
        }
      }

      // Fallback profile object based on user metadata
      return {
        id: userId,
        user_id: userId,
        username: defaultUsername || "officer.bis",
        role: "PROCUREMENT_OFFICER",
      };
    } catch (e) {
      console.error("fetchProfile error:", e);
      return {
        id: userId,
        user_id: userId,
        username: defaultUsername || "officer.bis",
        role: "PROCUREMENT_OFFICER",
      };
    }
  };

  // Initialize session on mount
  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      try {
        if (isSupabaseConfigured && supabase) {
          const { data, error } = await supabase.auth.getSession();
          if (error) {
            console.error("Supabase getSession error:", error);
          }

          if (data?.session?.user && isMounted) {
            const currentU = data.session.user;
            setUser(currentU);
            const username =
              (currentU.user_metadata?.username as string) ||
              currentU.email?.replace("@bis.local", "") ||
              "officer.bis";
            const prof = await fetchProfile(currentU.id, username);
            if (isMounted) setProfile(prof);
          }
        } else {
          // Fallback to local session
          const localSession = localStorage.getItem(LOCAL_STORAGE_SESSION_KEY);
          if (localSession && isMounted) {
            const parsed = JSON.parse(localSession);
            setUser({
              id: parsed.id,
              app_metadata: {},
              user_metadata: { username: parsed.username, role: parsed.role },
              aud: "authenticated",
              created_at: parsed.created_at,
              email: parsed.email,
            } as User);
            setProfile({
              id: parsed.id,
              user_id: parsed.id,
              username: parsed.username,
              role: parsed.role || "PROCUREMENT_OFFICER",
              created_at: parsed.created_at,
            });
          }
        }
      } catch (err) {
        console.error("Auth init error:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    initAuth();

    // Subscribe to Supabase auth state change if configured
    if (isSupabaseConfigured && supabase) {
      const { data: authListener } = supabase.auth.onAuthStateChange(
        async (event, session) => {
          if (!isMounted) return;
          if (session?.user) {
            setUser(session.user);
            const username =
              (session.user.user_metadata?.username as string) ||
              session.user.email?.replace("@bis.local", "") ||
              "officer.bis";
            const prof = await fetchProfile(session.user.id, username);
            if (isMounted) setProfile(prof);
          } else {
            setUser(null);
            setProfile(null);
          }
        }
      );

      return () => {
        isMounted = false;
        authListener.subscription.unsubscribe();
      };
    }

    return () => {
      isMounted = false;
    };
  }, []);

  // Sign In implementation
  const signIn = async (
    rawUsername: string,
    password: string
  ): Promise<{ success: boolean; error?: string }> => {
    const { isValid, error: valError, normalized } = validateBisUsername(rawUsername);
    if (!isValid) {
      return { success: false, error: valError || "Invalid username." };
    }
    if (!password) {
      return { success: false, error: "Password is required." };
    }

    const email = bisUsernameToEmail(normalized);

    // 1. If Supabase is configured, use Supabase Auth
    if (isSupabaseConfigured && supabase) {
      try {
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });

        if (error) {
          // User friendly message mapping
          const msg = error.message.toLowerCase();
          if (msg.includes("invalid login credentials") || msg.includes("invalid credential")) {
            return {
              success: false,
              error: "Invalid username or password. Please verify your officer credentials.",
            };
          }
          if (msg.includes("email not confirmed")) {
            return {
              success: false,
              error: "Account pending confirmation. Please check with the BIS administrator or sign in after activation.",
            };
          }
          return {
            success: false,
            error: "Authentication failed. Please verify your credentials.",
          };
        }

        if (data?.user) {
          setUser(data.user);
          const prof = await fetchProfile(data.user.id, normalized);
          setProfile(prof);
          return { success: true };
        }

        return { success: false, error: "Unable to establish officer session." };
      } catch (e: unknown) {
        console.error("Supabase signIn exception:", e);
        return {
          success: false,
          error: "Connection to BIS Authentication service failed. Please try again.",
        };
      }
    }

    // 2. Local fallback if Supabase anon key not set
    const users = getLocalUsers();
    const found = users.find(
      (u) => u.username.toLowerCase() === normalized.toLowerCase()
    );

    if (!found || found.passwordHash !== password) {
      return {
        success: false,
        error: "Invalid username or password. Please verify your officer credentials.",
      };
    }

    const mockSession = {
      id: found.id,
      username: found.username,
      email: found.email,
      role: found.role,
      created_at: found.created_at,
    };
    localStorage.setItem(LOCAL_STORAGE_SESSION_KEY, JSON.stringify(mockSession));

    setUser({
      id: found.id,
      app_metadata: {},
      user_metadata: { username: found.username, role: found.role },
      aud: "authenticated",
      created_at: found.created_at,
      email: found.email,
    } as User);

    setProfile({
      id: found.id,
      user_id: found.id,
      username: found.username,
      role: found.role,
      created_at: found.created_at,
    });

    return { success: true };
  };

  // Sign Up implementation
  const signUp = async (
    rawUsername: string,
    password: string
  ): Promise<{ success: boolean; error?: string }> => {
    const { isValid, error: valError, normalized } = validateBisUsername(rawUsername);
    if (!isValid) {
      return { success: false, error: valError || "Invalid username." };
    }
    if (!password) {
      return { success: false, error: "Password cannot be empty." };
    }
    if (password.length < 8) {
      return { success: false, error: "Password must be at least 8 characters long." };
    }

    const email = bisUsernameToEmail(normalized);

    // 1. If Supabase is configured, use Supabase Auth
    if (isSupabaseConfigured && supabase) {
      try {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              username: normalized,
              role: "PROCUREMENT_OFFICER",
            },
          },
        });

        if (error) {
          const msg = error.message.toLowerCase();
          if (msg.includes("already registered") || msg.includes("already exists") || msg.includes("user already")) {
            return {
              success: false,
              error: `The username "${normalized}" is already registered. Please sign in instead.`,
            };
          }
          if (msg.includes("password")) {
            return {
              success: false,
              error: "Password does not meet security requirements (minimum 8 characters).",
            };
          }
          return {
            success: false,
            error: "Unable to create officer account. Please check details and try again.",
          };
        }

        if (data?.user) {
          // Insert row into procurement_officers profile table
          try {
            await supabase.from("procurement_officers").insert([
              {
                user_id: data.user.id,
                username: normalized,
                role: "PROCUREMENT_OFFICER",
              },
            ]);
          } catch (profileInsertErr) {
            console.warn("Could not insert profile table row directly:", profileInsertErr);
          }

          // If session was granted immediately (auto-confirm enabled)
          if (data.session) {
            setUser(data.user);
            const prof = await fetchProfile(data.user.id, normalized);
            setProfile(prof);
          } else {
            // Attempt immediate login if auto-confirm is on
            const loginRes = await signIn(normalized, password);
            if (!loginRes.success) {
              // Registration succeeded, user can now sign in
              return { success: true };
            }
          }

          return { success: true };
        }

        return {
          success: false,
          error: "Failed to initialize officer registration.",
        };
      } catch (e: unknown) {
        console.error("Supabase signUp exception:", e);
        return {
          success: false,
          error: "Connection to BIS Authentication service failed. Please try again.",
        };
      }
    }

    // 2. Local fallback if Supabase anon key not set
    const users = getLocalUsers();
    const existing = users.find(
      (u) => u.username.toLowerCase() === normalized.toLowerCase()
    );
    if (existing) {
      return {
        success: false,
        error: `The username "${normalized}" is already registered. Please sign in instead.`,
      };
    }

    const newUser: LocalMockUser = {
      id: `po-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`,
      username: normalized,
      email,
      passwordHash: password,
      role: "PROCUREMENT_OFFICER",
      created_at: new Date().toISOString(),
    };

    users.push(newUser);
    saveLocalUsers(users);

    // Auto sign-in locally
    const mockSession = {
      id: newUser.id,
      username: newUser.username,
      email: newUser.email,
      role: newUser.role,
      created_at: newUser.created_at,
    };
    localStorage.setItem(LOCAL_STORAGE_SESSION_KEY, JSON.stringify(mockSession));

    setUser({
      id: newUser.id,
      app_metadata: {},
      user_metadata: { username: newUser.username, role: newUser.role },
      aud: "authenticated",
      created_at: newUser.created_at,
      email: newUser.email,
    } as User);

    setProfile({
      id: newUser.id,
      user_id: newUser.id,
      username: newUser.username,
      role: newUser.role,
      created_at: newUser.created_at,
    });

    return { success: true };
  };

  // Sign Out implementation
  const signOut = async () => {
    try {
      if (isSupabaseConfigured && supabase) {
        await supabase.auth.signOut();
      }
    } catch (e) {
      console.error("Error signing out:", e);
    } finally {
      localStorage.removeItem(LOCAL_STORAGE_SESSION_KEY);
      setUser(null);
      setProfile(null);
    }
  };

  const isAuthenticated = Boolean(user);

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        loading,
        isAuthenticated,
        isSupabaseActive: isSupabaseConfigured,
        signIn,
        signUp,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
