"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api";

interface State<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Generic data-fetching hook used across every dashboard page: handles
 * loading/error/empty states consistently and supports polling + manual
 * refetch, so pages don't each re-implement this.
 */
export function useApiQuery<T>(fetcher: () => Promise<T>, deps: unknown[] = [], options?: { pollMs?: number }) {
  const [state, setState] = useState<State<T>>({ data: null, loading: true, error: null });
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refetch = useCallback(async () => {
    setState((s) => ({ ...s, loading: s.data === null, error: null }));
    try {
      const data = await fetcherRef.current();
      setState({ data, loading: false, error: null });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setState((s) => ({ ...s, loading: false, error: message }));
    }
  }, []);

  useEffect(() => {
    refetch();
    if (options?.pollMs) {
      const id = setInterval(refetch, options.pollMs);
      return () => clearInterval(id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { ...state, refetch };
}
