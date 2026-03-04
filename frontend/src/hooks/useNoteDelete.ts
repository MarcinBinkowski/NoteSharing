import { useState } from "react";
import { toast } from "sonner";
import { useDeleteNote } from "@/api/generated";

export function useNoteDelete(noteId: string, onDeleted: () => void) {
  const [confirmPending, setConfirmPending] = useState(false);

  const mutation = useDeleteNote({
    mutation: {
      onSuccess: () => {
        onDeleted();
        toast.success("Note deleted.");
      },
      onError: () => {
        toast.error("Failed to delete note.");
        setConfirmPending(false);
      },
    },
  });

  const handleDelete = () => {
    if (!confirmPending) {
      setConfirmPending(true);
      return;
    }
    setConfirmPending(false);
    mutation.mutate({ noteId });
  };

  const handleCancel = () => {
    setConfirmPending(false);
  };

  return {
    handleDelete,
    handleCancel,
    isPending: mutation.isPending,
    confirmPending,
  };
}
