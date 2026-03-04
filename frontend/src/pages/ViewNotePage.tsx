import { useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { useGetNoteMetadata } from "@/api/generated";
import type { NoteMetadataResponse } from "@/api/generated";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { NoteBadges } from "@/components/NoteBadges";
import {
  Lock,
  Clock,
  ArrowLeft,
  Trash2,
  Eye,
  Flame,
} from "lucide-react";
import { isNotFound, isExpired } from "@/lib/error";
import { useNoteAccess } from "@/hooks/useNoteAccess";
import { useNoteDelete } from "@/hooks/useNoteDelete";

function BackToCreateButton() {
  return (
    <Button variant="outline" asChild>
      <Link to="/">
        <ArrowLeft className="h-4 w-4 mr-1" />
        Create a New Note
      </Link>
    </Button>
  );
}

function NoteMetadataBadges({ metadata }: { metadata: NoteMetadataResponse }) {
  return (
    <NoteBadges
      burnAfterReading={metadata.burn_after_reading}
      requiresPassword={metadata.requires_password}
      expiresAt={metadata.expires_at}
      expiresPrefix="Expires"
    />
  );
}

function NoteDeletedView() {
  return (
    <Card>
      <CardContent className="py-12 text-center space-y-4">
        <p className="text-muted-foreground">This note has been deleted.</p>
        <BackToCreateButton />
      </CardContent>
    </Card>
  );
}

function NoteLoadingView() {
  return (
    <Card>
      <CardContent className="py-12 text-center">
        <p className="text-muted-foreground">Loading note\u2026</p>
      </CardContent>
    </Card>
  );
}

function NoteErrorView({ error }: { error: unknown }) {
  return (
    <Card>
      <CardContent className="py-12 text-center space-y-4">
        {isNotFound(error) ? (
          <p className="text-muted-foreground">Note not found.</p>
        ) : isExpired(error) ? (
          <p className="text-muted-foreground">This note has expired.</p>
        ) : (
          <p className="text-destructive">Failed to load note.</p>
        )}
        <BackToCreateButton />
      </CardContent>
    </Card>
  );
}

function NoteContentView({
  metadata,
  content,
  onDelete,
  onDeleteCancel,
  isDeleting,
  deleteConfirmPending,
}: {
  metadata: NoteMetadataResponse;
  content: string;
  onDelete: () => void;
  onDeleteCancel: () => void;
  isDeleting: boolean;
  deleteConfirmPending: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Note Content</CardTitle>
          <NoteMetadataBadges metadata={metadata} />
        </div>
        <CardDescription>
          Created {new Date(metadata.created_at).toLocaleString()}
        </CardDescription>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4">
        <pre className="whitespace-pre-wrap break-words font-mono text-sm bg-muted p-4 rounded-md max-h-[60vh] overflow-auto">
          {content}
        </pre>
      </CardContent>
      <Separator />
      <CardContent className="pt-4 space-y-4">
        <div className="flex justify-between">
          <BackToCreateButton />
          {metadata.is_owner && (
            <div className="flex items-center gap-2">
              {deleteConfirmPending && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onDeleteCancel}
                  disabled={isDeleting}
                >
                  Cancel
                </Button>
              )}
              <Button
                variant="destructive"
                size="sm"
                onClick={onDelete}
                disabled={isDeleting}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                {isDeleting
                  ? "Deleting…"
                  : deleteConfirmPending
                    ? "Confirm delete?"
                    : "Delete"}
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function NoteAccessForm({
  metadata,
  password,
  onPasswordChange,
  onSubmit,
  isPending,
}: {
  metadata: NoteMetadataResponse;
  password: string;
  onPasswordChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isPending: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {metadata.requires_password && !metadata.is_owner ? (
            <>
              <Lock className="h-5 w-5" />
              Password Required
            </>
          ) : (
            <>
              <Eye className="h-5 w-5" />
              View Note
            </>
          )}
        </CardTitle>
        <CardDescription>
          {metadata.requires_password && !metadata.is_owner
            ? "This note is password-protected. Enter the password to view its content."
            : "Click below to reveal the note content."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          {metadata.requires_password && !metadata.is_owner && (
            <div className="space-y-2">
              <Label htmlFor="access-password">Password</Label>
              <Input
                id="access-password"
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => onPasswordChange(e.target.value)}
                autoFocus
                required
              />
            </div>
          )}

          <div className="flex items-center gap-2">
            {metadata.burn_after_reading && (
              <Badge variant="destructive" className="text-xs">
                <Flame className="h-3 w-3 mr-1" />
                Will be deleted after reading
              </Badge>
            )}
            {metadata.expires_at && (
              <Badge variant="outline" className="text-xs">
                <Clock className="h-3 w-3 mr-1" />
                Expires {new Date(metadata.expires_at).toLocaleString()}
              </Badge>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={isPending}
          >
            {isPending
              ? "Unlocking\u2026"
              : metadata.requires_password && !metadata.is_owner
                ? "Unlock Note"
                : "View Note"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export function ViewNotePage() {
  const { noteId } = useParams({ from: "/notes/$noteId" });
  const [deletedNoteId, setDeletedNoteId] = useState<string | null>(null);
  const isDeleted = deletedNoteId === noteId;

  const {
    data: metadata,
    isLoading,
    error,
  } = useGetNoteMetadata(noteId, {
    query: {
      enabled: !!noteId && !isDeleted,
      staleTime: 0,
      gcTime: 0,
      refetchOnMount: "always",
    },
  });

  const { password, setPassword, content, submit, isPending: isAccessPending } =
    useNoteAccess(noteId);

  const { handleDelete, handleCancel, isPending: isDeleting, confirmPending } =
    useNoteDelete(noteId, () => setDeletedNoteId(noteId));

  if (isDeleted) return <NoteDeletedView />;
  if (isLoading) return <NoteLoadingView />;
  if (error) return <NoteErrorView error={error} />;
  if (!metadata) return null;

  if (content !== null) {
    return (
      <NoteContentView
        metadata={metadata}
        content={content}
        onDelete={handleDelete}
        onDeleteCancel={handleCancel}
        isDeleting={isDeleting}
        deleteConfirmPending={confirmPending}
      />
    );
  }

  return (
    <NoteAccessForm
      metadata={metadata}
      password={password}
      onPasswordChange={setPassword}
      onSubmit={submit}
      isPending={isAccessPending}
    />
  );
}
