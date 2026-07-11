// Generates a static dist/client/index.html after the Vite build.
// TanStack Start (SSR mode) does not create a static index.html —
// this script fills that gap so the app can be served as a SPA on Vercel.

import { readdirSync, writeFileSync } from "fs";

const assetsDir = "dist/client/assets";
const files = readdirSync(assetsDir);

// CSS stylesheets (exclude font files)
const cssFiles = files.filter(
  (f) =>
    f.endsWith(".css") &&
    !f.match(/\.(woff2?|ttf|eot)$/)
);

// JS entry point — Vite names the main bundle "index-<hash>.js"
const entryJs = files.find((f) => f.startsWith("index-") && f.endsWith(".js"));

if (!entryJs) {
  console.error("Could not find index-*.js in", assetsDir);
  process.exit(1);
}

const html = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Edhanta Tutor</title>
    <meta name="description" content="AI-powered tutor for Class 9 & 10 students" />
    ${cssFiles.map((f) => `<link rel="stylesheet" href="/assets/${f}" />`).join("\n    ")}
  </head>
  <body>
    <script type="module" src="/assets/${entryJs}"></script>
  </body>
</html>`;

writeFileSync("dist/client/index.html", html);
console.log(`Generated dist/client/index.html (entry: ${entryJs})`);
console.log(`Linked CSS: ${cssFiles.join(", ")}`);
