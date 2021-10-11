import Layout from "../src/Layout";
import RepoDashboard from "../src/RepoDashboard";

export default function Page() {
  return (
    <Layout>
      <RepoDashboard owner="bazelbuild" repo="bazel" />
    </Layout>
  );
}
