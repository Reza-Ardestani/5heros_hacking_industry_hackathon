export type View = "problem" | "study" | "compare" | "intersections" | "evidence";
export type ChatArea = {
  lat: number;
  lon: number;
  radius_m?: number;
  label?: string;
};
export type ChatAction = {
  type: "navigate";
  view: View;
  step?: number;
  intersection?: string;
  quadrant?: string;
  tab?: "detail" | "mcp-info-ml";
  prediction?: Record<string, string | number | null>;
  area?: ChatArea;
} | {
  type: "study";
  intersection: string;
};
export type ExplorerCommand = Omit<Extract<ChatAction, {
  type: "navigate";
}>, "type" | "view" | "step"> & {
  nonce: number;
};
