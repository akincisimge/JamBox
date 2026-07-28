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

function getAccessToken(): string {
  const accessToken = localStorage.getItem(spotifyStorage.accessToken);
  if (!accessToken) {
    throw new Error("Spotify oturumu bulunamadı. Tekrar giriş yapmalısın.");
  }
  return accessToken;
}

async function spotifyFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${SPOTIFY_API_URL}${path}`, {
    headers: { Authorization: `Bearer ${getAccessToken()}` },
  });

  if (!response.ok) {
    throw new Error(`Spotify isteği başarısız: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getSpotifyPlaylists(): Promise<SpotifyPlaylist[]> {
  const data = await spotifyFetch<{ items?: SpotifyPlaylist[] }>(
    "/me/playlists?limit=12",
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

export async function startSpotifyLogin(): Promise<void> {
  const clientId = process.env.NEXT_PUBLIC_SPOTIFY_CLIENT_ID;
  const redirectUri = process.env.NEXT_PUBLIC_SPOTIFY_REDIRECT_URI;

  if (!clientId || !redirectUri) {
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
      "user-read-private user-read-email playlist-read-private playlist-read-collaborative user-top-read",
  });

  window.location.href = `${SPOTIFY_ACCOUNTS_URL}/authorize?${params}`;
}

export function clearSpotifySession(): void {
  Object.values(spotifyStorage).forEach((key) => localStorage.removeItem(key));
}
