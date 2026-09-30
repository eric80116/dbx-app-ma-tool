import { createFileRoute, Outlet } from "@tanstack/react-router";

// Layout for the /audiences subtree. The list lives in audiences.index.tsx and the
// detail in audiences.$id.tsx; this parent just renders the matched child.
export const Route = createFileRoute("/_sidebar/audiences")({
  component: () => <Outlet />,
});
