import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "./api";

afterEach(() => vi.unstubAllGlobals());

describe("job API client", () => {
  it("sends an authenticated job submission", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: 1, name: "example", status: "queued" }), { status: 201 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await api.createJob({ name: "example" }, "test-token");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/jobs",
      expect.objectContaining({
        method: "POST",
        headers: expect.any(Headers),
      }),
    );
    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers.get("Authorization")).toBe("Bearer test-token");
  });

  it("surfaces the API error message", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(
      new Response(JSON.stringify({ error: { message: "Invalid token" } }), { status: 401 }),
    )));

    await expect(api.listJobs("bad-token")).rejects.toThrow("Invalid token");
    await expect(api.listJobs("bad-token")).rejects.toMatchObject({ status: 401 });
  });
});
