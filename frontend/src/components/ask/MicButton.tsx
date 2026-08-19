import { Mic, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";

interface MicButtonProps {
  onTranscript: (transcript: string) => void;
  disabled?: boolean;
}

export default function MicButton({ onTranscript, disabled }: MicButtonProps) {
  const { isSupported, isListening, error, start, stop } = useSpeechRecognition(onTranscript);

  if (!isSupported) return null;

  const label = isListening ? "Stop voice input" : "Start voice input";

  return (
    <div className="flex items-center gap-2">
      <Button
        type="button"
        variant="outline"
        size="icon"
        aria-label={label}
        aria-pressed={isListening}
        title={isListening ? "Listening - click to stop" : "Ask by voice (English)"}
        disabled={disabled}
        onClick={isListening ? stop : start}
        className={cn(isListening && "border-destructive/40 bg-destructive/10 text-destructive")}
      >
        {isListening ? <Square className="size-4 animate-pulse" /> : <Mic className="size-4" />}
      </Button>
      {error ? <span className="text-xs text-destructive">{error}</span> : null}
    </div>
  );
}
