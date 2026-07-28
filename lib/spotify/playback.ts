import type { JamBoxPlayback } from "../../types/jambox";
import { getSpotifyAccessToken } from "./client";

const SPOTIFY_API_URL = "https://api.spotify.com/v1";
let sdkPromise: Promise<void> | null = null;

function loadSpotifySdk(): Promise<void> {
  if (window.Spotify) return Promise.resolve();
  if (sdkPromise) return sdkPromise;

  sdkPromise = new Promise((resolve, reject) => {
    window.onSpotifyWebPlaybackSDKReady = resolve;
    const script = document.createElement("script");
    script.src = "https://sdk.scdn.co/spotify-player.js";
    script.async = true;
    script.onerror = () => reject(new Error("Spotify oynatıcısı yüklenemedi."));
    document.body.appendChild(script);
  });
  return sdkPromise;
}

async function playerRequest(
  path: string,
  init: RequestInit,
): Promise<void> {
  const response = await fetch(`${SPOTIFY_API_URL}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${await getSpotifyAccessToken()}`,
      "Content-Type": "application/json",
      ...init.headers,
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Spotify oynatma isteği başarısız: ${response.status}${
        detail ? ` (${detail})` : ""
      }`,
    );
  }
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

export async function createSpotifyRoomPlayer(
  onError: (message: string) => void,
): Promise<{ player: SpotifyPlayer; deviceId: string }> {
  await loadSpotifySdk();
  if (!window.Spotify) throw new Error("Spotify oynatıcısı başlatılamadı.");

  const player = new window.Spotify.Player({
    name: "JamBox Room",
    volume: 0.7,
    getOAuthToken: (callback) => {
      void getSpotifyAccessToken().then(callback).catch((error) => {
        onError(error instanceof Error ? error.message : "Spotify oturumu geçersiz.");
      });
    },
  });

  for (const event of [
    "initialization_error",
    "authentication_error",
    "account_error",
    "playback_error",
  ] as const) {
    player.addListener(event, ({ message }) => onError(message));
  }

  const deviceId = await new Promise<string>((resolve, reject) => {
    player.addListener("ready", ({ device_id }) => resolve(device_id));
    void player.connect().then((connected) => {
      if (!connected) reject(new Error("Spotify oynatıcısına bağlanılamadı."));
    });
  });

  return { player, deviceId };
}

export async function activateSpotifyRoomPlayer(
  player: SpotifyPlayer,
  deviceId: string,
): Promise<void> {
  await player.activateElement();

  let lastError: unknown;
  for (const delay of [0, 500, 1000, 1500]) {
    if (delay) await wait(delay);
    try {
      await playerRequest("/me/player", {
        method: "PUT",
        body: JSON.stringify({ device_ids: [deviceId], play: false }),
      });
      return;
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}

export function currentPlaybackPosition(playback: JamBoxPlayback): number {
  const elapsed = playback.is_playing
    ? Math.max(0, Date.now() - Date.parse(playback.changed_at))
    : 0;
  return Math.min(playback.position_ms + elapsed, playback.duration_ms);
}

export async function applyRoomPlayback(
  playback: JamBoxPlayback,
  deviceId: string,
): Promise<void> {
  const positionMs = Math.floor(currentPlaybackPosition(playback));
  await playerRequest(`/me/player/play?device_id=${encodeURIComponent(deviceId)}`, {
    method: "PUT",
    body: JSON.stringify({
      uris: [playback.spotify_uri],
      position_ms: positionMs,
    }),
  });
  if (!playback.is_playing) {
    await playerRequest(`/me/player/pause?device_id=${encodeURIComponent(deviceId)}`, {
      method: "PUT",
    });
  }
}
