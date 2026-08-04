"use client";

import { useMemo, useState } from "react";
import type {
  BlofCard,
  BlofDeclaredRank,
  BlofGame,
} from "../../types/jambox";
import styles from "./BlofActivity.module.css";

const ranks: BlofDeclaredRank[] = [
  "A", "2", "3", "4", "5", "6", "7",
  "8", "9", "10", "J", "Q", "K",
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
  const [declaredRank, setDeclaredRank] =
    useState<BlofDeclaredRank>("A");

  const isPlayer = Boolean(
    game?.players.some((player) => player.user_id === currentUserId),
  );
  const isCreator = game?.creator_id === currentUserId;
  const myTurn =
    game?.turn_user_id === currentUserId &&
    game.status === "active";
  const canChallenge = Boolean(myTurn && game?.last_player_user_id);
  const mustResolveWinner = Boolean(
    myTurn && game?.pending_winner_user_id,
  );

  const winnerName = useMemo(
    () =>
      game?.players.find(
        (player) => player.user_id === game.winner_user_id,
      )?.user.display_name,
    [game],
  );

  const turnPlayerName = useMemo(
    () =>
      game?.players.find(
        (player) => player.user_id === game.turn_user_id,
      )?.user.display_name,
    [game],
  );

  const lastPlayerName = useMemo(
    () =>
      game?.players.find(
        (player) => player.user_id === game.last_player_user_id,
      )?.user.display_name,
    [game],
  );

  const pendingWinnerName = useMemo(
    () =>
      game?.players.find(
        (player) => player.user_id === game.pending_winner_user_id,
      )?.user.display_name,
    [game],
  );

  const revealedCards = game?.last_result?.revealed_cards
    .map((card) => `${card.rank}${suitSymbols[card.suit]}`)
    .join(", ");

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
      ? `İlan doğru çıktı. Ortadaki kartları ${
          game.players.find(
            (player) =>
              player.user_id ===
              game.last_result?.pile_receiver_user_id,
          )?.user.display_name ?? "itiraz eden oyuncu"
        } aldı.`
      : `Blöf yakalandı. Ortadaki kartları ${
          game.players.find(
            (player) =>
              player.user_id ===
              game.last_result?.pile_receiver_user_id,
          )?.user.display_name ?? "kartları oynayan oyuncu"
        } aldı.`
    : null;

  return (
    <section className={styles.activity} aria-label="Blöf masası">
      <div className={styles.copy}>
        <span className={styles.eyebrow}>
          PLAY TOGETHER · BLÖF
        </span>

        <h2>
          {!game
            ? "Yalanını iyi sakla"
            : game.status === "waiting"
              ? "Oyuncular bekleniyor"
              : game.status === "active"
                ? "Blöf masası açık"
                : `${winnerName ?? "Bir oyuncu"} kazandı`}
        </h2>

        <p>
          Kartlarını kapalı oyna, istediğin değeri ilan et ve
          rakibinin doğru söyleyip söylemediğine karar ver.
          2–4 kişilik.
        </p>

        <div className={styles.rules}>
          <strong>Nasıl oynanır?</strong>
          <div>
            <span>1</span>
            <p>Elinden bir veya birkaç kart seç.</p>
          </div>
          <div>
            <span>2</span>
            <p>Gerçek kartından bağımsız bir değer ilan edebilirsin.</p>
          </div>
          <div>
            <span>3</span>
            <p>Rakip inanmazsa “Blöf De” diyerek kartlarını açtırır.</p>
          </div>
        </div>

        {!game && (
          <button
            className={styles.primary}
            onClick={onCreate}
            disabled={busy}
          >
            🎭 Blöf masası aç
          </button>
        )}

        {game?.status === "waiting" && (
          <div className={styles.waitingActions}>
            {!isPlayer && (
              <button
                className={styles.primary}
                onClick={onJoin}
                disabled={busy || game.players.length >= 4}
              >
                Masaya katıl ({game.players.length}/4)
              </button>
            )}

            {isPlayer && (
              <div className={styles.status}>
                <i className={styles.dot} />
                Oyuncular bekleniyor ({game.players.length}/4)
              </div>
            )}

            {isCreator && game.players.length >= 2 && (
              <button
                className={styles.primary}
                onClick={onStart}
                disabled={busy}
              >
                Oyunu başlat
              </button>
            )}
          </div>
        )}

        {game?.status === "active" && (
          <div
            className={`${styles.turnNotice}${
              myTurn ? ` ${styles.turnNoticeActive}` : ""
            }`}
            role="status"
          >
            <span className={styles.turnIcon}>
              {myTurn ? "👉" : "⏳"}
            </span>
            <div>
              <strong>
                {myTurn
                  ? "Şimdi sıra sende"
                  : `Sıra ${turnPlayerName ?? "diğer oyuncuda"}`}
              </strong>
              <p>
                {myTurn
                  ? mustResolveWinner
                    ? `${pendingWinnerName ?? "Rakibin"} son kartlarını oynadı. Blöf diyebilir veya son hamleyi kabul edebilirsin.`
                    : canChallenge
                      ? "İlana inanmıyorsan Blöf De. İnanıyorsan kendi kapalı kartlarını oynayıp yeni bir ilan yap."
                      : "Kartlarını seç, bir değer ilan et ve kapalı olarak oyna."
                  : "Rakibin hamlesini yaparken kendi kartlarını hazırlayabilirsin."}
              </p>
            </div>
          </div>
        )}

        {game && (
          <div className={styles.players}>
            {game.players.map((player) => (
              <div
                className={`${styles.player}${
                  player.is_current_turn
                    ? ` ${styles.playerActive}`
                    : ""
                }`}
                key={player.user_id}
              >
                <div>
                  <strong>
                    {player.user.display_name}
                    {player.user_id === currentUserId
                      ? " (Sen)"
                      : ""}
                  </strong>
                  {player.is_current_turn && (
                    <em>Sıra bu oyuncuda</em>
                  )}
                </div>
                <small>
                  {player.hand_count} kart · Oyuncu{" "}
                  {player.player_order + 1}
                </small>
              </div>
            ))}
          </div>
        )}

        {resultText && (
          <div className={styles.result}>
            <strong>{resultText}</strong>
            {revealedCards && (
              <span>Açılan kartlar: {revealedCards}</span>
            )}
          </div>
        )}

        {error && <p className={styles.error}>{error}</p>}

        {game?.status === "finished" && isCreator && (
          <button
            className={styles.primary}
            onClick={onRestart}
            disabled={busy}
          >
            ↻ Yeni oyun
          </button>
        )}
      </div>

      {game?.status === "active" && (
        <div className={styles.table}>
          <div className={styles.center}>
            {game.last_player_user_id &&
              game.last_declared_rank && (
                <div className={styles.declaration}>
                  <span>SON İLAN</span>
                  <strong>
                    {lastPlayerName ?? "Bir oyuncu"} kapalı{" "}
                    {game.last_play_count} kart oynadı
                  </strong>
                  <b>“{game.last_declared_rank}” ilan etti</b>
                  <p>
                    Gerçek kartları yalnızca Blöf denildiğinde
                    açılır.
                  </p>
                </div>
              )}

            <div
              className={styles.pile}
              aria-label={`Ortada ${game.pile_count} kart var`}
            >
              {game.pile_count > 0 ? (
                <>
                  <span className={styles.back} />
                  <span className={styles.back} />
                  <span className={styles.back} />
                </>
              ) : (
                <span className={styles.emptyPile}>
                  İlk kartları sen oyna
                </span>
              )}
            </div>

            <div className={styles.lastPlay}>
              <span>
                Ortada <b>{game.pile_count}</b> kart
              </span>
              <span>
                Son ilan{" "}
                <b>{game.last_declared_rank ?? "Henüz yok"}</b>
              </span>
              <span>
                Son hamle <b>{game.last_play_count || 0}</b> kart
              </span>
            </div>
          </div>

          <div className={styles.handSection}>
            <div className={styles.handHeading}>
              <div>
                <span>ELİNDEKİ KARTLAR</span>
                <strong>
                  {selectedCards.length
                    ? `${selectedCards.length} kart seçtin`
                    : "Oynamak istediğin kartlara dokun"}
                </strong>
              </div>
              <small>
                Kartların rakiplere kapalı görünür.
              </small>
            </div>

            <div className={styles.hand} aria-label="Elindeki kartlar">
              {game.hand.map((card) => {
                const selected = selectedCards.includes(card.id);

                return (
                  <button
                    type="button"
                    key={card.id}
                    className={`${styles.card}${
                      selected ? ` ${styles.cardSelected}` : ""
                    }${
                      redSuits.has(card.suit)
                        ? ` ${styles.red}`
                        : ""
                    }`}
                    onClick={() => toggleCard(card.id)}
                    disabled={!myTurn || mustResolveWinner || busy}
                    aria-pressed={selected}
                  >
                    <span className={styles.rank}>{card.rank}</span>
                    <span className={styles.suit}>
                      {suitSymbols[card.suit]}
                    </span>
                    {selected && (
                      <span className={styles.selectedMark}>✓</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          <div className={styles.actionArea}>
            {myTurn && !mustResolveWinner && (
              <div className={styles.playPanel}>
                <label htmlFor="blof-declared-rank">
                  Hangi değeri ilan edeceksin?
                </label>
                <p>
                  Seçtiğin kartların gerçekten bu değerde olması
                  gerekmez.
                </p>

                <div className={styles.controls}>
                  <select
                    id="blof-declared-rank"
                    value={declaredRank}
                    onChange={(event) =>
                      setDeclaredRank(
                        event.target.value as BlofDeclaredRank,
                      )
                    }
                    disabled={busy}
                    aria-label="İlan edilen kart değeri"
                  >
                    {ranks.map((rank) => (
                      <option key={rank} value={rank}>
                        {rank} ilan et
                      </option>
                    ))}
                  </select>

                  <button
                    className={styles.primary}
                    onClick={submitPlay}
                    disabled={busy || selectedCards.length === 0}
                  >
                    Kapalı Oyna ve {declaredRank} İlan Et
                    {selectedCards.length > 0
                      ? ` (${selectedCards.length} kart)`
                      : ""}
                  </button>
                </div>
              </div>
            )}

            {canChallenge && (
              <div className={styles.decisionPanel}>
                <div>
                  <span>İLANA İNANIYOR MUSUN?</span>
                  <strong>
                    {lastPlayerName ?? "Rakip"}: “
                    {game.last_declared_rank}”
                  </strong>
                  <p>
                    İnanmıyorsan kartları açtır. İnanıyorsan
                    yukarıdan kendi kartlarını oynayarak devam et.
                  </p>
                </div>

                <button
                  className={styles.danger}
                  onClick={onCall}
                  disabled={busy}
                >
                  🎭 Blöf De · Kartları Aç
                </button>
              </div>
            )}

            {mustResolveWinner && (
              <div className={styles.finalDecision}>
                <div>
                  <span>SON HAMLE KARARI</span>
                  <strong>
                    {pendingWinnerName ?? "Rakip"} elindeki
                    kartları bitirdi
                  </strong>
                  <p>
                    Son ilanın yanlış olduğunu düşünüyorsan Blöf De.
                    Doğru olduğuna inanıyorsan oyunu bitir.
                  </p>
                </div>

                <div className={styles.finalButtons}>
                  <button
                    className={styles.danger}
                    onClick={onCall}
                    disabled={busy}
                  >
                    🎭 Blöf De · Kartları Aç
                  </button>
                  <button
                    className={styles.secondary}
                    onClick={onAccept}
                    disabled={busy}
                  >
                    ✓ Son Hamleyi Kabul Et
                  </button>
                </div>
              </div>
            )}

            {!myTurn && (
              <div className={styles.waitingTurn}>
                <span>⏳</span>
                <div>
                  <strong>Rakibin hamlesi bekleniyor</strong>
                  <p>
                    Hamle yapıldığında son ilan burada otomatik
                    olarak görünecek.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
