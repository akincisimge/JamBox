from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text()
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one anchor in {path}, found {count}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1))


def replace_many(path: str, old: str, new: str, expected: int) -> None:
    target = ROOT / path
    text = target.read_text()
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"Expected {expected} anchors in {path}, found {count}: {old[:80]!r}")
    target.write_text(text.replace(old, new))


# TypeScript domain types.
replace_once(
    "types/jambox.ts",
    '  message_type: "text" | "chess_invite" | "pisti_invite" | "papaz_kacti_invite" | "tek_kart_invite" | "blof_invite";\n',
    '  message_type: "text" | "chess_invite" | "pisti_invite" | "papaz_kacti_invite" | "tek_kart_invite" | "blof_invite" | "kelime_kapismasi_invite";\n',
)

replace_once(
    "types/jambox.ts",
    "export type JamBoxRoom = {\n",
    '''export type KelimeKapismasiDifficulty = "easy" | "medium" | "hard";

export type KelimeKapismasiStatus =
  | "waiting"
  | "countdown"
  | "playing"
  | "round_result"
  | "finished";

export type KelimeKapismasiPlayer = {
  user_id: string;
  player_order: number;
  current_word_count: number;
  stage_points: number;
  total_words: number;
  total_letters: number;
  is_creator: boolean;
  user: JamBoxUser;
};

export type KelimeKapismasiRoundPlayerResult = {
  user_id: string;
  words: string[];
  word_count: number;
  total_letters: number;
  longest_word: string | null;
  stage_points: number;
};

export type KelimeKapismasiRoundResult = {
  stage_number: number;
  difficulty: KelimeKapismasiDifficulty;
  winner_user_id: string | null;
  players: KelimeKapismasiRoundPlayerResult[];
};

export type KelimeKapismasiGame = {
  id: string;
  creator_id: string;
  status: KelimeKapismasiStatus;
  version: number;
  stage_number: number;
  stage_count: number;
  difficulty: KelimeKapismasiDifficulty | null;
  letters: string[];
  min_length: number;
  duration_seconds: number;
  phase_started_at: string | null;
  phase_ends_at: string | null;
  remaining_seconds: number;
  own_words: string[];
  own_word_count: number;
  players: KelimeKapismasiPlayer[];
  latest_result: KelimeKapismasiRoundResult | null;
  winner_user_id: string | null;
};

export type JamBoxRoom = {
''',
)

# API client and WebSocket event.
replace_once(
    "lib/jambox/client.ts",
    'import type { BlofDeclaredRank, BlofGame, ChatMessage, JamBoxPlayback, JamBoxRoom, JamBoxUser, PistiGame, PapazKactiGame, SpotifyProfile, TekKartColor, TekKartGame } from "../../types/jambox";\n',
    '''import type {
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
''',
)

replace_once(
    "lib/jambox/client.ts",
    "  onTekKartUpdated?: () => void;\n",
    "  onTekKartUpdated?: () => void;\n  onKelimeKapismasiUpdated?: () => void;\n",
)

replace_once(
    "lib/jambox/client.ts",
    '    if (message.type === "tek_kart_updated") handlers.onTekKartUpdated?.();\n',
    '    if (message.type === "tek_kart_updated") handlers.onTekKartUpdated?.();\n    if (message.type === "kelime_kapismasi_updated") handlers.onKelimeKapismasiUpdated?.();\n',
)

replace_once(
    "lib/jambox/client.ts",
    "export async function leaveJamBoxRoom(userId: string, code: string): Promise<void> {\n",
    '''export async function createJamBoxKelimeKapismasiGame(userId: string, code: string): Promise<KelimeKapismasiGame> {
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
''',
)

# JamBox application integration.
replace_once(
    "app/JamBoxApp.tsx",
    'import { TekKartActivity } from "../components/room/TekKartActivity";\n',
    'import { TekKartActivity } from "../components/room/TekKartActivity";\nimport { KelimeKapismasiActivity } from "../components/room/KelimeKapismasiActivity";\n',
)

replace_once(
    "app/JamBoxApp.tsx",
    '''  restartJamBoxTekKartGame,
  startJamBoxTekKartGame,
} from "../lib/jambox/client";
''',
    '''  restartJamBoxTekKartGame,
  startJamBoxTekKartGame,
  createJamBoxKelimeKapismasiGame,
  getJamBoxKelimeKapismasiGame,
  joinJamBoxKelimeKapismasiGame,
  restartJamBoxKelimeKapismasiGame,
  startJamBoxKelimeKapismasiGame,
  submitJamBoxKelimeKapismasiWord,
} from "../lib/jambox/client";
''',
)

replace_once(
    "app/JamBoxApp.tsx",
    "  TekKartGame,\n  SpotifyPlaylist,\n",
    "  TekKartGame,\n  KelimeKapismasiGame,\n  SpotifyPlaylist,\n",
)

replace_once(
    "app/JamBoxApp.tsx",
    '''  const [blofError, setBlofError] = useState("");
  const [activeGameTab, setActiveGameTab] = useState<
''',
    '''  const [blofError, setBlofError] = useState("");
  const [kelimeKapismasiGame, setKelimeKapismasiGame] = useState<KelimeKapismasiGame | null>(null);
  const [kelimeKapismasiBusy, setKelimeKapismasiBusy] = useState(false);
  const [kelimeKapismasiError, setKelimeKapismasiError] = useState("");
  const [activeGameTab, setActiveGameTab] = useState<
''',
)

replace_once(
    "app/JamBoxApp.tsx",
    '    "chess" | "pisti" | "papaz_kacti" | "tek_kart" | "blof"\n',
    '    "chess" | "pisti" | "papaz_kacti" | "tek_kart" | "blof" | "kelime_kapismasi"\n',
)

replace_once(
    "app/JamBoxApp.tsx",
    '''    void fetchBlofState();

    return connectToJamBoxRoom(jamBoxUserId, activeRoomCode, {
''',
    '''    void fetchBlofState();

    const fetchKelimeKapismasiState = async () => {
      try {
        setKelimeKapismasiGame(
          await getJamBoxKelimeKapismasiGame(jamBoxUserId, activeRoomCode),
        );
      } catch {
        setKelimeKapismasiGame(null);
      }
    };
    void fetchKelimeKapismasiState();

    return connectToJamBoxRoom(jamBoxUserId, activeRoomCode, {
''',
)

replace_once(
    "app/JamBoxApp.tsx",
    '''      onBlofUpdated: async () => {
        try {
          setBlofGame(await getJamBoxBlofGame(jamBoxUserId, activeRoomCode));
        } catch (error) {
          console.error("Blöf masası güncellenemedi:", error);
          setBlofGame(null);
        }
      },
      onMessageCreated: (newMessage) => {
''',
    '''      onBlofUpdated: async () => {
        try {
          setBlofGame(await getJamBoxBlofGame(jamBoxUserId, activeRoomCode));
        } catch (error) {
          console.error("Blöf masası güncellenemedi:", error);
          setBlofGame(null);
        }
      },
      onKelimeKapismasiUpdated: async () => {
        try {
          setKelimeKapismasiGame(
            await getJamBoxKelimeKapismasiGame(jamBoxUserId, activeRoomCode),
          );
        } catch (error) {
          console.error("Kelime Kapışması güncellenemedi:", error);
          setKelimeKapismasiGame(null);
        }
      },
      onMessageCreated: (newMessage) => {
''',
)

replace_once(
    "app/JamBoxApp.tsx",
    '''        setBlofGame(null);
        setView("home");
''',
    '''        setBlofGame(null);
        setKelimeKapismasiGame(null);
        setKelimeKapismasiError("");
        setView("home");
''',
)

replace_many(
    "app/JamBoxApp.tsx",
    '''    setTekKartGame(null);
    setTekKartError("");
    setBlofGame(null);
    setBlofError("");
    setView("home");
''',
    '''    setTekKartGame(null);
    setTekKartError("");
    setBlofGame(null);
    setBlofError("");
    setKelimeKapismasiGame(null);
    setKelimeKapismasiError("");
    setView("home");
''',
    1,
)

replace_once(
    "app/JamBoxApp.tsx",
    '''      setTekKartGame(null);
      setTekKartError("");
      setBlofGame(null);
      setBlofError("");
      setView("home");
''',
    '''      setTekKartGame(null);
      setTekKartError("");
      setBlofGame(null);
      setBlofError("");
      setKelimeKapismasiGame(null);
      setKelimeKapismasiError("");
      setView("home");
''',
)

replace_once(
    "app/JamBoxApp.tsx",
    "  async function playTrackTogether(track: SpotifyTrack) {\n",
    '''  async function refreshKelimeKapismasiGame() {
    if (!activeRoom || !jamBoxUserId) return;
    try {
      setKelimeKapismasiGame(
        await getJamBoxKelimeKapismasiGame(jamBoxUserId, activeRoom.code),
      );
    } catch (error) {
      console.error("Kelime Kapışması yenilenemedi:", error);
    }
  }

  async function openKelimeKapismasiTable() {
    if (!activeRoom || !jamBoxUserId) return;
    setKelimeKapismasiBusy(true);
    setKelimeKapismasiError("");
    try {
      setKelimeKapismasiGame(
        await createJamBoxKelimeKapismasiGame(jamBoxUserId, activeRoom.code),
      );
      setActiveGameTab("kelime_kapismasi");
      setToast("Kelime Kapışması daveti sohbete gönderildi.");
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Kelime Kapışması açılamadı.";
      setKelimeKapismasiError(msg);
      setToast(msg);
    } finally {
      setKelimeKapismasiBusy(false);
    }
  }

  async function acceptKelimeKapismasiInvite() {
    if (!activeRoom || !jamBoxUserId) return;
    setKelimeKapismasiBusy(true);
    setKelimeKapismasiError("");
    try {
      setKelimeKapismasiGame(
        await joinJamBoxKelimeKapismasiGame(jamBoxUserId, activeRoom.code),
      );
      setActiveGameTab("kelime_kapismasi");
      setToast("Kelime Kapışması düellosuna katıldın.");
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Düelloya katılamadın.";
      setKelimeKapismasiError(msg);
      setToast(msg);
    } finally {
      setKelimeKapismasiBusy(false);
    }
  }

  async function startKelimeKapismasiGame() {
    if (!activeRoom || !jamBoxUserId) return;
    setKelimeKapismasiBusy(true);
    setKelimeKapismasiError("");
    try {
      setKelimeKapismasiGame(
        await startJamBoxKelimeKapismasiGame(jamBoxUserId, activeRoom.code),
      );
      setToast("Kelime Kapışması başladı.");
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Kelime Kapışması başlatılamadı.";
      setKelimeKapismasiError(msg);
      setToast(msg);
    } finally {
      setKelimeKapismasiBusy(false);
    }
  }

  async function submitKelimeKapismasiWord(word: string): Promise<boolean> {
    if (!activeRoom || !jamBoxUserId) return false;
    setKelimeKapismasiBusy(true);
    setKelimeKapismasiError("");
    try {
      setKelimeKapismasiGame(
        await submitJamBoxKelimeKapismasiWord(
          jamBoxUserId,
          activeRoom.code,
          word,
        ),
      );
      return true;
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Kelime eklenemedi.";
      setKelimeKapismasiError(msg);
      return false;
    } finally {
      setKelimeKapismasiBusy(false);
    }
  }

  async function restartKelimeKapismasiGame() {
    if (!activeRoom || !jamBoxUserId) return;
    setKelimeKapismasiBusy(true);
    setKelimeKapismasiError("");
    try {
      setKelimeKapismasiGame(
        await restartJamBoxKelimeKapismasiGame(jamBoxUserId, activeRoom.code),
      );
      setToast("Kelime Kapışması rövanşı hazır.");
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Rövanş başlatılamadı.";
      setKelimeKapismasiError(msg);
      setToast(msg);
    } finally {
      setKelimeKapismasiBusy(false);
    }
  }

  async function playTrackTogether(track: SpotifyTrack) {
''',
)

replace_once(
    "app/JamBoxApp.tsx",
    '''                    <div className="message-reactions">
''',
    '''                    {item.message_type === "kelime_kapismasi_invite" && (
                      <div className="chess-invite-card">
                        <span>🔤</span>
                        <div>
                          <strong>Kelime Kapışması daveti</strong>
                          <small>İki kişilik, altı etaplı eş zamanlı kelime düellosu.</small>
                        </div>
                        {kelimeKapismasiGame?.status === "waiting" &&
                          !kelimeKapismasiGame.players.some(
                            (player) => player.user_id === jamBoxUserId,
                          ) && (
                            <button
                              type="button"
                              onClick={acceptKelimeKapismasiInvite}
                              disabled={kelimeKapismasiBusy}
                            >
                              Katıl
                            </button>
                          )}
                        {kelimeKapismasiGame &&
                          kelimeKapismasiGame.status !== "waiting" &&
                          kelimeKapismasiGame.status !== "finished" && <b>Oyun başladı</b>}
                      </div>
                    )}
                    <div className="message-reactions">
''',
)

replace_once(
    "app/JamBoxApp.tsx",
    '''              <button
                type="button"
                className={`game-tab${activeGameTab === "blof" ? " active" : ""}`}
                onClick={() => setActiveGameTab("blof")}
              >
                🎭 Blöf
              </button>
            </nav>
''',
    '''              <button
                type="button"
                className={`game-tab${activeGameTab === "blof" ? " active" : ""}`}
                onClick={() => setActiveGameTab("blof")}
              >
                🎭 Blöf
              </button>
              <button
                type="button"
                className={`game-tab${activeGameTab === "kelime_kapismasi" ? " active" : ""}`}
                onClick={() => setActiveGameTab("kelime_kapismasi")}
              >
                🔤 Kelime Kapışması
              </button>
            </nav>
''',
)

replace_once(
    "app/JamBoxApp.tsx",
    '''            )}
          </section>

          <section className="queue-panel panel music-library-panel">
''',
    '''            )}

            {activeGameTab === "kelime_kapismasi" && (
              <KelimeKapismasiActivity
                game={kelimeKapismasiGame}
                currentUserId={jamBoxUserId}
                busy={kelimeKapismasiBusy}
                error={kelimeKapismasiError}
                onCreate={openKelimeKapismasiTable}
                onJoin={acceptKelimeKapismasiInvite}
                onStart={startKelimeKapismasiGame}
                onSubmitWord={submitKelimeKapismasiWord}
                onRestart={restartKelimeKapismasiGame}
                onRefresh={refreshKelimeKapismasiGame}
              />
            )}
          </section>

          <section className="queue-panel panel music-library-panel">
''',
)

print("✅ Kelime Kapışması frontend entegrasyonu uygulandı.")
