import { defineConfig } from "orval";

export default defineConfig({
  api: {
    input: {
      target: "./openapi.json",
    },
    output: {
      target: "./src/api/generated.ts",
      client: "react-query",
      mode: "single",
      override: {
        mutator: {
          path: "./src/api/fetch-instance.ts",
          name: "customFetch",
        },
      },
    },
  },
});
