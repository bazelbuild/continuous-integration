const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

const serverUrl = process.env.SERVER_URL || "http://localhost:8080"

module.exports = withBundleAnalyzer({
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: serverUrl + "/:path*",
      },
    ];
  },
});
