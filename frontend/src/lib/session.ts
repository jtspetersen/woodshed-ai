const SESSION_KEY = "woodshed-session-id";

/** Generate a random UUID v4. */
function generateId(): string {
  return crypto.randomUUID();
}

/** Get or create a persistent session ID (survives page reloads). */
export function getSessionId(): string {
  if (typeof window === "undefined") {
    // SSR fallback — never stored
    return generateId();
  }

  let id = sessionStorage.getItem(SESSION_KEY);
  if (!id) {
    id = generateId();
    sessionStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

/** Reset the session (new conversation). */
export function resetSessionId(): string {
  const id = generateId();
  if (typeof window !== "undefined") {
    sessionStorage.setItem(SESSION_KEY, id);
  }
  return id;
}
