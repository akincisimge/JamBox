import type {
  SpotifyPlaylist,
  SpotifyPlaylistItem,
  SpotifyProfile,
  SpotifyTrack,
} from "../../types/jambox";

const SPOTIFY_API_URL = "https://api.spotify.com/v1";
const SPOTIFY_ACCOUNTS_URL = "https://accounts.spotify.com";

export const spotifyStorage = {
  profile: "spotify_profile",
  accessToken: "spotify_access_token",
  refreshToken: "spotify_refresh_token",
  expiresAt: "spotify_expires_at",
  codeVerifier: "spotify_code_verifier",
} as const;

export function readStoredSpotifyProfile(): SpotifyProfile | null {
  const savedProfile = localStorage.getItem(spotifyStorage.profile);
  if (!savedProfile) return null;

  try {
    return JSON.parse(savedProfile) as SpotifyProfile;
  } catch {
    localStorage.removeItem(spotifyStorage.profile);
    return null;
  }
}

export async function getSpotifyAccessToken(): Promise<string> {
  const accessToken = localStorage.getItem(spotifyStorage.accessToken);
  if (!accessToken) {
    throw new Error("Spotify oturumu bulunamadı. Tekrar giriş yapmalısın.");
  }

  const expiresAt = Number(localStorage.getItem(spotifyStorage.expiresAt) ?? 0);
  if (!expiresAt || Date.now() < expiresAt - 30_000) {
    return accessToken;
  }

  const refreshToken = localStorage.getItem(spotifyStorage.refreshToken);
  const clientId = process.env.NEXT_PUBLIC_SPOTIFY_CLIENT_ID;
  if (!refreshToken || !clientId) {
    throw new Error("Spotify oturumunun süresi doldu. Tekrar giriş yapmalısın.");
  }

  const response = await fetch(`${SPOTIFY_ACCOUNTS_URL}/api/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: clientId,
      grant_type: "refresh_token",
      refresh_token: refreshToken,
    }),
  });
  if (!response.ok) {
    throw new Error("Spotify oturumu yenilenemedi. Tekrar giriş yapmalısın.");
  }

  const token = (await response.json()) as {
    access_token: string;
    expires_in: number;
    refresh_token?: string;
  };
  localStorage.setItem(spotifyStorage.accessToken, token.access_token);
  localStorage.setItem(
    spotifyStorage.expiresAt,
    String(Date.now() + token.expires_in * 1000),
  );
  if (token.refresh_token) {
    localStorage.setItem(spotifyStorage.refreshToken, token.refresh_token);
  }
  return token.access_token;
}

async function spotifyFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${SPOTIFY_API_URL}${path}`, {
    headers: { Authorization: `Bearer ${await getSpotifyAccessToken()}` },
  });

  if (!response.ok) {
    throw new Error(`Spotify isteği başarısız: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getSpotifyPlaylists(): Promise<SpotifyPlaylist[]> {
  const data = await spotifyFetch<{ items?: SpotifyPlaylist[] }>(
    "/me/playlists?limit=10",
  );
  return data.items ?? [];
}

export async function getSpotifyPlaylistTracks(
  playlistId: string,
): Promise<SpotifyTrack[]> {
  const data = await spotifyFetch<{ items?: SpotifyPlaylistItem[] }>(
    `/playlists/${playlistId}/items?limit=50`,
  );

  return (data.items ?? [])
    .map((entry) => entry.item ?? entry.track)
    .filter((track): track is SpotifyTrack => Boolean(track?.id));
}

export async function searchSpotifyTracks(
  query: string,
): Promise<SpotifyTrack[]> {
  const trimmedQuery = query.trim();
  if (!trimmedQuery) return [];

  const data = await spotifyFetch<{ tracks?: { items?: SpotifyTrack[] } }>(
    `/search?type=track&limit=12&q=${encodeURIComponent(trimmedQuery)}`,
  );
  return data.tracks?.items ?? [];
}

export async function startSpotifyLogin(): Promise<void> {
  const clientId = process.env.NEXT_PUBLIC_SPOTIFY_CLIENT_ID;
  const redirectUri = `${window.location.origin}/callback`;

  if (!clientId) {
    throw new Error("Spotify ayarları bulunamadı.");
  }

  const characters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  const codeVerifier = Array.from(
    crypto.getRandomValues(new Uint8Array(64)),
    (value) => characters[value % characters.length],
  ).join("");

  const hashedVerifier = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(codeVerifier),
  );
  const codeChallenge = btoa(
    String.fromCharCode(...new Uint8Array(hashedVerifier)),
  )
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");

  localStorage.setItem(spotifyStorage.codeVerifier, codeVerifier);

  const params = new URLSearchParams({
    client_id: clientId,
    response_type: "code",
    redirect_uri: redirectUri,
    code_challenge_method: "S256",
    code_challenge: codeChallenge,
    scope:
      "streaming user-read-private user-read-email user-read-playback-state user-modify-playback-state playlist-read-private playlist-read-collaborative user-top-read",
  });

  window.location.href = `${SPOTIFY_ACCOUNTS_URL}/authorize?${params}`;
}

export function clearSpotifySession(): void {
  Object.values(spotifyStorage).forEach((key) => localStorage.removeItem(key));
}
