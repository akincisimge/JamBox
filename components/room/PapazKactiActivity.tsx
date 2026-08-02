"use client";

import type { CSSProperties } from "react";
import type { PapazKactiCard, PapazKactiGame, JamBoxUser } from "../../types/jambox";
import styles from "./PistiActivity.module.css";

const suitSymbols: Record<PapazKactiCard["suit"], string> = {
  clubs: "♣",
  diamonds: "♦",
  hearts: "♥",
  spades: "♠",
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

  return (
    <button
      type="button"
      className={`${styles.card} ${className} ${red ? styles.red : ""}`}
      disabled={disabled}
      onClick={onClick}
      aria-label={`${card.rank} ${card.suit}`}
    >
      <span className={styles.rank}>{card.rank}</span>
      <span className={styles.suit}>{symbol}</span>
      <span className={styles.bigSuit} aria-hidden="true">{symbol}</span>
    </button>
  );
}

function CardBack({ className = "", onClick, disabled = false }: { className?: string, onClick?: () => void, disabled?: boolean }) {
  if (onClick) {
    return (
      <button 
        type="button" 
        className={`${styles.cardBack} ${className}`} 
        onClick={onClick}
        disabled={disabled}
        aria-label="Kart Çek"
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
    game && [game.player_one_user_id, game.player_two_user_id, game.player_three_user_id, game.player_four_user_id].includes(currentUserId)
  );
  
  const isCreator = Boolean(game && game.creator_id === currentUserId);
  const myTurn = game?.status === "active" && game.turn_user_id === currentUserId;
  
  const players = [];
  if (game?.player_one_user) players.push(game.player_one_user);
  if (game?.player_two_user) players.push(game.player_two_user);
  if (game?.player_three_user) players.push(game.player_three_user);
  if (game?.player_four_user) players.push(game.player_four_user);
  
  // Target player to draw from
  let targetPlayerId: string | null = null;
  let targetPlayerUser: JamBoxUser | null = null;
  if (game?.status === "active" && myTurn) {
    const myIndex = players.findIndex(p => p.id === currentUserId);
    for (let i = 1; i < players.length; i++) {
      const idx = (myIndex + i) % players.length;
      if (game.hand_counts[players[idx].id] > 0) {
        targetPlayerId = players[idx].id;
        targetPlayerUser = players[idx];
        break;
      }
    }
  }
  
  const targetHandCount = targetPlayerId ? game?.hand_counts[targetPlayerId] ?? 0 : 0;
  
  const loserName = !game?.loser_user_id
    ? null
    : players.find(p => p.id === game.loser_user_id)?.display_name ?? null;

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
        <p>Klasik Papaz Kaçtı! Çiftleri at, papazı elinde bırakmamaya çalış. 2-4 Kişilik.</p>

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
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <div className={styles.status} role="status">
              <i className={styles.statusDot} /> Bekleniyor ({players.length}/4)
            </div>
            {isCreator && players.length >= 2 && (
              <button className={styles.primary} onClick={onStart} disabled={busy}>
                Oyunu Başlat
              </button>
            )}
          </div>
        )}

        {game?.status === "active" && (
          <div className={styles.status} role="status" aria-live="polite">
            <i className={styles.statusDot} />
            {myTurn && targetPlayerUser ? `Sıra sende · ${targetPlayerUser.display_name} kullanıcısından kart çek` : "Hamle bekleniyor"}
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
          <div className={styles.players} style={{ gridTemplateColumns: '1fr', gap: '10px' }}>
            {players.map((p) => {
              const cardCount = game.hand_counts[p.id] ?? 0;
              const isTarget = p.id === targetPlayerId;
              const isMe = p.id === currentUserId;
              return (
                <div key={p.id} className={styles.player} style={{ 
                  border: isTarget && myTurn ? '1px solid #ff9eb1' : game.turn_user_id === p.id ? '1px solid #fff' : '',
                  opacity: cardCount === 0 && game.status === 'active' ? 0.5 : 1
                }}>
                  <strong>{p.display_name} {isMe && "(Sen)"}</strong>
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
              <div style={{ color: 'var(--muted)', fontSize: '11px' }}>Sırasını bekleyen oyuncu</div>
            )}
          </div>

          <div className={styles.center} style={{ gridTemplateColumns: '1fr' }}>
             <div className={styles.pile}>
                {myTurn && targetPlayerUser && (
                   <span className={styles.status} style={{ background: 'transparent', border: '0', fontSize: '12px', fontWeight: 'bold' }}>
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
               <div style={{ color: '#fff', fontSize: '14px', fontWeight: 'bold', marginBottom: '20px' }}>
                 Elindeki kartlar bitti, kurtuldun!
               </div>
            )}
          </div>

          <small className={styles.turnHint}>
            Otomatik olarak çiftler elden atılır. Elinde kart kalmayan oyundan çıkar. Papaz elde kalana kadar oyun devam eder.
          </small>
        </div>
      )}
    </section>
  );
}
