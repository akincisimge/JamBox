"use client";

import type { CSSProperties } from "react";
import type { PistiCard, PistiGame } from "../../types/jambox";
import styles from "./PistiActivity.module.css";

const suitSymbols: Record<PistiCard["suit"], string> = {
  clubs: "♣",
  diamonds: "♦",
  hearts: "♥",
  spades: "♠",
};

const redSuits = new Set<PistiCard["suit"]>(["diamonds", "hearts"]);

type CardTransformStyle = CSSProperties & {
  "--card-x": string;
  "--card-y": string;
  "--card-rotation": string;
};

function PlayingCard({
  card,
  className = "",
  disabled = false,
  onClick,
  style,
}: {
  card: PistiCard;
  className?: string;
  disabled?: boolean;
  onClick?: () => void;
  style?: CSSProperties;
}) {
  const symbol = suitSymbols[card.suit];
  const red = redSuits.has(card.suit);

  return (
    <button
      type="button"
      className={`${styles.card} ${className} ${red ? styles.red : ""}`}
      disabled={disabled}
      onClick={onClick}
      style={style}
      aria-label={`${card.rank} ${card.suit}`}
    >
      <span className={styles.rank}>{card.rank}</span>
      <span className={styles.suit}>{symbol}</span>
      <span className={styles.bigSuit} aria-hidden="true">{symbol}</span>
    </button>
  );
}

type Props = {
  game: PistiGame | null;
  currentUserId: string;
  busy: boolean;
  error?: string;
  onCreate: () => void;
  onJoin: () => void;
  onPlayCard: (cardId: string) => void;
  onRestart: () => void;
};

export function PistiActivity({
  game,
  currentUserId,
  busy,
  error,
  onCreate,
  onJoin,
  onPlayCard,
  onRestart,
}: Props) {
  const isPlayer = Boolean(
    game &&
      (game.player_one_user_id === currentUserId ||
        game.player_two_user_id === currentUserId),
  );
  const myTurn = game?.status === "active" && game.turn_user_id === currentUserId;
  const opponentId =
    game?.player_one_user_id === currentUserId
      ? game.player_two_user_id
      : game?.player_one_user_id;
  const opponentHandCount = opponentId ? game?.hand_counts[opponentId] ?? 0 : 0;
  const myScore = game?.scores[currentUserId] ?? 0;
  const opponentScore = opponentId ? game?.scores[opponentId] ?? 0 : 0;
  const myCaptured = game?.captured_counts[currentUserId] ?? 0;
  const myPisti = game?.pisti_counts[currentUserId] ?? 0;
  const winnerName = !game?.winner_user_id
    ? null
    : game.winner_user_id === game.player_one_user_id
      ? game.player_one_user.display_name
      : game.winner_user_id === game.player_two_user_id
        ? game.player_two_user?.display_name ?? null
        : null;

  return (
    <section className={styles.activity} aria-label="Pişti masası">
      <div className={styles.copy}>
        <span className={styles.eyebrow}>PLAY TOGETHER · PİŞTİ</span>
        <h2>
          {!game
            ? "Kartları dağıt"
            : game.status === "waiting"
              ? "Rakip bekleniyor"
              : game.status === "active"
                ? "Pişti başladı"
                : "Oyun tamamlandı"}
        </h2>
        <p>Müzik ve sohbet devam ederken iki kişilik klasik Pişti oynayın.</p>

        {!game && (
          <button className={styles.primary} onClick={onCreate} disabled={busy}>
            🂡 Pişti masası aç
          </button>
        )}

        {game?.status === "waiting" && game.creator_id !== currentUserId && (
          <button className={styles.primary} onClick={onJoin} disabled={busy}>
            Masaya katıl
          </button>
        )}

        {game?.status === "waiting" && game.creator_id === currentUserId && (
          <div className={styles.status} role="status">
            <i className={styles.statusDot} /> Sohbetteki davet bekleniyor
          </div>
        )}

        {game?.status === "active" && (
          <div className={styles.status} role="status" aria-live="polite">
            <i className={styles.statusDot} />
            {myTurn ? "Sıra sende · Bir kart seç" : "Rakibin hamlesi bekleniyor"}
          </div>
        )}

        {game?.status === "finished" && (
          <>
            <div className={styles.status}>
              {winnerName ? `${winnerName} kazandı` : "Oyun berabere tamamlandı"}
            </div>
            {isPlayer && (
              <button className={styles.primary} onClick={onRestart} disabled={busy}>
                ↻ Yeni oyun
              </button>
            )}
          </>
        )}

        {game && (
          <>
            <div className={styles.players}>
              <div className={styles.player}>
                <strong>{game.player_one_user.display_name}</strong>
                <small>{game.scores[game.player_one_user_id] ?? 0} puan · {game.pisti_counts[game.player_one_user_id] ?? 0} pişti</small>
              </div>
              <span className={styles.versus}>VS</span>
              <div className={styles.player}>
                <strong>{game.player_two_user?.display_name ?? "Rakip bekleniyor"}</strong>
                <small>{game.player_two_user_id ? game.scores[game.player_two_user_id] ?? 0 : 0} puan · {game.player_two_user_id ? game.pisti_counts[game.player_two_user_id] ?? 0 : 0} pişti</small>
              </div>
            </div>
            <div className={styles.scoreboard}>
              <div><b>{myScore}</b><span>Puanın</span></div>
              <div><b>{myCaptured}</b><span>Topladığın</span></div>
              <div><b>{myPisti}</b><span>Pişti</span></div>
            </div>
          </>
        )}

        {error && <p className={styles.error}>{error}</p>}
      </div>

      {game && (
        <div className={styles.table}>
          <div className={styles.opponentHand} aria-label={`Rakibin ${opponentHandCount} kartı var`}>
            {Array.from({ length: opponentHandCount }, (_, index) => (
              <span className={styles.cardBack} key={index} aria-hidden="true" />
            ))}
          </div>

          <div className={styles.center}>
            <div className={styles.deck}>
              <span className={styles.deckCard} aria-hidden="true" />
              <b>{game.deck_count} kart</b>
            </div>

            <div className={styles.pile} aria-label={`Ortada ${game.table.length} kart var`}>
              {game.table.length === 0 ? (
                <span className={styles.emptyPile}>Orta boş</span>
              ) : (
                game.table.slice(-5).map((card, index, cards) => {
                  const offset = index - cards.length + 1;
                  const cardStyle: CardTransformStyle = {
                    "--card-x": `${offset * 5}px`,
                    "--card-y": `${offset * -3}px`,
                    "--card-rotation": `${offset * 2.5}deg`,
                  };
                  return (
                    <PlayingCard
                      card={card}
                      className={styles.tableCard}
                      key={card.id}
                      disabled
                      style={cardStyle}
                    />
                  );
                })
              )}
            </div>

            <div className={styles.captured}>
              <span>Toplanan</span>
              <b>{Object.values(game.captured_counts).reduce((sum, count) => sum + count, 0)}</b>
            </div>
          </div>

          <div className={styles.myHand} aria-label="Elindeki kartlar">
            {game.hand.map((card) => (
              <PlayingCard
                card={card}
                className={styles.handCard}
                key={card.id}
                disabled={!myTurn || busy}
                onClick={() => onPlayCard(card.id)}
              />
            ))}
          </div>

          <small className={styles.turnHint}>
            {game.status === "waiting"
              ? "İkinci oyuncu katıldığında kartlar dağıtılacak."
              : myTurn
                ? "Oynamak istediğin karta dokun."
                : `Rakip ${opponentScore} puanda.`}
          </small>
        </div>
      )}
    </section>
  );
}
