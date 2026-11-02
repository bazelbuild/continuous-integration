import { createProxyMiddleware } from "http-proxy-middleware";

const apiProxy = createProxyMiddleware({
  target: process.env.SERVER_URL || "http://localhost:8080",
  changeOrigin: true,
  pathRewrite: { [`^/api`]: "" },
});

export default function (req, res) {
  apiProxy(req, res);
}

export const config = { api: { externalResolver: true, bodyParser: false } };
