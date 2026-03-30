import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const CLIENT_ID = process.env.DOMO_CLIENT_ID;
const CLIENT_SECRET = process.env.DOMO_CLIENT_SECRET;
if (!CLIENT_ID || !CLIENT_SECRET) {
  process.stderr.write("DOMO_CLIENT_ID and DOMO_CLIENT_SECRET are required\n");
  process.exit(1);
}

const API_BASE = "https://api.domo.com";

// OAuth token cache — one per scope
const tokenCache: Record<string, { token: string; expiry: number }> = {};

async function getAccessToken(scope: "data" | "dashboard" = "data"): Promise<string> {
  const cached = tokenCache[scope];
  if (cached && Date.now() < cached.expiry) return cached.token;

  const credentials = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString("base64");
  const res = await fetch(`${API_BASE}/oauth/token?grant_type=client_credentials&scope=${scope}`, {
    method: "GET",
    headers: { Authorization: `Basic ${credentials}` },
  });
  if (!res.ok) throw new Error(`OAuth failed (scope=${scope}) ${res.status}: ${await res.text()}`);
  const json = (await res.json()) as { access_token: string; expires_in: number };
  tokenCache[scope] = { token: json.access_token, expiry: Date.now() + (json.expires_in - 60) * 1000 };
  return json.access_token;
}

async function domoGet(path: string, scope: "data" | "dashboard" = "data"): Promise<unknown> {
  const token = await getAccessToken(scope);
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `bearer ${token}`, "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`Domo API ${res.status}: ${await res.text()}`);
  return res.json();
}

async function domoPost(path: string, body: unknown): Promise<unknown> {
  const token = await getAccessToken("data");
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { Authorization: `bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Domo API ${res.status}: ${await res.text()}`);
  return res.json();
}

const server = new McpServer({ name: "domo", version: "1.0.0" });

server.registerTool("list-datasets", {
  description: "List Domo datasets",
  inputSchema: { limit: z.number().optional().default(50), offset: z.number().optional().default(0) },
}, async ({ limit, offset }) => {
  const data = await domoGet(`/v1/datasets?limit=${limit}&offset=${offset}&fields=id,name,description,rows,columns,updatedAt`);
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
});

server.registerTool("get-dataset", {
  description: "Get metadata for a Domo dataset",
  inputSchema: { datasetId: z.string().describe("Domo dataset ID") },
}, async ({ datasetId }) => {
  const data = await domoGet(`/v1/datasets/${datasetId}`);
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
});

server.registerTool("export-dataset", {
  description: "Export rows from a Domo dataset as CSV",
  inputSchema: {
    datasetId: z.string().describe("Domo dataset ID"),
    limit: z.number().optional().default(500).describe("Max rows to return"),
  },
}, async ({ datasetId, limit }) => {
  const token = await getAccessToken();
  const res = await fetch(`${API_BASE}/v1/datasets/${datasetId}/data?type=csv&limit=${limit}`, {
    headers: { Authorization: `bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Domo API ${res.status}: ${await res.text()}`);
  const csv = await res.text();
  return { content: [{ type: "text", text: csv }] };
});

server.registerTool("query-dataset", {
  description: "Run a SQL SELECT query against a Domo dataset",
  inputSchema: {
    datasetId: z.string().describe("Domo dataset ID"),
    sql: z.string().describe("SQL SELECT query, e.g. SELECT * FROM table LIMIT 100"),
  },
}, async ({ datasetId, sql }) => {
  const data = await domoPost(`/v1/datasets/query/execute/${datasetId}`, { sql });
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
});

server.registerTool("search-datasets", {
  description: "Search Domo datasets by name keyword",
  inputSchema: { query: z.string().describe("Name keyword to search for") },
}, async ({ query }) => {
  const data = await domoGet(`/v1/datasets?q=${encodeURIComponent(query)}&limit=20&fields=id,name,description,rows,updatedAt`);
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
});

server.registerTool("get-page", {
  description: "Get metadata and card list for a Domo page (dashboard scope)",
  inputSchema: { pageId: z.string().describe("Domo page ID") },
}, async ({ pageId }) => {
  const data = await domoGet(`/v1/pages/${pageId}`, "dashboard");
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
});

server.registerTool("get-page-cards", {
  description: "List all cards on a Domo page (dashboard scope). Use for pages with discover_cards: true.",
  inputSchema: { pageId: z.string().describe("Domo page ID") },
}, async ({ pageId }) => {
  const data = await domoGet(`/v1/pages/${pageId}/cards`, "dashboard");
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
});

server.registerTool("get-card", {
  description: "Get metadata and current value for a Domo card/KPI (dashboard scope)",
  inputSchema: { cardId: z.string().describe("Domo card ID") },
}, async ({ cardId }) => {
  const data = await domoGet(`/v1/cards/${cardId}`, "dashboard");
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
});

const transport = new StdioServerTransport();
await server.connect(transport);
