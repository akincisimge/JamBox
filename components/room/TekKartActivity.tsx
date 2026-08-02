"use client";

import { useMemo, useState } from "react";
import type {
  TekKartCard,
  TekKartColor,
  TekKartGame,
} from "../../types/jambox";
import styles from "./TekKartActivity.module.css";

const colorLabels: Record<TekKartColor, string> = {
  red: "Kırmızı",
  yellow: "Sarı",
  green: "Yeşil",
  blue: "Mavi",
};

const kindLabels: Record<TekKartCard["kind"], string> = {
  number: "",
  skip: "⊘",
  reverse: "↻",
  draw_two: "+2",
  wild: "★",
  wild_draw_four: "+4",
};

type Props = {
  game: TekKartGame | null;
  currentUserId: string;
  busy: boolean;
  error?: string;
  onCreate: () => void;
  onJoin: () => void;
  onStart: () => void;
  onPlay: (cardId: string, chosenColor?: TekKartColor) => void;
  onDraw: () => void;
  onCall: () => void;
  onRestart: () => void;
};

function cardText(card: TekKartCard) {
  return card.kind === "number" ? String(card.number) : kindLabels[card.kind];
}

function CardFace({
  card,
  activeColor,
  playable = false,
  disabled = false,
  onClick,
}: {
  card: TekKartCard;
  activeColor?: TekKartColor | null;
  playable?: boolean;
  disabled?: boolean;
  onClick?: () => void;
}) {
  const color = card.color ?? activeColor ?? "red";
  const wild = card.kind === "wild" || card.kind === "wild_draw_four";

  return (
    <button
      type="button"
      className={[
        styles.card,
        styles[color],
        wild ? styles.wild : "",
        playable ? styles.playable : "",
      ].filter(Boolean).join(" ")}
      disabled={disabled}
      onClick={onClick}
      aria-label={`${colorLabels[color]} ${cardText(card)} kartı`}
    >
      <span className={styles.corner}>{cardText(card)}</span>
      <span className={styles.cardCenter}>{cardText(card)}</span>
      <span className={styles.cornerBottom}>{cardText(card)}</span>
    </button>
  );
}

export function TekKartActivity({
  game,
  currentUserId,
  busy,
  error,
  onCreate,
  onJoin,
  onStart,
  onPlay,
  onDraw,
  onCall,
  onRestart,
}: Props) {
  const [chosenColor, setChosenColor] = useState<TekKartColor>("red");
  const isPlayer = Boolean(game?.players.some((player) => player.user_id === currentUserId));
  const isCreator = game?.creator_id === currentUserId;
  const myTurn = game?.status === "active" && game.turn_user_id === currentUserId;
  const winnerName = useMemo(
    () => game?.players.find((player) => player.user_id === game.winner_user_id)?.user.display_name,
    [game],
  );

  function play(card: TekKartCard) {
    const needsColor = card.kind === "wild" || card.kind === "wild_draw_four";
    onPlay(card.id, needsColor ? chosenColor : undefined);
  }

  return (
    <section className={styles.activity} aria-label="Tek Kart masası">
      <div className={styles.copy}>
        <span className={styles.eyebrow}>PLAY TOGETHER · TEK KART</span>
        <h2>
          {!game
            ? "Rengini eşleştir"
            : game.status === "waiting"
              ? "Oyuncular bekleniyor"
              : game.status === "active"
                ? "Tek Kart masası açık"
                : `${winnerName ?? "Bir oyuncu"} kazandı`}
        </h2>
        <p>
          Renk veya sembol eşleştir, özel kartlarla sırayı değiştir ve son kartından önce
          Tek Kart demeyi unutma. 2–4 kişilik.
        </p>

        {!game && (
          <button className={styles.primary} onClick={onCreate} disabled={busy}>
            🎨 Tek Kart masası aç
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
                <i className={styles.dot} /> Oyuncular bekleniyor ({game.players.length}/4)
              </div>
            )}
            {isCreator && game.players.length >= 2 && (
              <button className={styles.primary} onClick={onStart} disabled={busy}>
                Oyunu başlat
              </button>
            )}
          </div>
        )}

        {game?.status === "active" && (
          <div className={styles.status} role="status" aria-live="polite">
            <i className={styles.dot} />
            {myTurn ? "Sıra sende · Bir kart oyna veya çek" : "Rakibin hamlesi bekleniyor"}
          </div>
        )}

        {game && (
          <div className={styles.players}>
            {game.players.map((player) => (
              <div
                className={[styles.player, player.is_current_turn ? styles.playerActive : ""]
                  .filter(Boolean)
                  .join(" ")}
                key={player.user_id}
              >
                <strong>
                  {player.user.display_name}
                  {player.user_id === currentUserId ? " (Sen)" : ""}
                </strong>
                <small>{player.hand_count} kart</small>
              </div>
            ))}
          </div>
        )}

        {game?.called_tek_kart && (
          <div className={styles.called}>📣 Tek Kart çağrın hazır</div>
        )}
        {error && <p className={styles.error}>{error}</p>}

        {game?.status === "finished" && isCreator && (
          <button className={styles.primary} onClick={onRestart} disabled={busy}>
            ↻ Yeni oyun
          </button>
        )}
      </div>

      {game?.status === "active" && (
        <div className={styles.table}>
          <div className={styles.board}>
            <button
              type="button"
              className={styles.drawPile}
              onClick={onDraw}
              disabled={!myTurn || !game.can_draw || busy}
              aria-label={`Kart çek. Destede ${game.draw_pile_count} kart var.`}
            >
              <span>J</span>
              <small>{game.draw_pile_count}</small>
            </button>

            <div className={styles.topCard}>
              {game.top_card ? (
                <CardFace card={game.top_card} activeColor={game.active_color} disabled />
              ) : null}
              <small>
                Aktif renk: {game.active_color ? colorLabels[game.active_color] : "—"}
              </small>
            </div>
          </div>

          <div className={styles.colorPicker} aria-label="Renk seçimi">
            <span>Renk seçen kart için:</span>
            {Object.entries(colorLabels).map(([color, label]) => (
              <button
                type="button"
                key={color}
                className={[
                  styles.colorChoice,
                  styles[color as TekKartColor],
                  chosenColor === color ? styles.colorChoiceActive : "",
                ].filter(Boolean).join(" ")}
                onClick={() => setChosenColor(color as TekKartColor)}
                disabled={!myTurn || busy}
                aria-label={label}
                aria-pressed={chosenColor === color}
              />
            ))}
          </div>

          <div className={styles.hand} aria-label="Elindeki kartlar">
            {game.hand.map((card) => {
              const playable = game.playable_card_ids.includes(card.id);
              return (
                <CardFace
                  key={card.id}
                  card={card}
                  activeColor={game.active_color}
                  playable={playable}
                  disabled={!myTurn || !playable || busy}
                  onClick={() => play(card)}
                />
              );
            })}
          </div>

          <div className={styles.controls}>
            <button
              className={styles.callButton}
              onClick={onCall}
              disabled={!myTurn || !game.can_call_tek_kart || busy}
            >
              📣 Tek Kart!
            </button>
            <span>
              {game.direction === 1 ? "Saat yönünde" : "Saat yönünün tersinde"}
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
