import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { getNoteContent } from "@/api/generated";
import { isInvalidPassword } from "@/lib/error";

export function useNoteAccess(noteId: string) {
  const [password, setPassword] = useState("");
  const [accessResult, setAccessResult] = useState<
    { noteId: string; content: string } | null
  >(null);

  const mutation = useMutation({
    mutationFn: () => getNoteContent(noteId, { password: password || null }),
    onSuccess: (data) => {
      setAccessResult({ noteId, content: data.content });
    },
    onError: (err: unknown) => {
      if (isInvalidPassword(err)) {
        toast.error("Incorrect password.");
      } else {
        toast.error("Failed to access note.");
      }
    },
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  return {
    password,
    setPassword,
    content: accessResult?.noteId === noteId ? accessResult.content : null,
    submit,
    isPending: mutation.isPending,
  };
}
