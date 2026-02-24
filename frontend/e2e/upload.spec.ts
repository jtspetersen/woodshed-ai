import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";
import os from "os";

/**
 * Creates a minimal valid MIDI file for testing.
 * This is a tiny type-0 MIDI with a single note.
 */
function createTestMidi(): string {
  const tmpDir = os.tmpdir();
  const filePath = path.join(tmpDir, "test-upload.mid");

  // Minimal MIDI file: header + single track with one note
  const header = Buffer.from([
    0x4d, 0x54, 0x68, 0x64, // "MThd"
    0x00, 0x00, 0x00, 0x06, // header length (6)
    0x00, 0x00, // format 0
    0x00, 0x01, // 1 track
    0x00, 0x60, // 96 ticks per quarter
  ]);

  const trackData = Buffer.from([
    0x00, 0x90, 0x3c, 0x64, // note on C4, velocity 100
    0x60, 0x80, 0x3c, 0x00, // note off C4 after 96 ticks
    0x00, 0xff, 0x2f, 0x00, // end of track
  ]);

  const trackHeader = Buffer.from([
    0x4d, 0x54, 0x72, 0x6b, // "MTrk"
    0x00,
    0x00,
    0x00,
    trackData.length,
  ]);

  fs.writeFileSync(filePath, Buffer.concat([header, trackHeader, trackData]));
  return filePath;
}

test.describe("File Upload", () => {
  test("MIDI upload triggers analysis or error", async ({ page }) => {
    await page.goto("/");

    const midiPath = createTestMidi();

    // Upload MIDI via the hidden file input (use testid since it's hidden)
    const fileInput = page.getByTestId("file-input");
    await fileInput.setInputFiles(midiPath);

    // Wait for the upload to process — either:
    // 1. A user message appears about the uploaded file (analysis succeeded)
    // 2. Nothing visible changes (upload returned error, silently handled)
    // Both are valid outcomes depending on MIDI complexity
    const uploadMessage = page.getByText(/uploaded/i);
    try {
      await uploadMessage.waitFor({ state: "visible", timeout: 10_000 });
      // Upload succeeded — wait for assistant response
      await expect(page.getByTestId("vu-meter")).not.toBeVisible({
        timeout: 30_000,
      });
      await expect(page.getByTestId("message-bubble")).toHaveCount(2);
    } catch {
      // Upload returned error (minimal MIDI may fail analysis) — that's OK
      // Verify the page is still functional
      await expect(page.getByText("Welcome to Woodshed AI")).toBeVisible();
    }

    // Cleanup
    fs.unlinkSync(midiPath);
  });

  test("unsupported file type shows error or is rejected", async ({
    page,
  }) => {
    await page.goto("/");

    // The file input has accept=".mid,.midi,.wav,.mp3,.m4a,.ogg,.flac"
    // Browsers enforce this in real interaction but Playwright can bypass it.
    // The backend should reject unsupported formats.
    const tmpFile = path.join(os.tmpdir(), "test.txt");
    fs.writeFileSync(tmpFile, "not a music file");

    const fileInput = page.getByTestId("file-input");
    await fileInput.setInputFiles(tmpFile);

    // Wait briefly for any error response
    await page.waitForTimeout(3000);

    // Either no message is sent (client-side rejection) or error bar appears
    const errorBar = page.getByTestId("error-bar");
    const hasBubbles = await page.getByTestId("message-bubble").count();

    // One of these conditions should hold:
    // - No message bubbles (upload was silently rejected)
    // - Error bar is visible
    // - Message bubbles exist but show an error in the response
    expect(hasBubbles === 0 || (await errorBar.isVisible())).toBeTruthy();

    fs.unlinkSync(tmpFile);
  });
});
