import { Link } from "@tanstack/react-router";
import { useListMyNotes } from "@/api/generated";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { NoteBadges } from "@/components/NoteBadges";
import { isUnauthorized } from "@/lib/error";

export function MyNotesPage() {
  const { data: notes, isLoading, error } = useListMyNotes({
    query: {
      staleTime: 0,
      gcTime: 0,
      refetchOnMount: "always",
    },
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">Loading your notes…</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          {isUnauthorized(error) ? (
            <p className="text-muted-foreground">
              Please{" "}
              <Link to="/login" className="underline">
                sign in
              </Link>{" "}
              to view your notes.
            </p>
          ) : (
            <p className="text-destructive">Failed to load notes.</p>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>My Notes</CardTitle>
        <CardDescription>Notes you have created.</CardDescription>
      </CardHeader>
      <CardContent>
        {!notes || notes.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            You haven't created any notes yet.
          </p>
        ) : (
          <ul className="space-y-2">
            {notes.map((note) => (
              <li key={note.id}>
                <Link
                  to="/notes/$noteId"
                  params={{ noteId: note.id }}
                  className="flex items-center justify-between rounded-md border p-3 hover:bg-muted transition-colors gap-3"
                >
                  <span className="text-sm min-w-0 flex-1">
                    {note.content_preview ? (
                      <span className="truncate block">
                        {note.content_preview}
                      </span>
                    ) : (
                      <span className="font-mono text-xs text-muted-foreground truncate block">
                        {note.id}
                      </span>
                    )}
                    <span className="text-xs text-muted-foreground block mt-0.5">
                      {new Date(note.created_at).toLocaleString()}
                    </span>
                  </span>
                  <div className="shrink-0">
                    <NoteBadges
                      burnAfterReading={note.burn_after_reading}
                      requiresPassword={note.requires_password}
                      expiresAt={note.expires_at}
                    />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
