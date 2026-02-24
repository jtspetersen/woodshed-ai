interface ExamplePromptsProps {
  onSelect: (prompt: string) => void;
}

const PROMPTS = [
  "Analyze the chord Dm7 for me",
  "What key is this progression in: Am, F, C, G?",
  "Suggest a jazzy chord to follow Dm7 -> G7",
  "I want something that sounds melancholy in E minor",
  "How do I play a Cmaj7 on guitar?",
  "What's a good substitution for a G7 chord?",
];

export default function ExamplePrompts({ onSelect }: ExamplePromptsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto px-4">
      {PROMPTS.map((prompt) => (
        <button
          key={prompt}
          onClick={() => onSelect(prompt)}
          className="text-left p-4 rounded-lg bg-bark-900 border border-bark-600
                     hover:border-amber-400/50 hover:bg-bark-800
                     transition-all duration-normal text-sm font-body text-bark-300
                     hover:text-amber-100"
          data-testid="example-prompt"
        >
          {prompt}
        </button>
      ))}
    </div>
  );
}
