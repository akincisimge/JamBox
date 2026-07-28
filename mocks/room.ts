import type { ChatMessage, Track } from "../types/jambox";

export const initialQueue: Track[] = [
  {
    id: 1,
    title: "City Lights",
    artist: "Luna Park",
    addedBy: "Maya",
    votes: 12,
    art: "sunset",
  },
  {
    id: 2,
    title: "Ocean Eyes",
    artist: "Hollow Cove",
    addedBy: "Alex",
    votes: 9,
    art: "ocean",
  },
  {
    id: 3,
    title: "Golden Hour",
    artist: "Wildlight",
    addedBy: "Jordan",
    votes: 7,
    art: "gold",
  },
];

export const initialMessages: ChatMessage[] = [
  {
    name: "Maya",
    text: "This one is perfect ✨",
    color: "coral",
  },
  {
    name: "Alex",
    text: "Turn it up!",
    color: "purple",
  },
];

export const demoListeners = [
  ["SA", "Simge", "Host", "purple"],
  ["MY", "Maya", "Listening", "coral"],
  ["AL", "Alex", "Listening", "blue"],
  ["JR", "Jordan", "Listening", "cream"],
] as const;
