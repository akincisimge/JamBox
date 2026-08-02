from pathlib import Path

path = Path("app/JamBoxApp.tsx")
content = path.read_text()


def replace_once(old: str, new: str) -> None:
    global content
    if old not in content:
        raise RuntimeError(f"Anchor not found: {old[:100]!r}")
    content = content.replace(old, new, 1)


replace_once(
    'import { PapazKactiActivity } from "../components/room/PapazKactiActivity";\n',
    'import { PapazKactiActivity } from "../components/room/PapazKactiActivity";\nimport { BlofActivity } from "../components/room/BlofActivity";\n',
)
replace_once(
    "  restartJamBoxPapazKactiGame,\n",
    "  restartJamBoxPapazKactiGame,\n  acceptJamBoxBlofPlay,\n  callJamBoxBlof,\n  createJamBoxBlofGame,\n  getJamBoxBlofGame,\n  joinJamBoxBlofGame,\n  playJamBoxBlofCards,\n  restartJamBoxBlofGame,\n  startJamBoxBlofGame,\n",
)
replace_once(
    "  PapazKactiGame,\n",
    "  PapazKactiGame,\n  BlofDeclaredRank,\n  BlofGame,\n",
)
replace_once(
    '  const [activeGameTab, setActiveGameTab] = useState<"chess" | "pisti" | "papaz_kacti">("chess");\n',
    '  const [blofGame, setBlofGame] = useState<BlofGame | null>(null);\n  const [blofBusy, setBlofBusy] = useState(false);\n  const [blofError, setBlofError] = useState("");\n  const [activeGameTab, setActiveGameTab] = useState<"chess" | "pisti" | "papaz_kacti" | "blof">("chess");\n',
)
replace_once(
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
    "        setPapazKactiGame(null);\n        setView(\"home\");",
    "        setPapazKactiGame(null);\n        setBlofGame(null);\n        setView(\"home\");",
)
reset_anchor = '    setPapazKactiGame(null);\n    setPapazKactiError("");\n    setView("home");'
if content.count(reset_anchor) < 2:
    raise RuntimeError("Expected logout and leave reset anchors")
content = content.replace(
    reset_anchor,
    '    setPapazKactiGame(null);\n    setPapazKactiError("");\n    setBlofGame(null);\n    setBlofError("");\n    setView("home");',
    2,
)

handlers = '''
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
    "\n  async function playTrackTogether(track: SpotifyTrack) {\n",
    handlers + "\n  async function playTrackTogether(track: SpotifyTrack) {\n",
)
invite = '''                    {item.message_type === "blof_invite" && (
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
    "                    <div className=\"message-reactions\">\n",
    invite + "                    <div className=\"message-reactions\">\n",
)
tab = '''              <button
                type="button"
                className={`game-tab${activeGameTab === "blof" ? " active" : ""}`}
                onClick={() => setActiveGameTab("blof")}
              >
                🎭 Blöf
              </button>
'''
replace_once(
    "            </nav>\n\n            {activeGameTab === \"chess\"",
    tab + "            </nav>\n\n            {activeGameTab === \"chess\"",
)
render = '''
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
    "          </section>\n\n          <section className=\"queue-panel panel music-library-panel\">",
    render + "          </section>\n\n          <section className=\"queue-panel panel music-library-panel\">",
)
path.write_text(content)
