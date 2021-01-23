const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

module.exports = withBundleAnalyzer({
  serverRuntimeConfig: {
    SERVER_URL: process.env.SERVER_URL || "http://localhost:8080",
  },
});
