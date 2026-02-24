"use client";

import { useEffect, useState } from "react";
import type { StatusResponse } from "@/lib/types";
import { getStatus } from "@/lib/api";

const POLL_INTERVAL = 30_000;

export function useStatus() {
  const [status, setStatus] = useState<StatusResponse | null>(null);

  useEffect(() => {
    let mounted = true;

    async function poll() {
      try {
        const data = await getStatus();
        if (mounted) setStatus(data);
      } catch {
        if (mounted) setStatus(null);
      }
    }

    poll();
    const id = setInterval(poll, POLL_INTERVAL);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, []);

  return { status };
}
