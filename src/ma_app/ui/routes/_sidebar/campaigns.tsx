import { createFileRoute, Outlet } from "@tanstack/react-router";

// Layout for the /campaigns subtree. The list lives in campaigns.index.tsx, the wizard
// in campaigns.new.tsx and the detail in campaigns.$id.tsx; this parent renders the child.
export const Route = createFileRoute("/_sidebar/campaigns")({
  component: () => <Outlet />,
});
