import React, { ReactNode } from "react";
import Link from "next/link";

export interface LayoutProps {
  children: NonNullable<ReactNode>;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex flex-col">
      <header className="flex flex-row bg-green-bazel h-[52px] items-center fixed w-full z-header top-0 border-b">
        <img
          src="https://bazel.build/images/bazel-navbar.svg"
          className="h-[28px] pl-[15px]"
          alt="Bazel"
        />
        <ul className="flex ml-12 text-white text-base">
          {[
            { name: "Stats", link: "/" },
            { name: "Issues", link: "/issues" },
          ].map((menu) => (
            <li
              key={menu.name}
              className="flex hover:bg-green-bazel-light hover:text-gray-700"
            >
              <Link href={menu.link}>
                <a className="h-[50px] flex items-center px-4">{menu.name}</a>
              </Link>
            </li>
          ))}
        </ul>
      </header>
      <main className="pt-[50px]">{children}</main>
    </div>
  );
}
