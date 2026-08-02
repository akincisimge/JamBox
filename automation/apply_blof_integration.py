from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    content = file_path.read_text()
    if old not in content:
        raise RuntimeError(f"Anchor not found in {path}: {old[:80]!r}")
    file_path.write_text(content.replace(old, new, 1))


replace_once(
    "backend/app/api/router.py",
    "from app.api.routes.health import router as health_router\n",
    "from app.api.routes.blof import router as blof_router\nfrom app.api.routes.health import router as health_router\n",
)
replace_once(
    "backend/app/api/router.py",
    "api_router.include_router(papaz_kacti_router, tags=[\"papaz-kacti\"])\n",
    "api_router.include_router(papaz_kacti_router, tags=[\"papaz-kacti\"])\napi_router.include_router(blof_router, tags=[\"blof\"])\n",
)

replace_once(
    "backend/app/models/__init__.py",
    "from app.models.papaz_kacti import PapazKactiGame\n",
    "from app.models.blof import BlofGame\nfrom app.models.papaz_kacti import PapazKactiGame\n",
)
replace_once(
    "backend/app/models/__init__.py",
    "    \"ChessGame\",\n",
    "    \"BlofGame\",\n    \"ChessGame\",\n",
)

replace_once(
    "types/jambox.ts",
    '  message_type: "text" | "chess_invite" | "pisti_invite" | "papaz_kacti_invite";\n',
    '  message_type: "text" | "chess_invite" | "pisti_invite" | "papaz_kacti_invite" | "blof_invite";\n',
)
blof_types = '''export type BlofDeclaredRank = "A" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "J" | "Q" | "K";

export type BlofCard = {
  id: string;
  suit: "clubs" | "diamonds" | "hearts" | "spades";
  rank: BlofDeclaredRank;
};

export type BlofPlayer = {
  user_id: string;
  player_order: number;
  hand_count: number;
  is_current_turn: boolean;
  is_creator: boolean;
  user: JamBoxUser;
};

export type BlofChallengeResult = {
  truthful: boolean;
  challenger_user_id: string;
  challenged_user_id: string;
  pile_receiver_user_id: string;
  next_turn_user_id: string | null;
  revealed_cards: BlofCard[];
};

export type BlofGame = {
  id: string;
  creator_id: string;
  status: "waiting" | "active" | "finished";
  version: number;
  turn_user_id: string | null;
  pending_winner_user_id: string | null;
  winner_user_id: string | null;
  pile_count: number;
  last_play_count: number;
  last_declared_rank: BlofDeclaredRank | null;
  last_player_user_id: string | null;
  hand: BlofCard[];
  players: BlofPlayer[];
  last_result: BlofChallengeResult | null;
};

'''
replace_once("types/jambox.ts", "export type JamBoxRoom = {\n", blof_types + "export type JamBoxRoom = {\n")

replace_once(
    "lib/jambox/client.ts",
    "import type { ChatMessage, JamBoxPlayback, JamBoxRoom, JamBoxUser, PistiGame, PapazKactiGame, SpotifyProfile } from \"../../types/jambox\";",
    "import type { BlofDeclaredRank, BlofGame, ChatMessage, JamBoxPlayback, JamBoxRoom, JamBoxUser, PistiGame, PapazKactiGame, SpotifyProfile } from \"../../types/jambox\";",
)
replace_once(
    "lib/jambox/client.ts",
    "  onPapazKactiUpdated?: () => void;\n",
    "  onPapazKactiUpdated?: () => void;\n  onBlofUpdated?: () => void;\n",
)
replace_once(
    "lib/jambox/client.ts",
    '    if (message.type === "papaz_kacti_updated") handlers.onPapazKactiUpdated?.();\n',
    '    if (message.type === "papaz_kacti_updated") handlers.onPapazKactiUpdated?.();\n    if (message.type === "blof_updated") handlers.onBlofUpdated?.();\n',
)
blof_client = '''export async function createJamBoxBlofGame(userId: string, code: string): Promise<BlofGame> {
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
'''
replace_once(
    "lib/jambox/client.ts",
    "export async function leaveJamBoxRoom(userId: string, code: string): Promise<void> {\n",
    blof_client + "export async function leaveJamBoxRoom(userId: string, code: string): Promise<void> {\n",
)

replace_once(
    "app/JamBoxApp.tsx",
    'import { PapazKactiActivity } from "../components/room/PapazKactiActivity";\n',
    'import { PapazKactiActivity } from "../components/room/PapazKactiActivity";\nimport { BlofActivity } from "../components/room/BlofActivity";\n',
)
replace_once(
    "app/JamBoxApp.tsx",
    "  restartJamBoxPapazKactiGame,\n",
    "  restartJamBoxPapazKactiGame,\n  acceptJamBoxBlofPlay,\n  callJamBoxBlof,\n  createJamBoxBlofGame,\n  getJamBoxBlofGame,\n  joinJamBoxBlofGame,\n  playJamBoxBlofCards,\n  restartJamBoxBlofGame,\n  startJamBoxBlofGame,\n",
)
replace_once(
    "app/JamBoxApp.tsx",
    "  PapazKactiGame,\n",
    "  PapazKactiGame,\n  BlofDeclaredRank,\n  BlofGame,\n",
)
replace_once(
    "app/JamBoxApp.tsx",
    '  const [activeGameTab, setActiveGameTab] = useState<"chess" | "pisti" | "papaz_kacti">("chess");\n',
    '  const [blofGame, setBlofGame] = useState<BlofGame | null>(null);\n  const [blofBusy, setBlofBusy] = useState(false);\n  const [blofError, setBlofError] = useState("");\n  const [activeGameTab, setActiveGameTab] = useState<"chess" | "pisti" | "papaz_kacti" | "blof">("chess");\n',
)
replace_once(
    "app/JamBoxApp.tsx",
    "    void fetchPapazKactiState();\n\n    return connectToJamBoxRoom",
    '''    void fetchPapazKactiState();

    const fetchBlofState = async () => {
      try {
        setBlofGame(await getJamBoxBlofGame(jamBoxUserId, activeRoomCode));
      } catch {
        setBlofGame(null);
      }
    };
    void fetchBlofState();

    return connectToJamBoxRoom''',
)
replace_once(
    "app/JamBoxApp.tsx",
    "      onMessageCreated: (newMessage) => {\n",
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
)
replace_once(
    "app/JamBoxApp.tsx",
    "        setPapazKactiGame(null);\n        setView(\"home\");",
    "        setPapazKactiGame(null);\n        setBlofGame(null);\n        setView(\"home\");",
)
# Logout and leave each contain the same reset pair; update both occurrences.
app_path = Path("app/JamBoxApp.tsx")
app_content = app_path.read_text()
reset_anchor = '    setPapazKactiGame(null);\n    setPapazKactiError("");\n    setView("home");'
if app_content.count(reset_anchor) < 2:
    raise RuntimeError("Expected logout and leave reset anchors")
app_content = app_content.replace(
    reset_anchor,
    '    setPapazKactiGame(null);\n    setPapazKactiError("");\n    setBlofGame(null);\n    setBlofError("");\n    setView("home");',
    2,
)
app_path.write_text(app_content)

blof_handlers = '''
  async function openBlofTable() {
    if (!activeRoom || !jamBoxUserId) return;
    setBlofBusy(true);
    setBlofError("");
    try {
      setBlofGame(await createJamBoxBlofGame(jamBoxUserId, activeRoom.code));
      setActiveGameTab("blof");
      setToast("Blöf daveti sohbete gönderildi.");
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Blöf masası açılamadı.";
      setBlofError(msg);
      setToast(msg);
    } finally {
      setBlofBusy(false);
    }
  }

  async function acceptBlofInvite() {
    if (!activeRoom || !jamBoxUserId) return;
    setBlofBusy(true);
    setBlofError("");
    try {
      setBlofGame(await joinJamBoxBlofGame(jamBoxUserId, activeRoom.code));
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Blöf masasına katılamadın.";
      setBlofError(msg);
      setToast(msg);
    } finally {
      setBlofBusy(false);
    }
  }

  async function startBlofGame() {
    if (!activeRoom || !jamBoxUserId) return;
    setBlofBusy(true);
    setBlofError("");
    try {
      setBlofGame(await startJamBoxBlofGame(jamBoxUserId, activeRoom.code));
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Blöf başlatılamadı.";
      setBlofError(msg);
      setToast(msg);
    } finally {
      setBlofBusy(false);
    }
  }

  async function playBlofCards(cardIds: string[], declaredRank: BlofDeclaredRank) {
    if (!activeRoom || !jamBoxUserId) return;
    setBlofBusy(true);
    setBlofError("");
    try {
      setBlofGame(await playJamBoxBlofCards(jamBoxUserId, activeRoom.code, cardIds, declaredRank));
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Kartlar oynanamadı.";
      setBlofError(msg);
      setToast(msg);
    } finally {
      setBlofBusy(false);
    }
  }

  async function challengeBlof() {
    if (!activeRoom || !jamBoxUserId) return;
    setBlofBusy(true);
    try {
      setBlofGame(await callJamBoxBlof(jamBoxUserId, activeRoom.code));
    } catch (error) {
      setToast(error instanceof JamBoxApiError ? error.message : "Blöf itirazı yapılamadı.");
    } finally {
      setBlofBusy(false);
    }
  }

  async function acceptBlofLastPlay() {
    if (!activeRoom || !jamBoxUserId) return;
    setBlofBusy(true);
    try {
      setBlofGame(await acceptJamBoxBlofPlay(jamBoxUserId, activeRoom.code));
    } catch (error) {
      setToast(error instanceof JamBoxApiError ? error.message : "Son hamle kabul edilemedi.");
    } finally {
      setBlofBusy(false);
    }
  }

  async function restartBlof() {
    if (!activeRoom || !jamBoxUserId) return;
    setBlofBusy(true);
    try {
      setBlofGame(await restartJamBoxBlofGame(jamBoxUserId, activeRoom.code));
    } catch (error) {
      setToast(error instanceof JamBoxApiError ? error.message : "Yeni Blöf oyunu başlatılamadı.");
    } finally {
      setBlofBusy(false);
    }
  }
'''
replace_once(
    "app/JamBoxApp.tsx",
    "\n  async function playTrackTogether(track: SpotifyTrack) {\n",
    blof_handlers + "\n  async function playTrackTogether(track: SpotifyTrack) {\n",
)

blof_invite = '''                    {item.message_type === "blof_invite" && (
                      <div className="chess-invite-card">
                        <span>🎭</span>
                        <div>
                          <strong>Blöf daveti</strong>
                          <small>Müzik devam ederken masaya katıl.</small>
                        </div>
                        {blofGame?.status === "waiting" &&
                          !blofGame.players.some((player) => player.user_id === jamBoxUserId) && (
                            <button type="button" onClick={acceptBlofInvite} disabled={blofBusy}>
                              Katıl
                            </button>
                          )}
                        {blofGame?.status === "active" && <b>Oyun başladı</b>}
                      </div>
                    )}
'''
replace_once(
    "app/JamBoxApp.tsx",
    "                    <div className=\"message-reactions\">\n",
    blof_invite + "                    <div className=\"message-reactions\">\n",
)

blof_tab = '''              <button
                type="button"
                className={`game-tab${activeGameTab === "blof" ? " active" : ""}`}
                onClick={() => setActiveGameTab("blof")}
              >
                🎭 Blöf
              </button>
'''
replace_once(
    "app/JamBoxApp.tsx",
    "            </nav>\n\n            {activeGameTab === \"chess\"",
    blof_tab + "            </nav>\n\n            {activeGameTab === \"chess\"",
)

blof_render = '''
            {activeGameTab === "blof" && (
              <BlofActivity
                game={blofGame}
                currentUserId={jamBoxUserId}
                busy={blofBusy}
                error={blofError}
                onCreate={openBlofTable}
                onJoin={acceptBlofInvite}
                onStart={startBlofGame}
                onPlay={playBlofCards}
                onCall={challengeBlof}
                onAccept={acceptBlofLastPlay}
                onRestart={restartBlof}
              />
            )}
'''
replace_once(
    "app/JamBoxApp.tsx",
    "          </section>\n\n          <section className=\"queue-panel panel music-library-panel\">",
    blof_render + "          </section>\n\n          <section className=\"queue-panel panel music-library-panel\">",
)
