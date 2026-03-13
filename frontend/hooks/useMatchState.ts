"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { getMatchState } from "@/lib/api";
import type { MatchState } from "@/lib/types";

const POLL_INTERVAL_MS = 1200;

export function useMatchState(matchId: string, active: boolean = true) {
  const [state, setState] = useState<MatchState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchState = useCallback(async () => {
    try {
      const data = await getMatchState(matchId);
      setState(data);
      setError(null);
      // Stop polling once finished
      if (data.status === "finished" || data.status === "cancelled") {
        if (intervalRef.current) clearInterval(intervalRef.current);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [matchId]);

  useEffect(() => {
    if (!active) return;
    fetchState();
    intervalRef.current = setInterval(fetchState, POLL_INTERVAL_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [active, fetchState]);

  return { state, error, loading, refetch: fetchState };
}
