<?xml version='1.0' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>Test Gerrit code review for {{ variables.PROJECT_NAME }}.

This job for testing changes submitted to the Gerrit project: {{ variables.GERRIT_PROJECT }}.
</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    {% if variables.RUN_SEQUENTIAL == "true" %}
    <org.jenkinsci.plugins.workflow.job.properties.DisableConcurrentBuildsJobProperty/>
    {% endif %}
    <jenkins.model.BuildDiscarderProperty>
      <strategy class="hudson.tasks.LogRotator">
        <daysToKeep>90</daysToKeep>
        <numToKeep>-1</numToKeep>
        <artifactDaysToKeep>-1</artifactDaysToKeep>
        <artifactNumToKeep>-1</artifactNumToKeep>
      </strategy>
    </jenkins.model.BuildDiscarderProperty>
    {% if variables.github == "True" %}
    <com.coravy.hudson.plugins.github.GithubProjectProperty>
      <projectUrl>{{ variables.GITHUB_URL }}</projectUrl>
    </com.coravy.hudson.plugins.github.GithubProjectProperty>
    {% endif %}
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>REFSPEC</name>
          <description>Refs to pull</description>
          <defaultValue>+refs/heads/*:refs/remotes/origin/*</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>BRANCH</name>
          <description>Branch to build</description>
          <defaultValue>master</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>CHANGE_NUMBER</name>
          <description>Number of the change being tested, for information only.</description>
          <defaultValue>no-change</defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers/>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script><![CDATA[
gerritReview("https://bazel-review.googlesource.com/",
    "/opt/secrets/gerritcookies",
    "Bazel CI <ci.bazel@gmail.com>",
    params.CHANGE_NUMBER,
    params.BRANCH) {
    bazelCiConfiguredJob(
        repository: "https://bazel.googlesource.com/{{ variables.GERRIT_PROJECT }}",
        branch: params.BRANCH,
        refspec: params.REFSPEC,
        bazel_version: "latest",
        configuration: '''{{ raw_imports['JSON_CONFIGURATION'].replace('\\', '\\\\').replace("'", "\\'") }}''',
        workspace: "{{ variables.WORKSPACE }}",
        {% if variables.SAUCE_ENABLED == "true" %}
        sauce: "61b4846b-279d-4369-ae20-31e9d8b9bc66",
        {% endif %}
        run_sequentially: {{ variables.RUN_SEQUENTIAL }}
    )
}
    ]]></script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <quietPeriod>5</quietPeriod>
  <disabled>{{ variables.disabled }}</disabled>
</flow-definition>
