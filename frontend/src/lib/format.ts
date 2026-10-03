export const money = (value: number) =>
  new Intl.NumberFormat("en-CA", {
    style: "currency",
    currency: "CAD",
    maximumFractionDigits: 0,
  }).format(value);
export const number = (value: number) =>
  new Intl.NumberFormat("en-CA", { maximumFractionDigits: 1 }).format(value);
export const names: Record<string, string> = {
  reference: "Reference plan",
  candidate: "First proposal",
  revised: "Revised signals",
  capacity: "Extra lane",
};
export const optionName = (id: string, label?: string) =>
  names[id] ?? label ?? id;
export const settingName: Record<string, string> = {
  cross_guardrail_pct: "cross-street limit",
  budget_cad: "capital budget",
};
export const settingValue = (setting: string, value: number) =>
  setting === "budget_cad" ? money(value) : `${number(value)}%`;
export const kindNote: Record<string, string> = {
  signal: "Traffic control change at the hotspot junction (J2)",
  clearance: "Same plan; lane-blocking incidents cleared sooner",
  turn_lane: "Dedicated left-turn bay with a 10 s protected phase",
  turn_ban: "Left turns use the next junction (+36 s each)",
};
