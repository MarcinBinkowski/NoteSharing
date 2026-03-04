import { Badge } from "@/components/ui/badge";
import { Clock, Flame, Lock } from "lucide-react";

interface NoteBadgesProps {
  burnAfterReading: boolean;
  requiresPassword: boolean;
  expiresAt: string | null;
  expiresPrefix?: string;
}

export function NoteBadges({
  burnAfterReading,
  requiresPassword,
  expiresAt,
  expiresPrefix,
}: NoteBadgesProps) {
  return (
    <div className="flex items-center gap-2">
      {burnAfterReading && (
        <Badge variant="destructive">
          <Flame className="h-3 w-3 mr-1" />
          Burn
        </Badge>
      )}
      {requiresPassword && (
        <Badge variant="secondary">
          <Lock className="h-3 w-3 mr-1" />
          Protected
        </Badge>
      )}
      {expiresAt && (
        <Badge variant="outline">
          <Clock className="h-3 w-3 mr-1" />
          {expiresPrefix ? `${expiresPrefix} ` : ""}
          {new Date(expiresAt).toLocaleString()}
        </Badge>
      )}
    </div>
  );
}
