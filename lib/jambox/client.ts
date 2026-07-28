import type {
  JamBoxRoom,
  JamBoxUser,
  SpotifyProfile,
} from "../../types/jambox";

const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"
).replace(/\/$/, "");

export class JamBoxApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;

    throw new JamBoxApiError(
      body?.detail ?? `JamBox isteği başarısız: ${response.status}`,
      response.status,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function registerJamBoxUser(
  profile: SpotifyProfile,
): Promise<JamBoxUser> {
  return apiFetch<JamBoxUser>("/users", {
    method: "POST",
    body: JSON.stringify({
      spotify_id: profile.id,
      display_name: profile.display_name || "Spotify user",
      avatar_url: profile.images?.[0]?.url ?? null,
    }),
  });
}

export async function createJamBoxRoom(
  userId: string,
  name: string,
): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>("/rooms", {
    method: "POST",
    headers: { "X-User-Id": userId },
    body: JSON.stringify({ name: name.trim() }),
  });
}

export async function joinJamBoxRoom(
  userId: string,
  code: string,
): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>(
    `/rooms/${encodeURIComponent(code.trim().toUpperCase())}/join`,
    {
      method: "POST",
      headers: { "X-User-Id": userId },
    },
  );
}

export async function leaveJamBoxRoom(
  userId: string,
  code: string,
): Promise<void> {
  return apiFetch<void>(
    `/rooms/${encodeURIComponent(code)}/leave`,
    {
      method: "POST",
      headers: { "X-User-Id": userId },
    },
  );
}

export async function closeJamBoxRoom(
  userId: string,
  code: string,
): Promise<void> {
  return apiFetch<void>(`/rooms/${encodeURIComponent(code)}`, {
    method: "DELETE",
    headers: { "X-User-Id": userId },
  });
}
