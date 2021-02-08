import { useRouter } from "next/router";

import Layout from "../../src/Layout";
import RepoDashboard from "../../src/RepoDashboard";
import { GetStaticPaths, GetStaticProps } from "next";

interface PageProps {
  owner: string;
  repo: string;
}

export default function Page({ owner, repo }: PageProps) {
  return (
    <Layout>
      <RepoDashboard owner={owner} repo={repo} />
    </Layout>
  );
}

export const getStaticProps: GetStaticProps = async (context) => {
  const { owner, repo } = context.params as any;
  return {
    props: { owner, repo },
  };
};

export const getStaticPaths: GetStaticPaths = async (context) => {
  return {
    paths: [],
    fallback: "blocking",
  };
};
