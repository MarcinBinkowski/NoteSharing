import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";
import { useCreateNote } from "@/api/generated";
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
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Lock,
  Clock,
  Share2,
  Copy,
  ExternalLink,
  Flame,
} from "lucide-react";

const EXPIRY_OPTIONS = [
  { label: "No expiry", value: "none" },
  { label: "1 minute", value: "1" },
  { label: "5 minutes", value: "5" },
  { label: "15 minutes", value: "15" },
  { label: "1 hour", value: "60" },
  { label: "24 hours", value: "1440" },
  { label: "7 days", value: "10080" },
  { label: "30 days", value: "43200" },
] as const;

export function CreateNotePage() {
  const navigate = useNavigate();
  const [content, setContent] = useState("");
  const [password, setPassword] = useState("");
  const [expiresIn, setExpiresIn] = useState("none");
  const [burnAfterReading, setBurnAfterReading] = useState(false);
  const [createdId, setCreatedId] = useState<string | null>(null);

  const createdUrl = createdId
    ? `${window.location.origin}/notes/${createdId}`
    : null;

  const createNote = useCreateNote({
    mutation: {
      onSuccess: (data) => {
        setCreatedId(data.id);
        toast.success("Note created successfully!");
      },
      onError: () => {
        toast.error("Failed to create note. Please try again.");
      },
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) {
      toast.error("Note content cannot be empty.");
      return;
    }

    createNote.mutate({
      data: {
        content: content.trim(),
        password: password || undefined,
        expires_in_minutes:
          expiresIn && expiresIn !== "none" ? Number(expiresIn) : undefined,
        burn_after_reading: burnAfterReading,
      },
    });
  };

  const handleCopyLink = async () => {
    if (!createdUrl) return;
    try {
      await navigator.clipboard.writeText(createdUrl);
      toast.success("Link copied to clipboard!");
    } catch {
      toast.error("Could not copy — please copy the link manually.");
    }
  };

  const handleCreateAnother = () => {
    setContent("");
    setPassword("");
    setExpiresIn("none");
    setBurnAfterReading(false);
    setCreatedId(null);
  };

  if (createdUrl && createdId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5 text-green-600" />
            Note Created!
          </CardTitle>
          <CardDescription>
            Share this link with anyone you want to give access to:
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Input value={createdUrl} readOnly className="font-mono text-sm" />
            <Button
              variant="outline"
              size="icon"
              onClick={handleCopyLink}
              aria-label="Copy link"
              title="Copy link"
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>

          {password && (
            <p className="text-sm text-muted-foreground flex items-center gap-1">
              <Lock className="h-3.5 w-3.5" />
              This note is password-protected. Share the password separately.
            </p>
          )}

          {burnAfterReading && (
            <p className="text-sm text-muted-foreground flex items-center gap-1">
              <Flame className="h-3.5 w-3.5" />
              This note will be deleted after first read.
            </p>
          )}

          <div className="flex gap-2">
            <Button
              onClick={() =>
                navigate({
                  to: "/notes/$noteId",
                  params: { noteId: createdId },
                })
              }
            >
              <ExternalLink className="h-4 w-4 mr-1" />
              View Note
            </Button>
            <Button variant="outline" onClick={handleCreateAnother}>
              Create Another
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create a Note</CardTitle>
        <CardDescription>
          Share text securely with optional password protection and expiration.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="content">Note Content</Label>
            <Textarea
              id="content"
              placeholder="Type or paste your content here..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={8}
              maxLength={100_000}
              required
              className="font-mono text-sm resize-y"
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  e.currentTarget.form?.requestSubmit();
                }
              }}
            />
            <p className="text-xs text-muted-foreground text-right">
              {content.length.toLocaleString()} / 100,000
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5" />
              Password (optional)
            </Label>
            <Input
              id="password"
              type="password"
              placeholder="Leave empty for public access"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              maxLength={128}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="expiry" className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              Expiration
            </Label>
            <Select value={expiresIn} onValueChange={setExpiresIn}>
              <SelectTrigger id="expiry">
                <SelectValue placeholder="No expiry" />
              </SelectTrigger>
              <SelectContent>
                {EXPIRY_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Checkbox
              id="burn"
              checked={burnAfterReading}
              onCheckedChange={(v) => setBurnAfterReading(v === true)}
            />
            <Label
              htmlFor="burn"
              className="flex items-center gap-1.5 cursor-pointer"
            >
              <Flame className="h-3.5 w-3.5" />
              Burn after reading (delete after first view)
            </Label>
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={createNote.isPending || !content.trim()}
          >
            {createNote.isPending ? "Creating…" : "Create & Share Note"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
