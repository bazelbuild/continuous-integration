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
          <name>REPOSITORY</name>
          <description>The repository to build</description>
          <defaultValue>https://bazel.googlesource.com/bazel</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>BRANCH</name>
          <description>The branch to build</description>
          <defaultValue>master</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>REFSPEC</name>
          <description>The refspec to fetch</description>
          <defaultValue>+refs/heads/*:refs/remotes/origin/*</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.TextParameterDefinition>
          <name>EXTRA_BAZELRC</name>
          <description>To inject new option to the .bazelrc file in downstream projects.</description>
          <defaultValue></defaultValue>
        </hudson.model.TextParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers/>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
    <script>
json_config = '''{{ raw_imports['//jenkins/jobs:configs/bootstrap.json'].replace('\\', '\\\\').replace("'", "\\'") }}'''
restrict_configuration = {{ variables.RESTRICT_CONFIGURATION }}
mail_recipient = "{{ variables.BAZEL_BUILD_RECIPIENT }}"
{{ imports['//jenkins/jobs:global.groovy'] }}
  </script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
</flow-definition>
