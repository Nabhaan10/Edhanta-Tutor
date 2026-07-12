// Client-only entry point for Vercel static deployment.
// Uses React 18 createRoot instead of TanStack Start's hydrateRoot
// so the app works without an SSR server.
import { createRoot } from "react-dom/client";
import { RouterProvider } from "@tanstack/react-router";
import { getRouter } from "./router";
import "./styles.css";

const router = getRouter();

createRoot(document.getElementById("root")!).render(
  <RouterProvider router={router} />
);
