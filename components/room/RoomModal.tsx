import type { FormEvent } from "react";
import { Icon } from "../ui/Icon";

type RoomModalProps = {
  mode: "create" | "join";
  roomName: string;
  roomCode: string;
  error: string;
  isSubmitting: boolean;
  onRoomNameChange: (value: string) => void;
  onRoomCodeChange: (value: string) => void;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function RoomModal({
  mode,
  roomName,
  roomCode,
  error,
  isSubmitting,
  onRoomNameChange,
  onRoomCodeChange,
  onClose,
  onSubmit,
}: RoomModalProps) {
  const isCreating = mode === "create";

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={onClose}
    >
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose} aria-label="Close">
          <Icon name="close" />
        </button>

        <span className="modal-icon">
          <Icon name={isCreating ? "plus" : "hash"} size={28} />
        </span>

        <p>{isCreating ? "START A NEW VIBE" : "STEP INTO THE ROOM"}</p>
        <h2 id="modal-title">
          {isCreating ? "Name your room" : "Enter the room code"}
        </h2>

        <form onSubmit={onSubmit}>
          <label>
            {isCreating ? "Room name" : "Invite code"}
            <input
              autoFocus
              value={isCreating ? roomName : roomCode}
              onChange={(event) =>
                isCreating
                  ? onRoomNameChange(event.target.value)
                  : onRoomCodeChange(event.target.value.toUpperCase())
              }
              required
            />
          </label>

          <button
            className="primary-button"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "Connecting…"
              : isCreating
                ? "Create room"
                : "Join room"}
            <Icon name="arrow" />
          </button>

          {error && (
            <p className="modal-error" role="alert">
              {error}
            </p>
          )}
        </form>

        <small>Share the room code with the people you want to invite.</small>
      </div>
    </div>
  );
}
