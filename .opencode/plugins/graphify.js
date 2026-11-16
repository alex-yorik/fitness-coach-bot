// graphify OpenCode plugin (canonical: V2 + path-scoped id)
// Injects a knowledge graph reminder before the first shell command of a
// session when the graph exists.
//
// IMPORTANT: keep the reminder string free of backticks and $(...) constructs.
// The hook prepends `echo "<reminder>" ; <cmd>` to the user's shell command;
// backticks inside the double-quoted echo trigger command substitution,
// which both corrupts tool output and silently executes the very graphify
// command we are only suggesting. Plain words render fine in opencode's TUI.
import { existsSync } from "fs";
import { join } from "path";

// ';' not '&&' — Windows PowerShell 5.1 rejects '&&' as a statement
// separator, breaking the first shell command of the session (#1646).
const REMINDER =
  'echo "[graphify] knowledge graph at graphify-out/. For focused questions, run graphify query with your question (scoped subgraph, usually much smaller than GRAPH_REPORT.md) instead of grepping raw files. Read GRAPH_REPORT.md only for broad architecture context." ; ';

// OpenCode deduplicates plugins by id: the loser is not loaded and is reported
// as a failed plugin ("Duplicate plugin ID"). A project and the global copy in
// ~/.opencode can each load, so the id carries this file's location and is
// unique per deployment path. The copies share one record of who was reminded
// (globalThis), so a command still gets one reminder.
const location = [...import.meta.url].reduce((hash, ch) => (Math.imul(hash, 31) + ch.charCodeAt(0)) >>> 0, 7);
const reminded = (globalThis.__graphifyReminded ??= new Set());

export default {
  id: `graphify-${location.toString(16)}`,
  name: "Graphify",
  async setup(ctx) {
    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== "shell" || typeof event.input?.command !== "string") return;
      if (reminded.has(event.sessionID)) return;
      if (!existsSync(join(ctx.location.directory, "graphify-out", "graph.json"))) return;

      event.input = { ...event.input, command: REMINDER + event.input.command };
      reminded.add(event.sessionID);
    });
  },
};
