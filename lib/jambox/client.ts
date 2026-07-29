import type { ChatMessage, JamBoxPlayback, JamBoxRoom, JamBoxUser, SpotifyProfile } from "../../types/jambox";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api").replace(/\/$/, "");

export class JamBoxApiError extends Error {
  constructor(message: string, public readonly status: number) { super(message); }
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { ...init, headers: { "Content-Type": "application/json", ...init.headers } });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new JamBoxApiError(body?.detail ?? `JamBox isteği başarısız: ${response.status}`, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function registerJamBoxUser(profile: SpotifyProfile): Promise<JamBoxUser> {
  return apiFetch<JamBoxUser>("/users", { method: "POST", body: JSON.stringify({ spotify_id: profile.id, display_name: profile.display_name || "Spotify user", avatar_url: profile.images?.[0]?.url ?? null }) });
}
export async function createJamBoxRoom(userId: string, name: string): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>("/rooms", { method: "POST", headers: { "X-User-Id": userId }, body: JSON.stringify({ name: name.trim() }) });
}
export async function joinJamBoxRoom(userId: string, code: string): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>(`/rooms/${encodeURIComponent(code.trim().toUpperCase())}/join`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function getJamBoxRoom(code: string): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>(`/rooms/${encodeURIComponent(code.trim().toUpperCase())}`);
}

type RoomSocketHandlers = {
  onRoomUpdated: () => void;
  onPlaybackUpdated: () => void;
  onChessUpdated: () => void;
  onMessageCreated: (message: ChatMessage) => void;
  onMessageUpdated: (message: ChatMessage) => void;
  onRoomClosed: () => void;
};

export function connectToJamBoxRoom(userId: string, code: string, handlers: RoomSocketHandlers): () => void {
  const isLocalHost = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const socketApiUrl = API_URL.startsWith("http") || !isLocalHost ? new URL(API_URL, window.location.origin) : new URL(`http://${window.location.hostname}:8000${API_URL}`);
  const socketUrl = socketApiUrl;
  socketUrl.protocol = socketUrl.protocol === "https:" ? "wss:" : "ws:";
  socketUrl.pathname = `${socketUrl.pathname}/rooms/${encodeURIComponent(code)}/ws`;
  socketUrl.search = new URLSearchParams({ user_id: userId }).toString();
  let socket: WebSocket | null = new WebSocket(socketUrl);
  let reconnectTimer: number | undefined;
  let stopped = false;
  const handleMessage = (event: MessageEvent<string>) => {
    let message: { type?: string; message?: ChatMessage };
    try { message = JSON.parse(event.data) as { type?: string; message?: ChatMessage }; } catch { return; }
    if (message.type === "room_updated") handlers.onRoomUpdated();
    if (message.type === "playback_updated") handlers.onPlaybackUpdated();
    if (message.type === "chess_updated") handlers.onChessUpdated();
    if (message.type === "message_created" && message.message) handlers.onMessageCreated(message.message);
    if (message.type === "message_updated" && message.message) handlers.onMessageUpdated(message.message);
    if (message.type === "room_closed") handlers.onRoomClosed();
  };
  const handleClose = () => { if (!stopped) reconnectTimer = window.setTimeout(connect, 1500); };
  const connect = () => {
    socket = new WebSocket(socketUrl);
    socket.addEventListener("message", handleMessage);
    socket.addEventListener("close", handleClose);
  };
  socket.addEventListener("message", handleMessage);
  socket.addEventListener("close", handleClose);
  return () => {
    stopped = true;
    window.clearTimeout(reconnectTimer);
    socket?.removeEventListener("message", handleMessage);
    socket?.removeEventListener("close", handleClose);
    socket?.close();
    socket = null;
  };
}

export type PlaybackUpdate = Omit<JamBoxPlayback, "version" | "changed_at">;
export async function updateJamBoxPlayback(userId: string, code: string, playback: PlaybackUpdate): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>(`/rooms/${encodeURIComponent(code)}/playback`, { method: "PUT", headers: { "X-User-Id": userId }, body: JSON.stringify(playback) });
}
export async function sendJamBoxMessage(userId: string, code: string, text: string): Promise<ChatMessage> {
  return apiFetch<ChatMessage>(`/rooms/${encodeURIComponent(code)}/messages`, { method: "POST", headers: { "X-User-Id": userId }, body: JSON.stringify({ text: text.trim() }) });
}
export async function toggleJamBoxMessageReaction(userId: string, code: string, messageId: string, emoji: string): Promise<ChatMessage> {
  return apiFetch<ChatMessage>(`/rooms/${encodeURIComponent(code)}/messages/${encodeURIComponent(messageId)}/reactions`, { method: "PUT", headers: { "X-User-Id": userId }, body: JSON.stringify({ emoji }) });
}
export async function createJamBoxChessGame(userId: string, code: string): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>(`/rooms/${encodeURIComponent(code)}/chess`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function addJamBoxChessTestOpponent(userId: string, code: string): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>(`/rooms/${encodeURIComponent(code)}/chess/test-opponent`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function joinJamBoxChessGame(userId: string, code: string): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>(`/rooms/${encodeURIComponent(code)}/chess/join`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function restartJamBoxChessGame(userId: string, code: string): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>(`/rooms/${encodeURIComponent(code)}/chess/restart`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function resignJamBoxChessGame(userId: string, code: string): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>(`/rooms/${encodeURIComponent(code)}/chess/resign`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function offerJamBoxChessDraw(userId: string, code: string): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>(`/rooms/${encodeURIComponent(code)}/chess/draw`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function makeJamBoxChessMove(userId: string, code: string, fromSquare: string, toSquare: string, promotion?: string): Promise<JamBoxRoom> {
  return apiFetch<JamBoxRoom>(`/rooms/${encodeURIComponent(code)}/chess/moves`, { method: "POST", headers: { "X-User-Id": userId }, body: JSON.stringify({ from_square: fromSquare, to_square: toSquare, promotion: promotion ?? null }) });
}
export async function leaveJamBoxRoom(userId: string, code: string): Promise<void> {
  return apiFetch<void>(`/rooms/${encodeURIComponent(code)}/leave`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function closeJamBoxRoom(userId: string, code: string): Promise<void> {
  return apiFetch<void>(`/rooms/${encodeURIComponent(code)}`, { method: "DELETE", headers: { "X-User-Id": userId } });
}
