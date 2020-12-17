import "../styles/globals.scss";

import { AppProps } from "next/app";
import Head from "next/head";
import { createMuiTheme, CssBaseline, ThemeProvider } from "@material-ui/core";
import React from "react";

let theme = createMuiTheme({
  palette: {
    primary: {
      main: "#368039",
    },
  },
});

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

      <ThemeProvider theme={theme}>
        <Component {...pageProps} />
      </ThemeProvider>
    </>
  );
}

export default MyApp;
