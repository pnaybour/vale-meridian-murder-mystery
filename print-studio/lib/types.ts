export type Category =
  | 'clues'
  | 'badges'
  | 'evidence'
  | 'private'
  | 'seating'
  | 'stationery'
  | 'labels'
  | 'gm';
export type Item = {
  id: string;
  category: Category;
  title: string;
  content: string;
  character: string;
  description?: string;
  menu?: {
    starter: string;
    main: string;
    dessert: string;
    missing: boolean;
  };
  dietaryNote?: string;
  tableGuests?: { guest: string; character: string; dietaryNote: string; flags: string[] }[];
  hasFoodIntolerance?: boolean;
  tablePlan?: {
    date: string;
    venue: string;
    hosts: string;
    outline: number[][];
    rooms: Record<string, { name: string; short?: string; caption?: string | null }>;
    roomTables: Record<string, number[]>;
    tables: { number: number; room: string; x: number; y: number; guests: string[] }[];
  };
  roomPlan?: {
    date: string;
    venue: string;
    outline: number[][];
    rooms: Record<string, { name: string; short?: string; caption?: string | null }>;
    chairAllowance: number;
    tables: {
      number: number; room: string; x: number; y: number; diameter: number;
      seats: { guest: string; character: string; seat: number; angle: number }[];
    }[];
  };
  seatingPlan?: {
    date: string;
    venue: string;
    hosts: string;
    tables: {
      number: number;
      seats: { seat: number; guest: string; character: string }[];
    }[];
  };
  guest: string;
  table: number | null;
  round: number | null;
  quantity: number;
  private: boolean;
  source: string;
  revision: string;
  template: string;
  cue?: string;
  order?: number;
  proof?: boolean;
  /** Cross-table cards: the key of their pre-printed question note (not part of the revision). */
  noteKey?: string;
  /** Photographic evidence: the picture, its pixel size and how large it prints. */
  image?: string;
  imageWidth?: number;
  imageHeight?: number;
  photoSize?: 'photo' | 'document';
  /** Question notes: who the note goes to, and the card it belongs to. */
  toCharacter?: string;
  toTable?: number;
  clueId?: string;
};
export type Brand = {
  name: string;
  subtitle: string;
  color: string;
  inkSaver: boolean;
  cutMarks: boolean;
};
export const defaultBrand: Brand = {
  name: 'VALE MERIDIAN',
  subtitle: 'A NIGHT OF GLAMOUR & HIDDEN TRUTHS',
  color: '#732b40',
  inkSaver: false,
  cutMarks: true,
};
