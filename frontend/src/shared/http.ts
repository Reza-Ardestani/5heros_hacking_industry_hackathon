export async function request<T>(url: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, options);
  }
  catch {
    throw new Error("Cannot reach the API. Start it with `make api` (port 8008).");
  }
  const text = await response.text();
  let body;
  try {
    body = text ? JSON.parse(text) : {};
  }
  catch {
    body = {};
  }
  if (response.ok && !text) {
    throw new Error("API returned an empty response. Check the API connection.");
  }
  if (!response.ok && !text && response.status >= 500) {
    throw new Error("API is not responding. Start it with `make api` (port 8008) and retry.");
  }
  if (!response.ok) {
    const fields: Record<string, string> = {
      budget_cad: "Capital budget",
      cross_guardrail_pct: "Cross-street limit",
      main_vph: "Arterial arrivals",
      cross_vph: "Cross-street arrivals",
      duration_s: "Arrival window",
      flow_profile: "Imported flow profile",
    };
    const detail = Array.isArray(body.detail)
      ? body.detail
        .map((item: {
          loc: string[];
          msg: string;
        }) => {
          const field = item.loc.at(-1) ?? "Study inputs";
          return `${fields[field] ?? field.replaceAll("_", " ")}: ${item.msg.replace(/^Value error, /, "")}`;
        })
        .join(". ")
      : typeof body.detail === "string"
        ? body.detail
        : "Request failed. Check the API connection.";
    throw new Error(detail);
  }
  return body;
}
