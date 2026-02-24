import {
  isAbcNotation,
  isGuitarTab,
  extractMusicBlocks,
} from "../music-detection";

describe("isAbcNotation", () => {
  it("returns true for valid ABC with headers", () => {
    const abc = `X:1
T:Test Tune
M:4/4
K:C
CDEF GABc`;
    expect(isAbcNotation(abc)).toBe(true);
  });

  it("returns false for plain text", () => {
    expect(isAbcNotation("Hello world")).toBe(false);
  });

  it("returns false for text with only X: but no K:", () => {
    expect(isAbcNotation("X:1\nT:Title\nCDEF")).toBe(false);
  });

  it("returns true for minimal ABC (X + K)", () => {
    const abc = `X:1
K:Am
ABcd efga`;
    expect(isAbcNotation(abc)).toBe(true);
  });
});

describe("isGuitarTab", () => {
  it("returns true for standard guitar tab", () => {
    const tab = `e|---0---0---0---|
B|---1---1---1---|
G|---0---0---0---|
D|---2---2---2---|
A|---3---3---3---|
E|---------------|`;
    expect(isGuitarTab(tab)).toBe(true);
  });

  it("returns false for plain text", () => {
    expect(isGuitarTab("Just some regular text")).toBe(false);
  });

  it("returns false for too few lines", () => {
    expect(isGuitarTab("e|---0---|\nB|---1---|")).toBe(false);
  });

  it("returns true for tab without string names", () => {
    const tab = `|---0---0---0---|
|---1---1---1---|
|---0---0---0---|
|---2---2---2---|
|---3---3---3---|
|---------------|`;
    expect(isGuitarTab(tab)).toBe(true);
  });
});

describe("extractMusicBlocks", () => {
  it("extracts abc fenced code block", () => {
    const text = `Here is the notation:
\`\`\`abc
X:1
T:Test
K:C
CDEF
\`\`\`
That's it.`;
    const blocks = extractMusicBlocks(text);
    expect(blocks).toHaveLength(1);
    expect(blocks[0].type).toBe("abc");
    expect(blocks[0].content).toContain("X:1");
    expect(blocks[0].content).toContain("K:C");
  });

  it("extracts tab fenced code block", () => {
    const text = `\`\`\`tab
e|---0---|
B|---1---|
G|---0---|
D|---2---|
A|---3---|
E|-------|
\`\`\``;
    const blocks = extractMusicBlocks(text);
    expect(blocks).toHaveLength(1);
    expect(blocks[0].type).toBe("tab");
  });

  it("auto-detects abc in unlabeled code block", () => {
    const text = `\`\`\`
X:1
T:Auto Detect
M:4/4
K:G
GABc defg
\`\`\``;
    const blocks = extractMusicBlocks(text);
    expect(blocks).toHaveLength(1);
    expect(blocks[0].type).toBe("abc");
  });

  it("returns empty array for plain text with no code blocks", () => {
    const blocks = extractMusicBlocks("Just some text about music theory.");
    expect(blocks).toHaveLength(0);
  });

  it("extracts multiple blocks from mixed content", () => {
    const text = `Here's the notation:
\`\`\`abc
X:1
K:C
CDEF
\`\`\`
And here's the tab:
\`\`\`tab
e|---0---|
B|---1---|
G|---0---|
D|---2---|
A|---3---|
E|-------|
\`\`\``;
    const blocks = extractMusicBlocks(text);
    expect(blocks).toHaveLength(2);
    expect(blocks[0].type).toBe("abc");
    expect(blocks[1].type).toBe("tab");
  });

  it("includes correct start/end positions", () => {
    const prefix = "Before: ";
    const text = `${prefix}\`\`\`abc
X:1
K:C
CDEF
\`\`\``;
    const blocks = extractMusicBlocks(text);
    expect(blocks).toHaveLength(1);
    expect(blocks[0].start).toBe(prefix.length);
    expect(blocks[0].end).toBe(text.length);
  });
});
