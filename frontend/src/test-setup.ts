import "@testing-library/jest-dom";
import { TextDecoder, TextEncoder } from "util";

// JSDOM doesn't implement scrollTo
Element.prototype.scrollTo = jest.fn();

// JSDOM doesn't provide TextEncoder/TextDecoder (needed for SSE stream parsing)
if (typeof globalThis.TextDecoder === "undefined") {
  Object.assign(globalThis, { TextDecoder, TextEncoder });
}
