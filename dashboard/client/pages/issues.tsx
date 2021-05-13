import React from "react";
import { useRouter } from "next/router";
import queryString from "query-string";
import { GetServerSidePropsContext } from "next";
import { ParsedUrlQuery } from "querystring";

import GithubIssueList from "../src/GithubIssueList";
import Layout from "../src/Layout";

const PARAM_QUERY_KEY = "q";


export default function Page(props: { query: ParsedUrlQuery }) {
  const router = useRouter();

  const changeParams = (params: string) => {
    let newQuery = { ...props.query };
    newQuery[PARAM_QUERY_KEY] = params;

    const newUrl = queryString.stringifyUrl({
      url: router.pathname,
      query: newQuery,
    });
    router.push(newUrl, undefined, { scroll: false });
  };

  return (
    <Layout>
      <div className="flex flex-col space-y-4 mx-auto max-w-[1440px] px-4 mt-6">
        <GithubIssueList
          paramString={props.query[PARAM_QUERY_KEY] as string | undefined}
          changeParams={changeParams}
        />
      </div>
    </Layout>
  );
}

export function getServerSideProps(context: GetServerSidePropsContext) {
  return { props: { query: context.query } };
}
