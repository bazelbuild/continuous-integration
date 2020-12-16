import "../styles/globals.scss";

import { AppProps } from "next/app";
import Head from "next/head";
import { CssBaseline } from "@material-ui/core";

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>Bazel Dashboard</title>
        <meta
          name="viewport"
          content="minimum-scale=1, initial-scale=1, width=device-width"
        />

        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap"
        />
      </Head>
      <CssBaseline />
      <Component {...pageProps} />
    </>
  );
}

export default MyApp;
