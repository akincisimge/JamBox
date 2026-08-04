"use client";

import type { PapazKactiCard, PapazKactiGame, JamBoxUser } from "../../types/jambox";
import styles from "./PistiActivity.module.css";

const suitSymbols: Record<PapazKactiCard["suit"], string> = {
  clubs: "♣",
  diamonds: "♦",
  hearts: "♥",
  spades: "♠",
};

const suitNames: Record<PapazKactiCard["suit"], string> = {
  clubs: "sinek",
  diamonds: "karo",
  hearts: "kupa",
  spades: "maça",
};

const faceLabels: Partial<Record<PapazKactiCard["rank"], string>> = {
  J: "VALE",
  Q: "KIZ",
  K: "PAPAZ",
};

const redSuits = new Set<PapazKactiCard["suit"]>(["diamonds", "hearts"]);

function PlayingCard({
  card,
  className = "",
  disabled = false,
  onClick,
}: {
  card: PapazKactiCard;
  className?: string;
  disabled?: boolean;
  onClick?: () => void;
}) {
  const symbol = suitSymbols[card.suit];
  const red = redSuits.has(card.suit);
  const faceLabel = faceLabels[card.rank];
  const isKing = card.rank === "K";

  return (
    <button
      type="button"
      className={`${styles.card} ${className} ${red ? styles.red : ""}`}
      disabled={disabled}
      onClick={onClick}
      aria-label={`${faceLabel ?? card.rank} ${suitNames[card.suit]}`}
      title={`${faceLabel ?? card.rank} ${suitNames[card.suit]}`}
      style={
        isKing
          ? {
              border: "2px solid #e5aa36",
              background: "linear-gradient(145deg, #fff8dc, #fff1bd)",
              boxShadow: "0 12px 26px rgba(0,0,0,.34), 0 0 0 3px rgba(229,170,54,.2)",
            }
          : undefined
      }
    >
      <span className={styles.rank}>{card.rank}</span>
      <span className={styles.suit}>{symbol}</span>
      <span className={styles.bigSuit} aria-hidden="true">
        {faceLabel ? (
          <span
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 2,
              lineHeight: 1,
            }}
          >
            <strong style={{ fontSize: "clamp(24px, 3.5vw, 38px)" }}>{card.rank}</strong>
            <small
              style={{
                fontFamily: '"Avenir Next", "Segoe UI", sans-serif',
                fontSize: isKing ? 9 : 8,
                letterSpacing: ".08em",
                fontWeight: 950,
              }}
            >
              {faceLabel}
            </small>
            <em style={{ fontSize: 16, fontStyle: "normal" }}>{symbol}</em>
          </span>
        ) : (
          symbol
        )}
      </span>
    </button>
  );
}

function CardBack({
  className = "",
  onClick,
  disabled = false,
}: {
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
}) {
  if (onClick) {
    return (
      <button
        type="button"
        className={`${styles.cardBack} ${className}`}
        onClick={onClick}
        disabled={disabled}
        aria-label="Kart çek"
        style={{ cursor: disabled ? "default" : "pointer" }}
      />
    );
  }
  return <span className={`${styles.cardBack} ${className}`} aria-hidden="true" />;
}

type Props = {
  game: PapazKactiGame | null;
  currentUserId: string;
  busy: boolean;
  error?: string;
  onCreate: () => void;
  onJoin: () => void;
  onStart: () => void;
  onDrawCard: (cardIndex: number) => void;
  onRestart: () => void;
};

export function PapazKactiActivity({
  game,
  currentUserId,
  busy,
  error,
  onCreate,
  onJoin,
  onStart,
  onDrawCard,
  onRestart,
}: Props) {
  const isPlayer = Boolean(
    game &&
      [
        game.player_one_user_id,
        game.player_two_user_id,
        game.player_three_user_id,
        game.player_four_user_id,
      ].includes(currentUserId),
  );

  const isCreator = Boolean(game && game.creator_id === currentUserId);
  const myTurn = game?.status === "active" && game.turn_user_id === currentUserId;

  const players: JamBoxUser[] = [];
  if (game?.player_one_user) players.push(game.player_one_user);
  if (game?.player_two_user) players.push(game.player_two_user);
  if (game?.player_three_user) players.push(game.player_three_user);
  if (game?.player_four_user) players.push(game.player_four_user);

  let targetPlayerId: string | null = null;
  let targetPlayerUser: JamBoxUser | null = null;
  if (game?.status === "active" && myTurn) {
    const myIndex = players.findIndex((player) => player.id === currentUserId);
    for (let offset = 1; offset < players.length; offset += 1) {
      const index = (myIndex + offset) % players.length;
      if ((game.hand_counts[players[index].id] ?? 0) > 0) {
        targetPlayerId = players[index].id;
        targetPlayerUser = players[index];
        break;
      }
    }
  }

  const targetHandCount = targetPlayerId ? game?.hand_counts[targetPlayerId] ?? 0 : 0;
  const loserName = !game?.loser_user_id
    ? null
    : players.find((player) => player.id === game.loser_user_id)?.display_name ?? null;

  return (
    <section className={styles.activity} aria-label="Papaz Kaçtı masası">
      <div className={styles.copy}>
        <span className={styles.eyebrow}>PLAY TOGETHER · PAPAZ KAÇTI</span>
        <h2>
          {!game
            ? "Masa aç"
            : game.status === "waiting"
              ? "Oyuncular bekleniyor"
              : game.status === "active"
                ? "Oyun devam ediyor"
                : "Oyun bitti!"}
        </h2>
        <p>
          Çiftler otomatik atılır. <strong>K / PAPAZ</strong> yazılı altın çerçeveli
          kartı elinde bırakmamaya çalış. J Vale, Q Kız, K Papazdır.
        </p>

        {!game && (
          <button className={styles.primary} onClick={onCreate} disabled={busy}>
            🃏 Papaz Kaçtı masası aç
          </button>
        )}

        {game?.status === "waiting" && !isPlayer && (
          <button className={styles.primary} onClick={onJoin} disabled={busy || players.length >= 4}>
            Masaya katıl ({players.length}/4)
          </button>
        )}

        {game?.status === "waiting" && isPlayer && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <div className={styles.status} role="status">
              <i className={styles.statusDot} /> Bekleniyor ({players.length}/4)
            </div>
            {isCreator && players.length >= 2 && (
              <button className={styles.primary} onClick={onStart} disabled={busy}>
                Oyunu başlat
              </button>
            )}
          </div>
        )}

        {game?.status === "active" && (
          <div className={styles.status} role="status" aria-live="polite">
            <i className={styles.statusDot} />
            {myTurn && targetPlayerUser
              ? `Sıra sende · ${targetPlayerUser.display_name} kullanıcısından kart çek`
              : "Hamle bekleniyor"}
          </div>
        )}

        {game?.status === "finished" && (
          <>
            <div className={styles.status}>
              {loserName ? `${loserName} papazı elinde tuttu!` : "Oyun bitti"}
            </div>
            {isPlayer && (
              <button className={styles.primary} onClick={onRestart} disabled={busy}>
                ↻ Yeni oyun
              </button>
            )}
          </>
        )}

        {game && (
          <div className={styles.players} style={{ gridTemplateColumns: "1fr", gap: 10 }}>
            {players.map((player) => {
              const cardCount = game.hand_counts[player.id] ?? 0;
              const isTarget = player.id === targetPlayerId;
              const isMe = player.id === currentUserId;
              return (
                <div
                  key={player.id}
                  className={styles.player}
                  style={{
                    border: isTarget && myTurn
                      ? "1px solid #ff9eb1"
                      : game.turn_user_id === player.id
                        ? "1px solid #fff"
                        : undefined,
                    opacity: cardCount === 0 && game.status === "active" ? 0.5 : 1,
                  }}
                >
                  <strong>{player.display_name} {isMe && "(Sen)"}</strong>
                  <small>{cardCount > 0 ? `${cardCount} kart` : "Bitti!"}</small>
                </div>
              );
            })}
          </div>
        )}

        {error && <p className={styles.error}>{error}</p>}
      </div>

      {game && game.status === "active" && (
        <div className={styles.table}>
          <div className={styles.opponentHand} aria-label={`Hedef oyuncuda ${targetHandCount} kart var`}>
            {targetHandCount > 0 ? (
              Array.from({ length: targetHandCount }, (_, index) => (
                <CardBack
                  key={`target-${index}`}
                  onClick={myTurn && targetPlayerId ? () => onDrawCard(index) : undefined}
                  disabled={!myTurn || busy}
                />
              ))
            ) : (
              <div style={{ color: "var(--muted)", fontSize: 11 }}>Sırasını bekleyen oyuncu</div>
            )}
          </div>

          <div className={styles.center} style={{ gridTemplateColumns: "1fr" }}>
            <div className={styles.pile}>
              {myTurn && targetPlayerUser && (
                <span
                  className={styles.status}
                  style={{ background: "transparent", border: 0, fontSize: 12, fontWeight: "bold" }}
                >
                  ⬆️ {targetPlayerUser.display_name} kullanıcısından bir kart seç
                </span>
              )}
            </div>
          </div>

          <div className={styles.myHand} aria-label="Elindeki kartlar">
            {game.hand.map((card) => (
              <PlayingCard
                card={card}
                className={styles.handCard}
                key={card.id}
                disabled
              />
            ))}
            {game.hand.length === 0 && (
              <div style={{ color: "#fff", fontSize: 14, fontWeight: "bold", marginBottom: 20 }}>
                Elindeki kartlar bitti, kurtuldun!
              </div>
            )}
          </div>

          <small className={styles.turnHint}>
            Çiftler otomatik atılır. Altın çerçeveli K / PAPAZ kartı en sonda elinde kalan oyuncu kaybeder.
          </small>
        </div>
      )}
    </section>
  );
}
