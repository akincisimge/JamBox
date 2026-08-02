from pathlib import Path

path = Path("app/JamBoxApp.tsx")
content = path.read_text()


def replace_once(old: str, new: str) -> None:
    global content
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one anchor, found {count}: {old[:120]!r}")
    content = content.replace(old, new, 1)


def replace_count(old: str, new: str, expected: int) -> None:
    global content
    count = content.count(old)
    if count != expected:
        raise RuntimeError(
            f"Expected {expected} reset anchors, found {count}: {old[:120]!r}"
        )
    content = content.replace(old, new)


replace_once(
    'import { PapazKactiActivity } from "../components/room/PapazKactiActivity";\n',
    'import { PapazKactiActivity } from "../components/room/PapazKactiActivity";\n'
    'import { TekKartActivity } from "../components/room/TekKartActivity";\n',
)

replace_once(
    '  restartJamBoxPapazKactiGame,\n',
    '  restartJamBoxPapazKactiGame,\n'
    '  callJamBoxTekKart,\n'
    '  createJamBoxTekKartGame,\n'
    '  drawJamBoxTekKartCard,\n'
    '  getJamBoxTekKartGame,\n'
    '  joinJamBoxTekKartGame,\n'
    '  playJamBoxTekKartCard,\n'
    '  restartJamBoxTekKartGame,\n'
    '  startJamBoxTekKartGame,\n',
)

replace_once(
    '  PapazKactiGame,\n',
    '  PapazKactiGame,\n  TekKartColor,\n  TekKartGame,\n',
)

replace_once(
    '  const [activeGameTab, setActiveGameTab] = useState<"chess" | "pisti" | "papaz_kacti">("chess");\n',
    '  const [tekKartGame, setTekKartGame] = useState<TekKartGame | null>(null);\n'
    '  const [tekKartBusy, setTekKartBusy] = useState(false);\n'
    '  const [tekKartError, setTekKartError] = useState("");\n'
    '  const [activeGameTab, setActiveGameTab] = useState<\n'
    '    "chess" | "pisti" | "papaz_kacti" | "tek_kart"\n'
    '  >("chess");\n',
)

replace_once(
    '    void fetchPapazKactiState();\n\n    return connectToJamBoxRoom',
    '    void fetchPapazKactiState();\n\n'
    '    const fetchTekKartState = async () => {\n'
    '      try {\n'
    '        setTekKartGame(await getJamBoxTekKartGame(jamBoxUserId, activeRoomCode));\n'
    '      } catch {\n'
    '        setTekKartGame(null);\n'
    '      }\n'
    '    };\n'
    '    void fetchTekKartState();\n\n'
    '    return connectToJamBoxRoom',
)

replace_once(
    '      onPapazKactiUpdated: async () => {\n'
    '        try {\n'
    '          setPapazKactiGame(await getJamBoxPapazKactiGame(jamBoxUserId, activeRoomCode));\n'
    '        } catch (error) {\n'
    '          console.error("Papaz Kaçtı masası güncellenemedi:", error);\n'
    '          setPapazKactiGame(null);\n'
    '        }\n'
    '      },\n'
    '      onMessageCreated:',
    '      onPapazKactiUpdated: async () => {\n'
    '        try {\n'
    '          setPapazKactiGame(await getJamBoxPapazKactiGame(jamBoxUserId, activeRoomCode));\n'
    '        } catch (error) {\n'
    '          console.error("Papaz Kaçtı masası güncellenemedi:", error);\n'
    '          setPapazKactiGame(null);\n'
    '        }\n'
    '      },\n'
    '      onTekKartUpdated: async () => {\n'
    '        try {\n'
    '          setTekKartGame(await getJamBoxTekKartGame(jamBoxUserId, activeRoomCode));\n'
    '        } catch (error) {\n'
    '          console.error("Tek Kart masası güncellenemedi:", error);\n'
    '          setTekKartGame(null);\n'
    '        }\n'
    '      },\n'
    '      onMessageCreated:',
)

replace_once(
    '        setPapazKactiGame(null);\n        setView("home");\n',
    '        setPapazKactiGame(null);\n        setTekKartGame(null);\n        setView("home");\n',
)

replace_count(
    '    setPapazKactiGame(null);\n    setPapazKactiError("");\n    setView("home");\n',
    '    setPapazKactiGame(null);\n'
    '    setPapazKactiError("");\n'
    '    setTekKartGame(null);\n'
    '    setTekKartError("");\n'
    '    setView("home");\n',
    2,
)

handlers = '''\n  async function openTekKartTable() {
    if (!activeRoom || !jamBoxUserId) return;
    setTekKartBusy(true);
    setTekKartError("");
    try {
      setTekKartGame(await createJamBoxTekKartGame(jamBoxUserId, activeRoom.code));
      setActiveGameTab("tek_kart");
      setToast("Tek Kart daveti sohbete gönderildi.");
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Tek Kart masası açılamadı.";
      setTekKartError(msg);
      setToast(msg);
    } finally {
      setTekKartBusy(false);
    }
  }

  async function acceptTekKartInvite() {
    if (!activeRoom || !jamBoxUserId) return;
    setTekKartBusy(true);
    setTekKartError("");
    try {
      setTekKartGame(await joinJamBoxTekKartGame(jamBoxUserId, activeRoom.code));
      setToast("Tek Kart masasına katıldın.");
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Tek Kart masasına katılamadın.";
      setTekKartError(msg);
      setToast(msg);
    } finally {
      setTekKartBusy(false);
    }
  }

  async function startTekKartGame() {
    if (!activeRoom || !jamBoxUserId) return;
    setTekKartBusy(true);
    setTekKartError("");
    try {
      setTekKartGame(await startJamBoxTekKartGame(jamBoxUserId, activeRoom.code));
      setToast("Tek Kart başladı.");
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Tek Kart başlatılamadı.";
      setTekKartError(msg);
      setToast(msg);
    } finally {
      setTekKartBusy(false);
    }
  }

  async function playTekKartCard(cardId: string, chosenColor?: TekKartColor) {
    if (!activeRoom || !jamBoxUserId) return;
    setTekKartBusy(true);
    setTekKartError("");
    try {
      setTekKartGame(
        await playJamBoxTekKartCard(jamBoxUserId, activeRoom.code, cardId, chosenColor),
      );
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Kart oynanamadı.";
      setTekKartError(msg);
      setToast(msg);
    } finally {
      setTekKartBusy(false);
    }
  }

  async function drawTekKartCard() {
    if (!activeRoom || !jamBoxUserId) return;
    setTekKartBusy(true);
    setTekKartError("");
    try {
      setTekKartGame(await drawJamBoxTekKartCard(jamBoxUserId, activeRoom.code));
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Kart çekilemedi.";
      setTekKartError(msg);
      setToast(msg);
    } finally {
      setTekKartBusy(false);
    }
  }

  async function announceTekKart() {
    if (!activeRoom || !jamBoxUserId) return;
    setTekKartBusy(true);
    setTekKartError("");
    try {
      setTekKartGame(await callJamBoxTekKart(jamBoxUserId, activeRoom.code));
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Tek Kart çağrısı yapılamadı.";
      setTekKartError(msg);
      setToast(msg);
    } finally {
      setTekKartBusy(false);
    }
  }

  async function restartTekKartGame() {
    if (!activeRoom || !jamBoxUserId) return;
    setTekKartBusy(true);
    setTekKartError("");
    try {
      setTekKartGame(await restartJamBoxTekKartGame(jamBoxUserId, activeRoom.code));
      setToast("Yeni Tek Kart oyunu başladı.");
    } catch (error) {
      const msg = error instanceof JamBoxApiError ? error.message : "Yeni Tek Kart oyunu başlatılamadı.";
      setTekKartError(msg);
      setToast(msg);
    } finally {
      setTekKartBusy(false);
    }
  }
'''
replace_once(
    '\n  async function playTrackTogether(track: SpotifyTrack) {',
    handlers + '\n  async function playTrackTogether(track: SpotifyTrack) {',
)

invite = '''                    {item.message_type === "tek_kart_invite" && (
                      <div className="chess-invite-card">
                        <span>🎨</span>
                        <div>
                          <strong>Tek Kart daveti</strong>
                          <small>Müzik devam ederken masaya katıl.</small>
                        </div>
                        {tekKartGame?.status === "waiting" &&
                          !tekKartGame.players.some((player) => player.user_id === jamBoxUserId) && (
                            <button type="button" onClick={acceptTekKartInvite} disabled={tekKartBusy}>
                              Katıl
                            </button>
                          )}
                        {tekKartGame?.status === "active" && <b>Oyun başladı</b>}
                      </div>
                    )}
'''
replace_once(
    '                    <div className="message-reactions">',
    invite + '                    <div className="message-reactions">',
)

replace_once(
    '              <button\n'
    '                type="button"\n'
    '                className={`game-tab${activeGameTab === "papaz_kacti" ? " active" : ""}`}\n'
    '                onClick={() => setActiveGameTab("papaz_kacti")}\n'
    '              >\n'
    '                🃏 Papaz Kaçtı\n'
    '              </button>\n'
    '            </nav>',
    '              <button\n'
    '                type="button"\n'
    '                className={`game-tab${activeGameTab === "papaz_kacti" ? " active" : ""}`}\n'
    '                onClick={() => setActiveGameTab("papaz_kacti")}\n'
    '              >\n'
    '                🃏 Papaz Kaçtı\n'
    '              </button>\n'
    '              <button\n'
    '                type="button"\n'
    '                className={`game-tab${activeGameTab === "tek_kart" ? " active" : ""}`}\n'
    '                onClick={() => setActiveGameTab("tek_kart")}\n'
    '              >\n'
    '                🎨 Tek Kart\n'
    '              </button>\n'
    '            </nav>',
)

render = '''

            {activeGameTab === "tek_kart" && (
              <TekKartActivity
                game={tekKartGame}
                currentUserId={jamBoxUserId}
                busy={tekKartBusy}
                error={tekKartError}
                onCreate={openTekKartTable}
                onJoin={acceptTekKartInvite}
                onStart={startTekKartGame}
                onPlay={playTekKartCard}
                onDraw={drawTekKartCard}
                onCall={announceTekKart}
                onRestart={restartTekKartGame}
              />
            )}'''
replace_once(
    '            {activeGameTab === "papaz_kacti" && (\n'
    '              <PapazKactiActivity\n'
    '                game={papazKactiGame}\n'
    '                currentUserId={jamBoxUserId}\n'
    '                busy={papazKactiBusy}\n'
    '                error={papazKactiError}\n'
    '                onCreate={openPapazKactiTable}\n'
    '                onJoin={acceptPapazKactiInvite}\n'
    '                onStart={startPapazKactiGame}\n'
    '                onDrawCard={drawPapazKactiCard}\n'
    '                onRestart={restartPapazKactiGame}\n'
    '              />\n'
    '            )}\n'
    '          </section>',
    '            {activeGameTab === "papaz_kacti" && (\n'
    '              <PapazKactiActivity\n'
    '                game={papazKactiGame}\n'
    '                currentUserId={jamBoxUserId}\n'
    '                busy={papazKactiBusy}\n'
    '                error={papazKactiError}\n'
    '                onCreate={openPapazKactiTable}\n'
    '                onJoin={acceptPapazKactiInvite}\n'
    '                onStart={startPapazKactiGame}\n'
    '                onDrawCard={drawPapazKactiCard}\n'
    '                onRestart={restartPapazKactiGame}\n'
    '              />\n'
    '            )}' + render + '\n          </section>',
)

path.write_text(content)
print("Tek Kart JamBoxApp integration applied.")
