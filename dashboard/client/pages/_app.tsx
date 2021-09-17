import "../styles/globals.css";

import { AppProps } from "next/app";
import React from "react";
import Head from "next/head";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>Bazel Dashboard</title>
      </Head>
      <Component {...pageProps} />
    </>
  );
}
