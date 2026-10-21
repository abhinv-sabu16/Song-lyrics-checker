export type MatchType = "exact" | "fuzzy";

export interface SearchRequest {
  query: string;
  limit?: number;
  min_score?: number;
}

export interface MatchResult {
  song_id: number;
  title: string;
  artist: string;
  matched_excerpt: string;
  similarity_score: number; // 0-100 text similarity, NOT a probability
  match_type: MatchType;
  start_time?: number | null;
  end_time?: number | null;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: MatchResult[];
  message?: string | null;
}