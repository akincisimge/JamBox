"use client";

import { useMemo, useState } from "react";
import type { ChessGame } from "../../types/jambox";

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
  onMove: (from: string, to: string) => void;
};

export function ChessActivity({ game, currentUserId, busy, onCreate, onJoin, onAddTestOpponent, onMove }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const board = useMemo(() => boardFromFen(game?.fen), [game?.fen]);
  const isPlayer = game?.white_user_id === currentUserId || game?.black_user_id === currentUserId;
  const myColor = game?.white_user_id === currentUserId ? "white" : game?.black_user_id === currentUserId ? "black" : null;
  const canMove = game?.status === "active" && isPlayer && game.turn === myColor;

  const chooseSquare = (index: number) => {
    if (!canMove) return;
    const square = squareName(index);
    if (!selected) {
      if (board[index]) setSelected(square);
      return;
    }
    if (selected === square) {
      setSelected(null);
      return;
    }
    onMove(selected, square);
    setSelected(null);
  };

  return (
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
            <button className="chess-test-button" onClick={onAddTestOpponent} disabled={busy}>
              ⚙ Test rakibi ekle
            </button>
          </>
        )}
        {game?.status === "active" && <div className="chess-turn">{game.turn === "white" ? "Beyaz" : "Siyah"} hamlede {canMove && "· Sıra sende"}</div>}
        {game?.status === "finished" && <div className="chess-turn">Sonuç: {game.result ?? "Tamamlandı"}</div>}
        {game && (
          <div className="chess-players">
            <span><b>♔</b>{game.white_user.display_name}</span>
            <em>VS</em>
            <span><b>♚</b>{game.black_user?.display_name ?? "Rakip bekleniyor"}</span>
          </div>
        )}
      </div>
      {game && (
        <div className="chess-board" aria-label="Satranç tahtası">
          {board.map((piece, index) => {
            const square = squareName(index);
            return (
              <button
                type="button"
                key={square}
                className={`${(Math.floor(index / 8) + index) % 2 ? "dark" : "light"}${selected === square ? " selected" : ""}`}
                onClick={() => chooseSquare(index)}
                disabled={!canMove || busy}
                aria-label={`${square}${piece ? ` ${pieces[piece]}` : ""}`}
              >
                {pieces[piece] ?? ""}
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
