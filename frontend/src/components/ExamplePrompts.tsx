interface ExamplePromptsProps {
  onSelect: (prompt: string) => void;
}

const PROMPTS = [
  "What are the notes in a Dm7 chord?",
  "What key is this progression in: Am, F, C, G?",
  "I want to write something that sounds like a rainy afternoon",
  "Help me make this chorus more interesting: C, G, Am, F",
  "Suggest a jazzy chord to follow Dm7 -> G7",
  "I'm stuck on my bridge — the verse is in D minor",
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
