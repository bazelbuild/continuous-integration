import "../styles/globals.css";

import { AppProps } from "next/app";
import Head from "next/head";
import { CssBaseline, ThemeProvider } from "@material-ui/core";
import React from "react";

import theme from "../src/theme";

function MyApp({ Component, pageProps }: AppProps) {
  React.useEffect(() => {
    const jssStyles = document.querySelector("#jss-server-side");
    if (jssStyles) {
      jssStyles.parentElement!!.removeChild(jssStyles);
    }
  }, []);

  return (
    <>
      <Head>
        <title>Bazel Dashboard</title>
        <meta
          name="viewport"
          content="minimum-scale=1, initial-scale=1, width=device-width"
        />
      </Head>

      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Component {...pageProps} />
      </ThemeProvider>
    </>
  );
}

export default MyApp;
