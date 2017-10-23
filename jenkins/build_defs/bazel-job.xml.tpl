<?xml version='1.0' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>Test the {{ variables.PROJECT_NAME }} project located at {{ variables.GIT_URL }}.</description>
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
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        {% if variables.production == "true" %}
        {% if variables.enable_trigger == "true" %}
        <com.cloudbees.jenkins.GitHubPushTrigger>
          <spec></spec>
        </com.cloudbees.jenkins.GitHubPushTrigger>
        {% endif %}
        {% if variables.poll == "true" %}
        <hudson.triggers.SCMTrigger>
          <spec>0 * * * *
15 * * * *
30 * * * *
45 * * * *</spec>
          <ignorePostCommitHooks>false</ignorePostCommitHooks>
        </hudson.triggers.SCMTrigger>
        {% endif %}
        {% endif %}
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script><![CDATA[
bazelCiConfiguredJob(
    repository: "{{ variables.GIT_URL }}",
    branch: "{{ variables.BRANCH }}",
    bazel_version: "latest",
    configuration: '''{{ raw_imports['JSON_CONFIGURATION'].replace('\\', '\\\\').replace("'", "\\'") }}''',
    workspace: "{{ variables.WORKSPACE }}",
    {% if variables.SAUCE_ENABLED == "true" %}
    sauce: "61b4846b-279d-4369-ae20-31e9d8b9bc66",
    {% endif %}
    run_sequentially: {{ variables.RUN_SEQUENTIAL }},
    restrict_configuration: {{ variables.RESTRICT_CONFIGURATION }}
)
    ]]></script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <quietPeriod>5</quietPeriod>
  <disabled>{{ variables.disabled }}</disabled>
</flow-definition>
