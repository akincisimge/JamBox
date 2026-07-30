"use client";

import { useEffect, useMemo, useState } from "react";
import {
  connectToJamBoxRoom,
  createJamBoxPistiGame,
  getJamBoxPistiGame,
  JamBoxApiError,
  joinJamBoxPistiGame,
  playJamBoxPistiCard,
  restartJamBoxPistiGame,
} from "../../lib/jambox/client";
import type { ChessGame, PistiGame } from "../../types/jambox";
import { PistiActivity } from "./PistiActivity";
import pistiStyles from "./PistiActivity.module.css";

const ACTIVE_ROOM_STORAGE_KEY = "jambox_active_room_code";

const pieces: Record<string, string> = {
  K: "♔", Q: "♕", R: "♖", B: "♗", N: "♘", P: "♙",
  k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟",
};

function boardFromFen(fen?: string) {
  const position = (fen ?? "8/8/8/8/8/8/8/8").split(" ")[0];
  return position.split("/").flatMap((rank) => {
    const row: string[] = [];
    for (const token of rank) {
      if (/\d/.test(token)) row.push(...Array(Number(token)).fill(""));
      else row.push(token);
    }
    return row;
  });
}

function squareName(index: number) {
  return `${"abcdefgh"[index % 8]}${8 - Math.floor(index / 8)}`;
}

type Props = {
  game: ChessGame | null;
  currentUserId: string;
  busy: boolean;
  onCreate: () => void;
  onJoin: () => void;
  onAddTestOpponent: () => void;
  onMove: (from: string, to: string, promotion?: string) => void;
  onRestart: () => void;
  onResign: () => void;
  onDraw: () => void;
};

export function ChessActivity({
  game,
  currentUserId,
  busy,
  onCreate,
  onJoin,
  onAddTestOpponent,
  onMove,
  onRestart,
  onResign,
  onDraw,
}: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const [activeActivity, setActiveActivity] = useState<"pisti" | "chess">(
    game?.status === "active" ? "chess" : "pisti",
  );
  const [roomCode, setRoomCode] = useState("");
  const [pistiGame, setPistiGame] = useState<PistiGame | null>(null);
  const [pistiBusy, setPistiBusy] = useState(false);
  const [pistiError, setPistiError] = useState("");

  useEffect(() => {
    setRoomCode(window.localStorage.getItem(ACTIVE_ROOM_STORAGE_KEY) ?? "");
  }, []);

  useEffect(() => {
    if (!roomCode || !currentUserId) return;

    let stopped = false;

    const refreshPisti = async () => {
      try {
        const nextGame = await getJamBoxPistiGame(currentUserId, roomCode);
        if (stopped) return;
        setPistiGame(nextGame);
        setPistiError("");
        if (nextGame.status === "waiting" || nextGame.status === "active") {
          setActiveActivity("pisti");
        }
      } catch (error) {
        if (stopped) return;
        if (error instanceof JamBoxApiError && error.status === 404) {
          setPistiGame(null);
          setPistiError("");
          return;
        }
        setPistiError(
          error instanceof Error ? error.message : "Pişti masası yüklenemedi.",
        );
      }
    };

    void refreshPisti();
    const disconnect = connectToJamBoxRoom(currentUserId, roomCode, {
      onRoomUpdated: () => undefined,
      onPlaybackUpdated: () => undefined,
      onChessUpdated: () => undefined,
      onPistiUpdated: () => {
        void refreshPisti();
      },
      onMessageCreated: () => undefined,
      onMessageUpdated: () => undefined,
      onRoomClosed: () => {
        setPistiGame(null);
      },
    });

    return () => {
      stopped = true;
      disconnect();
    };
  }, [currentUserId, roomCode]);

  async function runPistiAction(
    action: () => Promise<PistiGame>,
    fallbackMessage: string,
  ) {
    if (!roomCode || !currentUserId) {
      setPistiError("Aktif oda bilgisi bulunamadı.");
      return;
    }

    setPistiBusy(true);
    setPistiError("");
    try {
      setPistiGame(await action());
      setActiveActivity("pisti");
    } catch (error) {
      setPistiError(
        error instanceof JamBoxApiError ? error.message : fallbackMessage,
      );
    } finally {
      setPistiBusy(false);
    }
  }

  const canUseJamBot = process.env.NODE_ENV === "development";
  const board = useMemo(() => boardFromFen(game?.fen), [game?.fen]);
  const legalMoves = useMemo(() => game?.legal_moves ?? [], [game?.legal_moves]);
  const isPlayer = game?.white_user_id === currentUserId || game?.black_user_id === currentUserId;
  const myColor = game?.white_user_id === currentUserId ? "white" : game?.black_user_id === currentUserId ? "black" : null;
  const boardSquares = useMemo(() => {
    const squares = board.map((piece, index) => ({ piece, index }));
    return myColor === "black" ? squares.reverse() : squares;
  }, [board, myColor]);
  const canMove = game?.status === "active" && isPlayer && game.turn === myColor;
  const movableSquares = useMemo(() => new Set(legalMoves.map((move) => move.slice(0, 2))), [legalMoves]);
  const targetSquares = useMemo(
    () => new Set(selected ? legalMoves.filter((move) => move.startsWith(selected)).map((move) => move.slice(2, 4)) : []),
    [legalMoves, selected],
  );
  const drawOfferedByMe = game?.draw_offer_user_id === currentUserId;
  const drawOfferedByOpponent = Boolean(game?.draw_offer_user_id && !drawOfferedByMe);
  const moveRows = useMemo(() => {
    const labels = game?.move_labels ?? [];
    return Array.from({ length: Math.ceil(labels.length / 2) }, (_, index) => ({
      number: index + 1,
      white: labels[index * 2],
      black: labels[index * 2 + 1],
    }));
  }, [game?.move_labels]);

  const chooseSquare = (index: number) => {
    if (!canMove || busy) return;
    const square = squareName(index);
    if (selected && targetSquares.has(square)) {
      const legalMove = legalMoves.find((move) => move.startsWith(`${selected}${square}`));
      onMove(selected, square, legalMove?.slice(4) || undefined);
      setSelected(null);
      return;
    }
    if (selected === square) {
      setSelected(null);
      return;
    }
    setSelected(movableSquares.has(square) ? square : null);
  };

  const resultText = game?.result === "resignation"
    ? "Teslim ile tamamlandı"
    : game?.result === "1/2-1/2"
      ? "Berabere"
      : game?.result ?? "Tamamlandı";

  return (
    <div className={pistiStyles.playTogetherShell}>
      <div className={pistiStyles.activityTabs} role="tablist" aria-label="Oda oyunları">
        <button
          type="button"
          role="tab"
          aria-selected={activeActivity === "pisti"}
          className={`${pistiStyles.tab} ${activeActivity === "pisti" ? pistiStyles.activeTab : ""}`}
          onClick={() => setActiveActivity("pisti")}
        >
          🂡 Pişti
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeActivity === "chess"}
          className={`${pistiStyles.tab} ${activeActivity === "chess" ? pistiStyles.activeTab : ""}`}
          onClick={() => setActiveActivity("chess")}
        >
          ♟ Satranç
        </button>
      </div>

      {activeActivity === "pisti" ? (
        <PistiActivity
          game={pistiGame}
          currentUserId={currentUserId}
          busy={pistiBusy}
          error={pistiError}
          onCreate={() => {
            void runPistiAction(
              () => createJamBoxPistiGame(currentUserId, roomCode),
              "Pişti masası açılamadı.",
            );
          }}
          onJoin={() => {
            void runPistiAction(
              () => joinJamBoxPistiGame(currentUserId, roomCode),
              "Pişti masasına katılamadın.",
            );
          }}
          onPlayCard={(cardId) => {
            void runPistiAction(
              () => playJamBoxPistiCard(currentUserId, roomCode, cardId),
              "Kart oynanamadı.",
            );
          }}
          onRestart={() => {
            void runPistiAction(
              () => restartJamBoxPistiGame(currentUserId, roomCode),
              "Yeni Pişti oyunu başlatılamadı.",
            );
          }}
        />
      ) : (
        <section className="chess-activity" aria-label="Satranç masası">
          <div className="chess-copy">
            <span className="music-panel-eyebrow">PLAY TOGETHER · SATRANÇ</span>
            <h2>{!game ? "Müzik çalarken bir masa aç" : game.status === "waiting" ? "Rakip bekleniyor" : game.status === "active" ? "Oyun başladı" : "Oyun tamamlandı"}</h2>
            <p>Müzik ve sohbet kesilmeden, oda içinde eşzamanlı oynayın.</p>
            {!game && <button className="chess-primary" onClick={onCreate} disabled={busy}>♟ Satranç masası aç</button>}
            {game?.status === "waiting" && game.creator_id !== currentUserId && <button className="chess-primary" onClick={onJoin} disabled={busy}>Masaya katıl</button>}
            {game?.status === "waiting" && game.creator_id === currentUserId && (
              <>
                <div className="chess-waiting"><i /> Sohbetteki davetin kabul edilmesi bekleniyor</div>
                {canUseJamBot && <button className="chess-test-button" onClick={onAddTestOpponent} disabled={busy}>♟ JamBot ile oyna</button>}
              </>
            )}
            {game?.status === "active" && <div className="chess-turn" role="status" aria-live="polite">{game.turn === "white" ? "Beyaz" : "Siyah"} hamlede {canMove && "· Sıra sende"}</div>}
            {game?.status === "finished" && <div className="chess-turn">{resultText}</div>}
            {game && (
              <div className="chess-players">
                <span><b>♔</b>{game.white_user.display_name}</span><em>VS</em>
                <span><b>♚</b>{game.black_user?.display_name ?? "Rakip bekleniyor"}</span>
              </div>
            )}
            {game?.status === "active" && isPlayer && (
              <div className="chess-actions">
                <button className="chess-secondary" onClick={onDraw} disabled={busy}>
                  {drawOfferedByOpponent ? "Beraberliği kabul et" : drawOfferedByMe ? "Teklifi geri çek" : "Beraberlik teklif et"}
                </button>
                <button className="chess-danger" onClick={onResign} disabled={busy}>Teslim ol</button>
              </div>
            )}
            {game?.status === "finished" && isPlayer && (
              <button className="chess-primary chess-restart" onClick={onRestart} disabled={busy}>↻ Yeni oyun</button>
            )}
            {drawOfferedByOpponent && <small className="chess-notice">Rakibin beraberlik teklif etti.</small>}
            {drawOfferedByMe && <small className="chess-notice">Beraberlik teklifin rakibe gönderildi.</small>}
            {canMove && <small className="chess-help">Bir taş seç; gidebileceği kareler parlayacak.</small>}
            {game && (
              <div className="chess-history">
                <div className="chess-history-heading"><strong>Hamleler</strong><span>{game.move_labels?.length ?? 0}</span></div>
                <div className="chess-history-list">
                  {moveRows.length === 0 ? <small>İlk hamle bekleniyor.</small> : moveRows.map((row) => (
                    <div className="chess-history-row" key={row.number}>
                      <b>{row.number}.</b><span>{row.white}</span><span>{row.black ?? "—"}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          {game && (
            <div className="chess-board" aria-label="Satranç tahtası">
              {boardSquares.map(({ piece, index }) => {
                const square = squareName(index);
                const isTarget = targetSquares.has(square);
                return (
                  <button
                    type="button"
                    key={square}
                    className={`${(Math.floor(index / 8) + index) % 2 ? "dark" : "light"}${selected === square ? " selected" : ""}${isTarget ? " legal-target" : ""}${movableSquares.has(square) && canMove ? " movable" : ""}${piece ? " occupied" : ""}`}
                    onClick={() => chooseSquare(index)}
                    disabled={!canMove || busy}
                    aria-label={`${square}${piece ? ` ${pieces[piece]}` : ""}`}
                  >
                    {pieces[piece] ?? ""}
                    {isTarget && <i />}
                  </button>
                );
              })}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
