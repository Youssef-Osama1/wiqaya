import { Square, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { stripMarkdown } from "@/lib/format";

export default function SpeakButton({ text }: { text: string }) {
  const { isSupported, isSpeaking, speak, cancel } = useSpeechSynthesis();

  if (!isSupported) return null;

  const label = isSpeaking ? "Stop reading" : "Read recommendation aloud";

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      aria-label={label}
      aria-pressed={isSpeaking}
      title={label}
      onClick={isSpeaking ? cancel : () => speak(stripMarkdown(text))}
    >
      {isSpeaking ? <Square className="size-4 text-destructive" /> : <Volume2 className="size-4" />}
    </Button>
  );
}
