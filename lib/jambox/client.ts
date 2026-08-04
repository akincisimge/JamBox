import type {
  BlofDeclaredRank,
  BlofGame,
  ChatMessage,
  JamBoxPlayback,
  JamBoxRoom,
  JamBoxUser,
  KelimeKapismasiGame,
  PapazKactiGame,
  PistiGame,
  SpotifyProfile,
  TekKartColor,
  TekKartGame,
} from "../../types/jambox";

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
  onPistiUpdated?: () => void;
  onPapazKactiUpdated?: () => void;
  onTekKartUpdated?: () => void;
  onKelimeKapismasiUpdated?: () => void;
  onBlofUpdated?: () => void;
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
  let socket: WebSocket | null = null;
  let reconnectTimer: number | undefined;
  let reconnectDelay = 1000;
  let stopped = false;
  const handleMessage = (event: MessageEvent<string>) => {
    let message: { type?: string; message?: ChatMessage };
    try { message = JSON.parse(event.data) as { type?: string; message?: ChatMessage }; } catch { return; }
    if (message.type === "room_updated") handlers.onRoomUpdated();
    if (message.type === "playback_updated") handlers.onPlaybackUpdated();
    if (message.type === "chess_updated") handlers.onChessUpdated();
    if (message.type === "pisti_updated") handlers.onPistiUpdated?.();
    if (message.type === "papaz_kacti_updated") handlers.onPapazKactiUpdated?.();
    if (message.type === "tek_kart_updated") handlers.onTekKartUpdated?.();
    if (message.type === "kelime_kapismasi_updated") handlers.onKelimeKapismasiUpdated?.();
    if (message.type === "blof_updated") handlers.onBlofUpdated?.();
    if (message.type === "message_created" && message.message) handlers.onMessageCreated(message.message);
    if (message.type === "message_updated" && message.message) handlers.onMessageUpdated(message.message);
    if (message.type === "room_closed") handlers.onRoomClosed();
  };
  const handleOpen = () => { reconnectDelay = 1000; };
  const handleClose = () => {
    socket = null;
    if (stopped || reconnectTimer !== undefined) return;
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = undefined;
      connect();
    }, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 15000);
  };
  const connect = () => {
    if (stopped || socket) return;
    socket = new WebSocket(socketUrl);
    socket.addEventListener("open", handleOpen);
    socket.addEventListener("message", handleMessage);
    socket.addEventListener("close", handleClose);
  };
  connect();
  return () => {
    stopped = true;
    window.clearTimeout(reconnectTimer);
    reconnectTimer = undefined;
    socket?.removeEventListener("open", handleOpen);
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
export async function createJamBoxPistiGame(userId: string, code: string): Promise<PistiGame> {
  return apiFetch<PistiGame>(`/rooms/${encodeURIComponent(code)}/pisti`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function getJamBoxPistiGame(userId: string, code: string): Promise<PistiGame> {
  return apiFetch<PistiGame>(`/rooms/${encodeURIComponent(code)}/pisti`, { headers: { "X-User-Id": userId } });
}
export async function joinJamBoxPistiGame(userId: string, code: string): Promise<PistiGame> {
  return apiFetch<PistiGame>(`/rooms/${encodeURIComponent(code)}/pisti/join`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function playJamBoxPistiCard(userId: string, code: string, cardId: string): Promise<PistiGame> {
  return apiFetch<PistiGame>(`/rooms/${encodeURIComponent(code)}/pisti/cards`, { method: "POST", headers: { "X-User-Id": userId }, body: JSON.stringify({ card_id: cardId }) });
}
export async function restartJamBoxPistiGame(userId: string, code: string): Promise<PistiGame> {
  return apiFetch<PistiGame>(`/rooms/${encodeURIComponent(code)}/pisti/restart`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function createJamBoxPapazKactiGame(userId: string, code: string): Promise<PapazKactiGame> {
  return apiFetch<PapazKactiGame>(`/rooms/${encodeURIComponent(code)}/papaz-kacti`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function getJamBoxPapazKactiGame(userId: string, code: string): Promise<PapazKactiGame> {
  return apiFetch<PapazKactiGame>(`/rooms/${encodeURIComponent(code)}/papaz-kacti`, { headers: { "X-User-Id": userId } });
}
export async function joinJamBoxPapazKactiGame(userId: string, code: string): Promise<PapazKactiGame> {
  return apiFetch<PapazKactiGame>(`/rooms/${encodeURIComponent(code)}/papaz-kacti/join`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function startJamBoxPapazKactiGame(userId: string, code: string): Promise<PapazKactiGame> {
  return apiFetch<PapazKactiGame>(`/rooms/${encodeURIComponent(code)}/papaz-kacti/start`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function drawJamBoxPapazKactiCard(userId: string, code: string, cardIndex: number): Promise<PapazKactiGame> {
  return apiFetch<PapazKactiGame>(`/rooms/${encodeURIComponent(code)}/papaz-kacti/draw`, { method: "POST", headers: { "X-User-Id": userId }, body: JSON.stringify({ card_index: cardIndex }) });
}
export async function restartJamBoxPapazKactiGame(userId: string, code: string): Promise<PapazKactiGame> {
  return apiFetch<PapazKactiGame>(`/rooms/${encodeURIComponent(code)}/papaz-kacti/restart`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function createJamBoxTekKartGame(userId: string, code: string): Promise<TekKartGame> {
  return apiFetch<TekKartGame>(`/rooms/${encodeURIComponent(code)}/tek-kart`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function getJamBoxTekKartGame(userId: string, code: string): Promise<TekKartGame> {
  return apiFetch<TekKartGame>(`/rooms/${encodeURIComponent(code)}/tek-kart`, { headers: { "X-User-Id": userId } });
}
export async function joinJamBoxTekKartGame(userId: string, code: string): Promise<TekKartGame> {
  return apiFetch<TekKartGame>(`/rooms/${encodeURIComponent(code)}/tek-kart/join`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function startJamBoxTekKartGame(userId: string, code: string): Promise<TekKartGame> {
  return apiFetch<TekKartGame>(`/rooms/${encodeURIComponent(code)}/tek-kart/start`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function playJamBoxTekKartCard(userId: string, code: string, cardId: string, chosenColor?: TekKartColor): Promise<TekKartGame> {
  return apiFetch<TekKartGame>(`/rooms/${encodeURIComponent(code)}/tek-kart/play`, { method: "POST", headers: { "X-User-Id": userId }, body: JSON.stringify({ card_id: cardId, chosen_color: chosenColor ?? null }) });
}
export async function drawJamBoxTekKartCard(userId: string, code: string): Promise<TekKartGame> {
  return apiFetch<TekKartGame>(`/rooms/${encodeURIComponent(code)}/tek-kart/draw`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function callJamBoxTekKart(userId: string, code: string): Promise<TekKartGame> {
  return apiFetch<TekKartGame>(`/rooms/${encodeURIComponent(code)}/tek-kart/call`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function restartJamBoxTekKartGame(userId: string, code: string): Promise<TekKartGame> {
  return apiFetch<TekKartGame>(`/rooms/${encodeURIComponent(code)}/tek-kart/restart`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function createJamBoxBlofGame(userId: string, code: string): Promise<BlofGame> {
  return apiFetch<BlofGame>(`/rooms/${encodeURIComponent(code)}/blof`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function getJamBoxBlofGame(userId: string, code: string): Promise<BlofGame> {
  return apiFetch<BlofGame>(`/rooms/${encodeURIComponent(code)}/blof`, { headers: { "X-User-Id": userId } });
}
export async function joinJamBoxBlofGame(userId: string, code: string): Promise<BlofGame> {
  return apiFetch<BlofGame>(`/rooms/${encodeURIComponent(code)}/blof/join`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function startJamBoxBlofGame(userId: string, code: string): Promise<BlofGame> {
  return apiFetch<BlofGame>(`/rooms/${encodeURIComponent(code)}/blof/start`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function playJamBoxBlofCards(userId: string, code: string, cardIds: string[], declaredRank: BlofDeclaredRank): Promise<BlofGame> {
  return apiFetch<BlofGame>(`/rooms/${encodeURIComponent(code)}/blof/play`, { method: "POST", headers: { "X-User-Id": userId }, body: JSON.stringify({ card_ids: cardIds, declared_rank: declaredRank }) });
}
export async function callJamBoxBlof(userId: string, code: string): Promise<BlofGame> {
  return apiFetch<BlofGame>(`/rooms/${encodeURIComponent(code)}/blof/call`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function acceptJamBoxBlofPlay(userId: string, code: string): Promise<BlofGame> {
  return apiFetch<BlofGame>(`/rooms/${encodeURIComponent(code)}/blof/accept`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function restartJamBoxBlofGame(userId: string, code: string): Promise<BlofGame> {
  return apiFetch<BlofGame>(`/rooms/${encodeURIComponent(code)}/blof/restart`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function createJamBoxKelimeKapismasiGame(userId: string, code: string): Promise<KelimeKapismasiGame> {
  return apiFetch<KelimeKapismasiGame>(`/rooms/${encodeURIComponent(code)}/kelime-kapismasi`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function getJamBoxKelimeKapismasiGame(userId: string, code: string): Promise<KelimeKapismasiGame> {
  return apiFetch<KelimeKapismasiGame>(`/rooms/${encodeURIComponent(code)}/kelime-kapismasi`, { headers: { "X-User-Id": userId } });
}
export async function joinJamBoxKelimeKapismasiGame(userId: string, code: string): Promise<KelimeKapismasiGame> {
  return apiFetch<KelimeKapismasiGame>(`/rooms/${encodeURIComponent(code)}/kelime-kapismasi/join`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function startJamBoxKelimeKapismasiGame(userId: string, code: string): Promise<KelimeKapismasiGame> {
  return apiFetch<KelimeKapismasiGame>(`/rooms/${encodeURIComponent(code)}/kelime-kapismasi/start`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function submitJamBoxKelimeKapismasiWord(userId: string, code: string, word: string): Promise<KelimeKapismasiGame> {
  return apiFetch<KelimeKapismasiGame>(`/rooms/${encodeURIComponent(code)}/kelime-kapismasi/words`, { method: "POST", headers: { "X-User-Id": userId }, body: JSON.stringify({ word: word.trim() }) });
}
export async function restartJamBoxKelimeKapismasiGame(userId: string, code: string): Promise<KelimeKapismasiGame> {
  return apiFetch<KelimeKapismasiGame>(`/rooms/${encodeURIComponent(code)}/kelime-kapismasi/restart`, { method: "POST", headers: { "X-User-Id": userId } });
}

export async function leaveJamBoxRoom(userId: string, code: string): Promise<void> {
  return apiFetch<void>(`/rooms/${encodeURIComponent(code)}/leave`, { method: "POST", headers: { "X-User-Id": userId } });
}
export async function closeJamBoxRoom(userId: string, code: string): Promise<void> {
  return apiFetch<void>(`/rooms/${encodeURIComponent(code)}`, { method: "DELETE", headers: { "X-User-Id": userId } });
}
