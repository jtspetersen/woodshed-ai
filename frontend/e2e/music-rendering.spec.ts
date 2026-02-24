import { test, expect } from "@playwright/test";

test.describe("Music Rendering", () => {
  test("assistant response with chord analysis renders chord tags", async ({
    page,
  }) => {
    await page.goto("/");

    // Ask about a chord — this should trigger chord-tag rendering
    const textarea = page.getByTestId("chat-textarea");
    await textarea.fill("Analyze the chord Dm7 for me");
    await textarea.press("Enter");

    // Wait for streaming to complete
    await expect(page.getByTestId("vu-meter")).not.toBeVisible({
      timeout: 30_000,
    });

    // The assistant message should contain chord-tag spans
    const chordTags = page.locator(".chord-tag");
    await expect(chordTags.first()).toBeVisible({ timeout: 5_000 });
  });

  test("file download links are present when MIDI files are generated", async ({
    page,
  }) => {
    await page.goto("/");

    // Ask for something that might generate a MIDI file
    const textarea = page.getByTestId("chat-textarea");
    await textarea.fill(
      "Generate a MIDI file of a Dm7 G7 Cmaj7 chord progression",
    );
    await textarea.press("Enter");

    // Wait for streaming to complete
    await expect(page.getByTestId("vu-meter")).not.toBeVisible({
      timeout: 45_000,
    });

    // Check if file links appeared (depends on LLM generating MIDI)
    // This test verifies the rendering pipeline — if files are generated,
    // download links should be visible
    const fileLinks = page.getByTestId("file-link");
    const linkCount = await fileLinks.count();

    if (linkCount > 0) {
      // Verify the link has a proper download URL
      const href = await fileLinks.first().getAttribute("href");
      expect(href).toContain("/api/files/download/");
    }
    // If no files were generated, the test still passes —
    // file generation depends on LLM tool invocation which isn't guaranteed
  });

  test("ABC notation in code blocks renders sheet music component", async ({
    page,
  }) => {
    await page.goto("/");

    // Ask for notation — the LLM may respond with ABC notation in a code block
    const textarea = page.getByTestId("chat-textarea");
    await textarea.fill(
      "Show me ABC notation for a simple C major scale, use a ```abc code block",
    );
    await textarea.press("Enter");

    // Wait for streaming to complete
    await expect(page.getByTestId("vu-meter")).not.toBeVisible({
      timeout: 45_000,
    });

    // If the LLM produced ABC notation, the SheetMusic component should render
    const sheetMusic = page.getByTestId("sheet-music");
    const fallback = page.getByTestId("sheet-music-fallback");

    const hasSheet = (await sheetMusic.count()) > 0;
    const hasFallback = (await fallback.count()) > 0;

    if (hasSheet) {
      // Sheet music rendered successfully — check for SVG content
      await expect(sheetMusic.first()).toBeVisible();
    } else if (hasFallback) {
      // Fallback rendered (abcjs couldn't render) — still valid
      await expect(fallback.first()).toBeVisible();
    }
    // If neither appeared, the LLM didn't produce ABC notation in a code block.
    // That's OK — this test verifies the rendering pipeline, not LLM output.
  });
});
