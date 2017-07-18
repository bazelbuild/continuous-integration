<?xml version='1.0' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>Test Github pull requests for {{ variables.PROJECT_NAME }}.</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    {% if variables.RUN_SEQUENTIAL == "true" %}
    <org.jenkinsci.plugins.workflow.job.properties.DisableConcurrentBuildsJobProperty/>
    {% endif %}
    <com.coravy.hudson.plugins.github.GithubProjectProperty>
      <projectUrl>{{ variables.GITHUB_URL }}</projectUrl>
    </com.coravy.hudson.plugins.github.GithubProjectProperty>
    {% if variables.production == "true" %}
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        <org.jenkinsci.plugins.ghprb.GhprbTrigger>
          <spec>H/5 * * * *</spec>
          <latestVersion>3</latestVersion>
          <configVersion>3</configVersion>
          <adminlist></adminlist>
          <allowMembersOfWhitelistedOrgsAsAdmin>true</allowMembersOfWhitelistedOrgsAsAdmin>
          <orgslist>google bazelbuild</orgslist>
          <cron>H/5 * * * *</cron>
          <buildDescTemplate></buildDescTemplate>
          <onlyTriggerPhrase>false</onlyTriggerPhrase>
          <useGitHubHooks>true</useGitHubHooks>
          <permitAll>false</permitAll>
          <whitelist></whitelist>
          <autoCloseFailedPullRequests>false</autoCloseFailedPullRequests>
          <displayBuildErrorsOnDownstreamBuilds>false</displayBuildErrorsOnDownstreamBuilds>
          <whiteListTargetBranches>
            <org.jenkinsci.plugins.ghprb.GhprbBranch>
              <branch></branch>
            </org.jenkinsci.plugins.ghprb.GhprbBranch>
          </whiteListTargetBranches>
          <gitHubAuthId>0182cdc4-ebe9-4d40-9b60-b66809f141cc</gitHubAuthId>
          <triggerPhrase></triggerPhrase>
          <extensions>
            <org.jenkinsci.plugins.ghprb.extensions.status.GhprbSimpleStatus>
              <commitStatusContext>ci.bazel.io</commitStatusContext>
              <triggeredStatus></triggeredStatus>
              <startedStatus></startedStatus>
              <statusUrl>${RUN_DISPLAY_URL}</statusUrl>
              <addTestResults>false</addTestResults>
            </org.jenkinsci.plugins.ghprb.extensions.status.GhprbSimpleStatus>
          </extensions>
        </org.jenkinsci.plugins.ghprb.GhprbTrigger>
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
    {% endif %}
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script><![CDATA[
    bazelCiConfiguredJob(
        repository: "{{ variables.GIT_URL }}",
        branch: env.sha1,
        refspec: "+refs/pull/*:refs/remotes/origin/pr/*",
        bazel_version: "latest",
        configuration: '''{{ raw_imports['JSON_CONFIGURATION'].replace('\\', '\\\\').replace("'", "\\'") }}''',
        mail_recipient: "",
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
</flow-definition>
