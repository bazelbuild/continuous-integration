import React, { useEffect } from "react";
import { GetStaticPaths, GetStaticProps } from "next";

import { useRouter } from "next/router";

function Breadcrumb({ owner, repo }: { owner: string; repo: string }) {
  return (
    <div className="flex flex-row items-center space-x-1">
      <svg
        className="w-4 h-4 mr-1"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
      >
        <path
          fillRule="evenodd"
          d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"
        />
      </svg>
      <a
        className="text-base text-blue-github"
        href={`https://github.com/${owner}`}
        target="_blank"
      >
        {owner}
      </a>
      <span className="text-base">/</span>
      <a
        className="text-base text-blue-github font-bold"
        href={`https://github.com/${owner}/${repo}`}
        target="_blank"
      >
        {repo}
      </a>
    </div>
  );
}

export default function Page({ owner, repo }: { owner: string; repo: string }) {
  const router = useRouter();
  useEffect(() => {
    router.replace("/issues");
  }, []);
  return null;
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
