import { test, expect } from "@playwright/test";

test.describe("Chat", () => {
  test("page loads with header, status bar, and example prompts", async ({
    page,
  }) => {
    await page.goto("/");

    // Header elements
    await expect(page.getByTestId("chat-interface")).toBeVisible();
    await expect(page.getByText("New Chat")).toBeVisible();

    // Welcome state with example prompts
    await expect(page.getByText("Welcome to Woodshed AI")).toBeVisible();
    const prompts = page.getByTestId("example-prompt");
    await expect(prompts).toHaveCount(6);
  });

  test("clicking an example prompt sends message and gets response", async ({
    page,
  }) => {
    await page.goto("/");

    // Click the first example prompt
    const firstPrompt = page.getByTestId("example-prompt").first();
    const promptText = await firstPrompt.textContent();
    await firstPrompt.click();

    // Welcome should disappear, messages should appear
    await expect(page.getByText("Welcome to Woodshed AI")).not.toBeVisible();

    // User message should appear
    const userBubble = page.getByTestId("message-bubble").filter({
      has: page.getByText(promptText!),
    });
    await expect(userBubble).toBeVisible();

    // Wait for assistant response (streaming completes)
    await expect(
      page.getByTestId("message-bubble").nth(1),
    ).toBeVisible({ timeout: 30_000 });

    // VU meter should disappear when streaming is done
    await expect(page.getByTestId("vu-meter")).not.toBeVisible({
      timeout: 30_000,
    });

    // Assistant message should have content
    const assistantBubble = page
      .getByTestId("message-bubble")
      .nth(1)
      .locator("div");
    const content = await assistantBubble.first().textContent();
    expect(content!.length).toBeGreaterThan(0);
  });

  test("type message and press Enter to get streaming response", async ({
    page,
  }) => {
    await page.goto("/");

    const textarea = page.getByTestId("chat-textarea");
    await textarea.fill("What notes are in a C major chord?");
    await textarea.press("Enter");

    // Message should appear
    await expect(
      page.getByText("What notes are in a C major chord?"),
    ).toBeVisible();

    // Wait for streaming to complete
    await expect(page.getByTestId("vu-meter")).not.toBeVisible({
      timeout: 30_000,
    });

    // Should have 2 message bubbles (user + assistant)
    await expect(page.getByTestId("message-bubble")).toHaveCount(2);
  });

  test("creativity control is visible and selectable", async ({ page }) => {
    await page.goto("/");

    // Default is Balanced
    const balanced = page.getByRole("radio", { name: "Balanced" });
    await expect(balanced).toHaveAttribute("aria-checked", "true");

    // Click More Creative
    await page.getByRole("radio", { name: "More Creative" }).click();
    await expect(
      page.getByRole("radio", { name: "More Creative" }),
    ).toHaveAttribute("aria-checked", "true");
    await expect(balanced).toHaveAttribute("aria-checked", "false");
  });

  test("conversation reset clears messages", async ({ page }) => {
    await page.goto("/");

    // Send a message
    const textarea = page.getByTestId("chat-textarea");
    await textarea.fill("Hello");
    await textarea.press("Enter");

    // Wait for response
    await expect(page.getByTestId("vu-meter")).not.toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByTestId("message-bubble")).toHaveCount(2);

    // Click New Chat
    await page.getByText("New Chat").click();

    // Messages should be cleared, welcome should return
    await expect(page.getByText("Welcome to Woodshed AI")).toBeVisible();
    await expect(page.getByTestId("message-bubble")).toHaveCount(0);
  });
});
