import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";

import GithubIssueList from "../src/GithubIssueList";
import Layout from "../src/Layout";
import { GithubIssueListParams } from "../src/data/GithubIssueList";

const PARAM_QUERY_KEY = "q";

export default function Page() {
  const router = useRouter();
  const [params, setParams] = useState(undefined);

  useEffect(() => {
    const paramsString = router.query[PARAM_QUERY_KEY] as string | undefined;
    if (paramsString) {
      try {
        setParams(JSON.parse(paramsString));
        return;
      } catch (e) {
        console.error(e);
      }
    }

    setParams(undefined);
  }, [router]);

  const changeParams = (params: GithubIssueListParams) => {
    let newQuery = { ...router.query };
    newQuery[PARAM_QUERY_KEY] = JSON.stringify(params);

    router.push(
      {
        pathname: router.pathname,
        query: newQuery,
      },
      undefined,
      { scroll: false }
    );
  };

  return (
    <Layout>
      <div className="flex flex-col space-y-4 mx-auto max-w-[1440px] px-4 mt-6">
        <GithubIssueList params={params} changeParams={changeParams} />
      </div>
    </Layout>
  );
}
