import getConfig from "next/config";
import { createProxyMiddleware } from "http-proxy-middleware";

const { serverRuntimeConfig } = getConfig();

const apiProxy = createProxyMiddleware({
  target: serverRuntimeConfig.SERVER_URL,
  changeOrigin: true,
  pathRewrite: { [`^/api`]: "" },
});

export default function (req, res) {
  apiProxy(req, res);
}

export const config = { api: { externalResolver: true, bodyParser: false } };
