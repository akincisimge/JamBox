"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import type {
  KelimeKapismasiDifficulty,
  KelimeKapismasiGame,
} from "../../types/jambox";
import styles from "./KelimeKapismasiActivity.module.css";

type Props = {
  game: KelimeKapismasiGame | null;
  currentUserId: string;
  busy: boolean;
  error?: string;
  onCreate: () => void;
  onJoin: () => void;
  onStart: () => void;
  onSubmitWord: (word: string) => Promise<boolean>;
  onRestart: () => void;
  onRefresh: () => void;
};

const difficultyCopy: Record<
  KelimeKapismasiDifficulty,
  { label: string; icon: string }
> = {
  easy: { label: "Kolay", icon: "🌱" },
  medium: { label: "Orta", icon: "⚡" },
  hard: { label: "Zor", icon: "🔥" },
};

function playerName(game: KelimeKapismasiGame, userId: string | null) {
  if (!userId) return null;
  return game.players.find((player) => player.user_id === userId)?.user
    .display_name;
}

export function KelimeKapismasiActivity({
  game,
  currentUserId,
  busy,
  error,
  onCreate,
  onJoin,
  onStart,
  onSubmitWord,
  onRestart,
  onRefresh,
}: Props) {
  const [word, setWord] = useState("");
  const [clock, setClock] = useState(() => Date.now());

  useEffect(() => {
    if (!game || game.status === "waiting" || game.status === "finished") {
      return;
    }

    const timer = window.setInterval(() => setClock(Date.now()), 250);
    return () => window.clearInterval(timer);
  }, [game?.id, game?.status]);

  const remainingSeconds = useMemo(() => {
    if (!game?.phase_ends_at) return game?.remaining_seconds ?? 0;
    const difference = new Date(game.phase_ends_at).getTime() - clock;
    return Math.max(0, Math.ceil(difference / 1000));
  }, [clock, game?.phase_ends_at, game?.remaining_seconds]);

  useEffect(() => {
    if (
      !game ||
      game.status === "waiting" ||
      game.status === "finished" ||
      remainingSeconds > 0
    ) {
      return;
    }

    void onRefresh();
    const timer = window.setInterval(onRefresh, 1000);
    return () => window.clearInterval(timer);
  }, [game?.id, game?.stage_number, game?.status, onRefresh, remainingSeconds]);

  const isPlayer = Boolean(
    game?.players.some((player) => player.user_id === currentUserId),
  );
  const isCreator = game?.creator_id === currentUserId;
  const ownPlayer = game?.players.find(
    (player) => player.user_id === currentUserId,
  );
  const opponent = game?.players.find(
    (player) => player.user_id !== currentUserId,
  );
  const difficulty = game?.difficulty
    ? difficultyCopy[game.difficulty]
    : null;
  const winnerName = game
    ? playerName(game, game.winner_user_id)
    : null;
  const latestResult = game?.latest_result ?? null;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = word.trim();
    if (!value) return;
    const accepted = await onSubmitWord(value);
    if (accepted) setWord("");
  }

  return (
    <section className={styles.activity} aria-label="Kelime Kapışması">
      <header className={styles.hero}>
        <div>
          <span className={styles.eyebrow}>PLAY TOGETHER · KELİME KAPIŞMASI</span>
          <h2>Harfleri yakala, kelimeleri çoğalt</h2>
          <p>
            İki oyuncu aynı harflerle ve aynı sürede yarışır. Rakibin
            kelimeleri etap bitene kadar gizli kalır.
          </p>
        </div>
        {game && game.status !== "waiting" && (
          <div className={styles.stageBadge}>
            <span>{difficulty?.icon}</span>
            <strong>Etap {game.stage_number}/{game.stage_count}</strong>
            <small>{difficulty?.label}</small>
          </div>
        )}
      </header>

      {!game && (
        <div className={styles.intro}>
          <div className={styles.rules}>
            <article>
              <b>6 etap</b>
              <span>2 kolay · 2 orta · 2 zor</span>
            </article>
            <article>
              <b>Eş zamanlı</b>
              <span>İki oyuncuya aynı harfler gelir</span>
            </article>
            <article>
              <b>Gizli yarış</b>
              <span>Kelimeler etap bitince açılır</span>
            </article>
          </div>
          <button className={styles.primary} onClick={onCreate} disabled={busy}>
            🔤 Kelime Kapışması aç
          </button>
        </div>
      )}

      {game?.status === "waiting" && (
        <div className={styles.waitingCard}>
          <div className={styles.waitingIcon}>VS</div>
          <div>
            <span>İKİ KİŞİLİK DÜELLO</span>
            <h3>
              {game.players.length === 1
                ? "Rakip bekleniyor"
                : "İki oyuncu hazır"}
            </h3>
            <p>
              Oyun başladığında her etap için aynı harfler iki ekranda da
              aynı anda açılır.
            </p>
          </div>
          <div className={styles.waitingActions}>
            {!isPlayer && game.players.length < 2 && (
              <button className={styles.primary} onClick={onJoin} disabled={busy}>
                Düelloya katıl
              </button>
            )}
            {isCreator && game.players.length === 2 && (
              <button className={styles.primary} onClick={onStart} disabled={busy}>
                Oyunu başlat
              </button>
            )}
            {isPlayer && game.players.length === 1 && (
              <span className={styles.waitingText}>Rakibin odaya katılması bekleniyor…</span>
            )}
          </div>
        </div>
      )}

      {game && (
        <div className={styles.scoreboard}>
          {game.players.map((player) => (
            <article
              key={player.user_id}
              className={player.user_id === currentUserId ? styles.ownScore : ""}
            >
              <div>
                <strong>
                  {player.user.display_name}
                  {player.user_id === currentUserId ? " (Sen)" : ""}
                </strong>
                <small>{player.total_words} toplam kelime</small>
              </div>
              <b>{player.stage_points} puan</b>
            </article>
          ))}
        </div>
      )}

      {game && game.status !== "waiting" && (
        <div className={styles.stageTrack} aria-label="Etap ilerlemesi">
          {Array.from({ length: game.stage_count }, (_, index) => {
            const stage = index + 1;
            const level = index < 2 ? "easy" : index < 4 ? "medium" : "hard";
            return (
              <span
                key={stage}
                className={`${styles.stageDot} ${styles[level]}${
                  stage === game.stage_number ? ` ${styles.currentStage}` : ""
                }${stage < game.stage_number ? ` ${styles.completedStage}` : ""}`}
              >
                {stage}
              </span>
            );
          })}
        </div>
      )}

      {game?.status === "countdown" && (
        <div className={styles.countdown}>
          <span>SIRADAKİ ETAP</span>
          <strong>{remainingSeconds || "BAŞLA"}</strong>
          <p>
            {difficulty?.icon} {difficulty?.label} · En az {game.min_length} harfli kelimeler
          </p>
        </div>
      )}

      {game?.status === "playing" && (
        <div className={styles.arena}>
          <div className={styles.timerPanel}>
            <div>
              <span>KALAN SÜRE</span>
              <strong>{String(Math.floor(remainingSeconds / 60)).padStart(2, "0")}:{String(remainingSeconds % 60).padStart(2, "0")}</strong>
            </div>
            <div className={styles.rivalProgress}>
              <span>Rakip ilerlemesi</span>
              <b>{opponent?.current_word_count ?? 0} kelime</b>
              <small>Kelimeler gizli</small>
            </div>
          </div>

          <div className={styles.letters} aria-label="Bu etabın harfleri">
            {game.letters.map((letter, index) => (
              <span key={`${letter}-${index}`}>{letter.toLocaleUpperCase("tr-TR")}</span>
            ))}
          </div>

          <p className={styles.stageRule}>
            Yalnızca bu harfleri kullan · En az <b>{game.min_length} harf</b> · Her kelime bir kez
          </p>

          <form className={styles.wordForm} onSubmit={submit}>
            <input
              value={word}
              onChange={(event) => setWord(event.target.value)}
              placeholder="Kelime yaz ve Enter'a bas"
              maxLength={40}
              autoComplete="off"
              autoFocus
              disabled={busy || !isPlayer}
              aria-label="Bulduğun kelime"
            />
            <button className={styles.primary} disabled={busy || !word.trim() || !isPlayer}>
              Kelimeyi ekle
            </button>
          </form>

          <div className={styles.ownWords}>
            <header>
              <div>
                <span>SENİN KELİMELERİN</span>
                <strong>{game.own_word_count} geçerli kelime</strong>
              </div>
              <b>{ownPlayer?.current_word_count ?? 0}</b>
            </header>
            <div>
              {game.own_words.length ? (
                game.own_words.map((item) => <span key={item}>✓ {item}</span>)
              ) : (
                <p>İlk kelimeni yaz; rakibin bunları etap bitene kadar göremez.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {game?.status === "round_result" && latestResult && (
        <div className={styles.resultPanel}>
          <header>
            <span>ETAP {latestResult.stage_number} TAMAMLANDI</span>
            <h3>
              {latestResult.winner_user_id
                ? `${playerName(game, latestResult.winner_user_id) ?? "Bir oyuncu"} etabı kazandı`
                : "Etap berabere"}
            </h3>
            <p>Yeni etap {remainingSeconds} saniye içinde otomatik başlayacak.</p>
          </header>
          <div className={styles.resultColumns}>
            {latestResult.players.map((result) => (
              <article key={result.user_id}>
                <div className={styles.resultTitle}>
                  <strong>{playerName(game, result.user_id)}</strong>
                  <b>{result.word_count} kelime · +{result.stage_points} puan</b>
                </div>
                <div className={styles.resultWords}>
                  {result.words.length ? (
                    result.words.map((item) => <span key={item}>{item}</span>)
                  ) : (
                    <em>Geçerli kelime bulunamadı</em>
                  )}
                </div>
              </article>
            ))}
          </div>
        </div>
      )}

      {game?.status === "finished" && (
        <div className={styles.finished}>
          <span>🏆 KARŞILAŞMA TAMAMLANDI</span>
          <h3>{winnerName ? `${winnerName} kazandı!` : "Karşılaşma berabere!"}</h3>
          <div className={styles.finalScores}>
            {game.players.map((player) => (
              <article key={player.user_id}>
                <strong>{player.user.display_name}</strong>
                <b>{player.stage_points} puan</b>
                <small>{player.total_words} kelime · {player.total_letters} harf</small>
              </article>
            ))}
          </div>
          {isCreator && (
            <button className={styles.primary} onClick={onRestart} disabled={busy}>
              ↻ Aynı rakiple rövanş
            </button>
          )}
        </div>
      )}

      {error && <p className={styles.error}>{error}</p>}
    </section>
  );
}
