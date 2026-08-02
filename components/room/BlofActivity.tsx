"use client";

import { useMemo, useState } from "react";
import type { BlofCard, BlofDeclaredRank, BlofGame } from "../../types/jambox";
import styles from "./BlofActivity.module.css";

const ranks: BlofDeclaredRank[] = [
  "A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K",
];
const suitSymbols: Record<BlofCard["suit"], string> = {
  clubs: "♣",
  diamonds: "♦",
  hearts: "♥",
  spades: "♠",
};
const redSuits = new Set<BlofCard["suit"]>(["diamonds", "hearts"]);

type Props = {
  game: BlofGame | null;
  currentUserId: string;
  busy: boolean;
  error?: string;
  onCreate: () => void;
  onJoin: () => void;
  onStart: () => void;
  onPlay: (cardIds: string[], declaredRank: BlofDeclaredRank) => void;
  onCall: () => void;
  onAccept: () => void;
  onRestart: () => void;
};

export function BlofActivity({
  game,
  currentUserId,
  busy,
  error,
  onCreate,
  onJoin,
  onStart,
  onPlay,
  onCall,
  onAccept,
  onRestart,
}: Props) {
  const [selectedCards, setSelectedCards] = useState<string[]>([]);
  const [declaredRank, setDeclaredRank] = useState<BlofDeclaredRank>("A");

  const isPlayer = Boolean(game?.players.some((player) => player.user_id === currentUserId));
  const isCreator = game?.creator_id === currentUserId;
  const myTurn = game?.turn_user_id === currentUserId && game.status === "active";
  const canChallenge = Boolean(myTurn && game?.last_player_user_id);
  const mustResolveWinner = Boolean(myTurn && game?.pending_winner_user_id);
  const winnerName = useMemo(
    () => game?.players.find((player) => player.user_id === game.winner_user_id)?.user.display_name,
    [game],
  );

  function toggleCard(cardId: string) {
    setSelectedCards((current) =>
      current.includes(cardId)
        ? current.filter((id) => id !== cardId)
        : [...current, cardId],
    );
  }

  function submitPlay() {
    if (!selectedCards.length) return;
    onPlay(selectedCards, declaredRank);
    setSelectedCards([]);
  }

  const resultText = game?.last_result
    ? game.last_result.truthful
      ? `İlan doğru çıktı. Ortadaki kartları ${game.players.find((p) => p.user_id === game.last_result?.pile_receiver_user_id)?.user.display_name ?? "itiraz eden"} aldı.`
      : `Blöf yakalandı. Ortadaki kartları ${game.players.find((p) => p.user_id === game.last_result?.pile_receiver_user_id)?.user.display_name ?? "oynayan"} aldı.`
    : null;

  return (
    <section className={styles.activity} aria-label="Blöf masası">
      <div className={styles.copy}>
        <span className={styles.eyebrow}>PLAY TOGETHER · BLÖF</span>
        <h2>
          {!game
            ? "Yalanını iyi sakla"
            : game.status === "waiting"
              ? "Oyuncular bekleniyor"
              : game.status === "active"
                ? "Blöf masası açık"
                : `${winnerName ?? "Bir oyuncu"} kazandı`}
        </h2>
        <p>Kapalı kartlarını oyna, değerini ilan et ve rakibinin blöfünü yakala. 2–4 kişilik.</p>

        {!game && (
          <button className={styles.primary} onClick={onCreate} disabled={busy}>
            🎭 Blöf masası aç
          </button>
        )}

        {game?.status === "waiting" && (
          <div className={styles.waitingActions}>
            {!isPlayer && (
              <button className={styles.primary} onClick={onJoin} disabled={busy || game.players.length >= 4}>
                Masaya katıl ({game.players.length}/4)
              </button>
            )}
            {isPlayer && (
              <div className={styles.status}><i className={styles.dot} /> Oyuncular bekleniyor ({game.players.length}/4)</div>
            )}
            {isCreator && game.players.length >= 2 && (
              <button className={styles.primary} onClick={onStart} disabled={busy}>Oyunu başlat</button>
            )}
          </div>
        )}

        {game?.status === "active" && (
          <div className={styles.status} role="status">
            <i className={styles.dot} />
            {myTurn
              ? mustResolveWinner
                ? "Son hamle için Blöf diyebilir veya kabul edebilirsin"
                : canChallenge
                  ? "Sıra sende · Kart oyna veya Blöf de"
                  : "Sıra sende · Kartlarını seç"
              : "Rakibin hamlesi bekleniyor"}
          </div>
        )}

        {game && (
          <div className={styles.players}>
            {game.players.map((player) => (
              <div
                className={`${styles.player}${player.is_current_turn ? ` ${styles.playerActive}` : ""}`}
                key={player.user_id}
              >
                <strong>{player.user.display_name}{player.user_id === currentUserId ? " (Sen)" : ""}</strong>
                <small>{player.hand_count} kart · #{player.player_order + 1}</small>
              </div>
            ))}
          </div>
        )}

        {resultText && <div className={styles.result}>{resultText}</div>}
        {error && <p className={styles.error}>{error}</p>}

        {game?.status === "finished" && isCreator && (
          <button className={styles.primary} onClick={onRestart} disabled={busy}>↻ Yeni oyun</button>
        )}
      </div>

      {game?.status === "active" && (
        <div className={styles.table}>
          <div className={styles.center}>
            <div className={styles.pile} aria-label={`Ortada ${game.pile_count} kart var`}>
              {game.pile_count > 0 ? (
                <>
                  <span className={styles.back} />
                  <span className={styles.back} />
                  <span className={styles.back} />
                </>
              ) : null}
            </div>
            <div className={styles.lastPlay}>
              <span>Ortada <b>{game.pile_count}</b> kart</span>
              <span>Son ilan <b>{game.last_declared_rank ?? "—"}</b></span>
              <span>Son hamle <b>{game.last_play_count || 0}</b> kart</span>
            </div>
          </div>

          <div className={styles.hand} aria-label="Elindeki kartlar">
            {game.hand.map((card) => {
              const selected = selectedCards.includes(card.id);
              return (
                <button
                  type="button"
                  key={card.id}
                  className={`${styles.card}${selected ? ` ${styles.cardSelected}` : ""}${redSuits.has(card.suit) ? ` ${styles.red}` : ""}`}
                  onClick={() => toggleCard(card.id)}
                  disabled={!myTurn || mustResolveWinner || busy}
                  aria-pressed={selected}
                >
                  <span className={styles.rank}>{card.rank}</span>
                  <span className={styles.suit}>{suitSymbols[card.suit]}</span>
                </button>
              );
            })}
          </div>

          <div className={styles.controls}>
            <select
              value={declaredRank}
              onChange={(event) => setDeclaredRank(event.target.value as BlofDeclaredRank)}
              disabled={!myTurn || mustResolveWinner || busy}
              aria-label="İlan edilen kart değeri"
            >
              {ranks.map((rank) => <option key={rank} value={rank}>{rank} ilan et</option>)}
            </select>
            <button
              className={styles.primary}
              onClick={submitPlay}
              disabled={!myTurn || mustResolveWinner || busy || selectedCards.length === 0}
            >
              Kartları Oyna ({selectedCards.length})
            </button>
            {canChallenge && (
              <button className={styles.danger} onClick={onCall} disabled={busy}>Blöf De</button>
            )}
            {mustResolveWinner && (
              <button className={styles.secondary} onClick={onAccept} disabled={busy}>Son Hamleyi Kabul Et</button>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
