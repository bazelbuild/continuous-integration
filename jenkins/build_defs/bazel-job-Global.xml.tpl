<?xml version='1.0' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>Test the {{ variables.PROJECT_NAME }} project located at {{ variables.GIT_URL }}.

  Job for Global tests with Bazel at HEAD.
  </description>
  <keepDependencies>false</keepDependencies>
  <properties>
    {% if variables.RUN_SEQUENTIAL == "true" %}
    <org.jenkinsci.plugins.workflow.job.properties.DisableConcurrentBuildsJobProperty/>
    {% endif %}
    {% if variables.github == "True" %}
    <com.coravy.hudson.plugins.github.GithubProjectProperty>
      <projectUrl>{{ variables.GITHUB_URL }}</projectUrl>
    </com.coravy.hudson.plugins.github.GithubProjectProperty>
    {% endif %}
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.TextParameterDefinition>
          <name>EXTRA_BAZELRC</name>
          <description>Extraneous content for the .bazelrc file</description>
          <defaultValue></defaultValue>
        </hudson.model.TextParameterDefinition>
{% if variables.GLOBAL_USE_UPSTREAM_BRANCH == "True" %}
        <hudson.model.StringParameterDefinition>
          <name>REPOSITORY</name>
          <description>Repository to build</description>
          <defaultValue>{{ variables.GIT_URL }}</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>BRANCH</name>
          <description>Branch to build</description>
          <defaultValue>{{ variables.BRANCH }}</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.TextParameterDefinition>
          <name>REFSPEC</name>
          <description>Refspec to fetch</description>
          <defaultValue>+refs/heads/*:refs/remotes/origin/*</defaultValue>
        </hudson.model.TextParameterDefinition>
{% endif %}
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers/>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script><![CDATA[
bazelCiConfiguredJob(
    bazel_version: "custom",
{% if variables.GLOBAL_USE_UPSTREAM_BRANCH == "True" %}
    repository: params.REPOSITORY,
    refspec: params.REFSPEC,
    branch: params.BRANCH,
{% else %}
    repository: "{{ variables.GIT_URL }}",
    branch: "{{ variables.BRANCH }}",
{% endif %}
    extra_bazelrc: params.EXTRA_BAZELRC,
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
  <disabled>{{ variables.disabled }}</disabled>
</flow-definition>
