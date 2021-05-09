const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

module.exports = withBundleAnalyzer({
  future: {
    webpack5: true,
  },
  serverRuntimeConfig: {
    SERVER_URL: process.env.SERVER_URL || "http://localhost:8080",
  },
  async redirects() {
    return [
      {
        source: "/",
        destination: "/bazelbuild/bazel",
        permanent: false,
      },
    ];
  },
});
