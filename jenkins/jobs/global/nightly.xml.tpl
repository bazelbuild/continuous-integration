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
        <hudson.model.TextParameterDefinition>
          <name>EXTRA_BAZELRC</name>
          <description>To inject new option to the .bazelrc file in downstream projects.</description>
          <defaultValue></defaultValue>
        </hudson.model.TextParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        <hudson.triggers.TimerTrigger>
          <spec>@midnight</spec>
        </hudson.triggers.TimerTrigger>
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
    <script>
  globalBazelTest(
      repository: "https://bazel.googlesource.com/bazel",
      branch: "master",
      extra_bazelrc: params.EXTRA_BAZELRC,
      refspec: "+refs/heads/*:refs/remotes/origin/*",
      configuration: '''{{ raw_imports['//jenkins/jobs:configs/bootstrap.json'].replace('\\', '\\\\').replace("'", "\\'") }}''')
  </script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
</flow-definition>
