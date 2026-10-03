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
