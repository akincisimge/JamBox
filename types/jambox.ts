export type Track = {
  id: number;
  title: string;
  artist: string;
  addedBy: string;
  votes: number;
  art: string;
};

export type ChatMessage = {
  id: string;
  user_id: string;
  text: string;
  reactions: Record<string, string[]>;
  message_type: "text" | "chess_invite" | "pisti_invite" | "papaz_kacti_invite" | "tek_kart_invite" | "blof_invite" | "kelime_kapismasi_invite";
  payload: Record<string, string>;
  created_at: string;
  user: JamBoxUser;
};

export type SpotifyProfile = { id: string; display_name: string; images?: { url: string }[] };
export type SpotifyPlaylist = { id: string; name: string; images?: { url: string }[]; items?: { total: number }; tracks?: { total: number }; owner: { display_name: string } };
export type SpotifyTrack = { id: string; name: string; uri: string; duration_ms: number; artists: { name: string }[]; album: { name: string; images?: { url: string }[] } };
export type SpotifyPlaylistItem = { item?: SpotifyTrack | null; track?: SpotifyTrack | null };

export type JamBoxUser = {
  id: string;
  spotify_id: string;
  display_name: string;
  email: string | null;
  avatar_url: string | null;
  created_at: string;
};

export type JamBoxRoomMember = {
  user_id: string;
  is_owner: boolean;
  can_control_music: boolean;
  created_at: string;
  user: JamBoxUser;
};

export type JamBoxPlayback = {
  spotify_uri: string;
  spotify_track_id: string;
  queue_uris: string[];
  title: string;
  artist: string;
  album_image_url: string | null;
  duration_ms: number;
  position_ms: number;
  is_playing: boolean;
  version: number;
  changed_at: string;
};

export type ChessGame = {
  id: string;
  creator_id: string;
  white_user_id: string;
  black_user_id: string | null;
  status: "waiting" | "active" | "finished";
  fen: string;
  turn: "white" | "black";
  move_history: string[];
  legal_moves: string[];
  move_labels: string[];
  draw_offer_user_id: string | null;
  winner_user_id: string | null;
  result: string | null;
  created_at: string;
  updated_at: string;
  white_user: JamBoxUser;
  black_user: JamBoxUser | null;
};

export type PistiCard = {
  id: string;
  suit: "clubs" | "diamonds" | "hearts" | "spades";
  rank: "A" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "J" | "Q" | "K";
};

export type PistiGame = {
  id: string;
  creator_id: string;
  player_one_user_id: string;
  player_two_user_id: string | null;
  status: "waiting" | "active" | "finished";
  turn_user_id: string | null;
  hand: PistiCard[];
  hand_counts: Record<string, number>;
  captured_counts: Record<string, number>;
  pisti_counts: Record<string, number>;
  table: PistiCard[];
  deck_count: number;
  scores: Record<string, number>;
  winner_user_id: string | null;
  player_one_user: JamBoxUser;
  player_two_user: JamBoxUser | null;
};

export type PapazKactiCard = {
  id: string;
  suit: "clubs" | "diamonds" | "hearts" | "spades";
  rank: "A" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "J" | "Q" | "K";
};

export type PapazKactiGame = {
  id: string;
  creator_id: string;
  player_one_user_id: string;
  player_two_user_id: string | null;
  player_three_user_id: string | null;
  player_four_user_id: string | null;
  status: "waiting" | "active" | "finished";
  turn_user_id: string | null;
  loser_user_id: string | null;
  hand: PapazKactiCard[];
  hand_counts: Record<string, number>;
  player_one_user: JamBoxUser;
  player_two_user: JamBoxUser | null;
  player_three_user: JamBoxUser | null;
  player_four_user: JamBoxUser | null;
};

export type TekKartColor = "red" | "yellow" | "green" | "blue";

export type TekKartCardKind =
  | "number"
  | "skip"
  | "reverse"
  | "draw_two"
  | "wild"
  | "wild_draw_four";

export type TekKartCard = {
  id: string;
  kind: TekKartCardKind;
  color: TekKartColor | null;
  number: number | null;
};

export type TekKartPlayer = {
  user_id: string;
  player_order: number;
  hand_count: number;
  is_current_turn: boolean;
  is_creator: boolean;
  user: JamBoxUser;
};

export type TekKartGame = {
  id: string;
  creator_id: string;
  status: "waiting" | "active" | "finished";
  version: number;
  turn_user_id: string | null;
  winner_user_id: string | null;
  active_color: TekKartColor | null;
  direction: -1 | 1;
  draw_pile_count: number;
  top_card: TekKartCard | null;
  hand: TekKartCard[];
  playable_card_ids: string[];
  can_draw: boolean;
  can_call_tek_kart: boolean;
  called_tek_kart: boolean;
  players: TekKartPlayer[];
};

export type BlofDeclaredRank =
  | "A" | "2" | "3" | "4" | "5" | "6" | "7"
  | "8" | "9" | "10" | "J" | "Q" | "K";

export type BlofCard = {
  id: string;
  suit: "clubs" | "diamonds" | "hearts" | "spades";
  rank: BlofDeclaredRank;
};

export type BlofPlayer = {
  user_id: string;
  player_order: number;
  hand_count: number;
  is_current_turn: boolean;
  is_creator: boolean;
  user: JamBoxUser;
};

export type BlofChallengeResult = {
  truthful: boolean;
  challenger_user_id: string;
  challenged_user_id: string;
  pile_receiver_user_id: string;
  next_turn_user_id: string | null;
  revealed_cards: BlofCard[];
};

export type BlofGame = {
  id: string;
  creator_id: string;
  status: "waiting" | "active" | "finished";
  version: number;
  turn_user_id: string | null;
  pending_winner_user_id: string | null;
  winner_user_id: string | null;
  pile_count: number;
  last_play_count: number;
  last_declared_rank: BlofDeclaredRank | null;
  last_player_user_id: string | null;
  hand: BlofCard[];
  players: BlofPlayer[];
  last_result: BlofChallengeResult | null;
};

export type KelimeKapismasiDifficulty = "easy" | "medium" | "hard";

export type KelimeKapismasiStatus =
  | "waiting"
  | "countdown"
  | "playing"
  | "round_result"
  | "finished";

export type KelimeKapismasiPlayer = {
  user_id: string;
  player_order: number;
  current_word_count: number;
  stage_points: number;
  total_words: number;
  total_letters: number;
  is_creator: boolean;
  user: JamBoxUser;
};

export type KelimeKapismasiRoundPlayerResult = {
  user_id: string;
  words: string[];
  word_count: number;
  total_letters: number;
  longest_word: string | null;
  stage_points: number;
};

export type KelimeKapismasiRoundResult = {
  stage_number: number;
  difficulty: KelimeKapismasiDifficulty;
  winner_user_id: string | null;
  players: KelimeKapismasiRoundPlayerResult[];
};

export type KelimeKapismasiGame = {
  id: string;
  creator_id: string;
  status: KelimeKapismasiStatus;
  version: number;
  stage_number: number;
  stage_count: number;
  difficulty: KelimeKapismasiDifficulty | null;
  letters: string[];
  min_length: number;
  duration_seconds: number;
  phase_started_at: string | null;
  phase_ends_at: string | null;
  remaining_seconds: number;
  own_words: string[];
  own_word_count: number;
  players: KelimeKapismasiPlayer[];
  latest_result: KelimeKapismasiRoundResult | null;
  winner_user_id: string | null;
};

export type JamBoxRoom = {
  id: string;
  code: string;
  name: string;
  owner_id: string;
  is_active: boolean;
  created_at: string;
  members: JamBoxRoomMember[];
  playback: JamBoxPlayback | null;
  messages: ChatMessage[];
  chess_game: ChessGame | null;
};
