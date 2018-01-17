<?xml version='1.0' encoding='UTF-8'?>
<flow-definition>
  <actions/>
  <description>Global pipeline to bootstrap bazel and runs all downstream jobs</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.DisableConcurrentBuildsJobProperty/>
    <com.coravy.hudson.plugins.github.GithubProjectProperty>
      <projectUrl>https://github.com/bazelbuild/bazel/</projectUrl>
      <displayName></displayName>
    </com.coravy.hudson.plugins.github.GithubProjectProperty>
    <jenkins.model.BuildDiscarderProperty>
      <strategy class="hudson.tasks.LogRotator">
        <daysToKeep>90</daysToKeep>
        <numToKeep>-1</numToKeep>
        <artifactDaysToKeep>-1</artifactDaysToKeep>
        <artifactNumToKeep>-1</artifactNumToKeep>
      </strategy>
    </jenkins.model.BuildDiscarderProperty>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>payload</name>
          <description>Payload sent by GitHub</description>
          <defaultValue></defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.TextParameterDefinition>
          <name>EXTRA_BAZELRC</name>
          <description>To inject new option to the .bazelrc file in downstream projects.</description>
          <defaultValue></defaultValue>
        </hudson.model.TextParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <authToken>##SECRET:github_trigger_auth_token##</authToken>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
    <script>
githubHook(refs: '^refs/(heads/release-|tags/).*$') {
  globalBazelTest(
      repository: delegate.url,
      branch: delegate.branch,
      extra_bazelrc: params.EXTRA_BAZELRC,
      refspec: "+refs/heads/*:refs/remotes/origin/* +refs/notes/*:refs/notes/*",
      configuration: '''{{ raw_imports['//jenkins/jobs:configs/bootstrap.json'].replace('\\', '\\\\').replace("'", "\\'") }}''')
}
  </script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
</flow-definition>
